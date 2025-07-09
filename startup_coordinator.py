#!/usr/bin/env python3
"""
Startup coordinator for smooth service initialization.
Manages the startup sequence of API and model services for optimal performance.
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
import signal
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('startup_coordinator.log')
    ]
)
log = logging.getLogger("startup_coordinator")

class ServiceManager:
    """Manages the lifecycle of individual services."""
    
    def __init__(self, name: str, command: List[str], health_check_url: Optional[str] = None):
        self.name = name
        self.command = command
        self.health_check_url = health_check_url
        self.process: Optional[subprocess.Popen] = None
        self.status = "stopped"
        self.startup_time = 0
        self.restart_count = 0
        self.max_restarts = 3
    
    def start(self, wait_for_health: bool = True, timeout: int = 60) -> bool:
        """Start the service."""
        try:
            log.info(f"Starting {self.name}...")
            self.status = "starting"
            start_time = time.time()
            
            # Start process
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            log.info(f"{self.name} process started (PID: {self.process.pid})")
            
            if wait_for_health and self.health_check_url:
                # Wait for health check to pass
                for _ in range(timeout):
                    if self.is_healthy():
                        self.status = "running"
                        self.startup_time = time.time() - start_time
                        log.info(f"✅ {self.name} started successfully in {self.startup_time:.2f}s")
                        return True
                    time.sleep(1)
                
                log.error(f"❌ {self.name} failed health check within {timeout}s")
                self.stop()
                return False
            else:
                # Just wait a moment for process to stabilize
                time.sleep(2)
                if self.process.poll() is None:  # Process still running
                    self.status = "running"
                    self.startup_time = time.time() - start_time
                    log.info(f"✅ {self.name} started in {self.startup_time:.2f}s")
                    return True
                else:
                    log.error(f"❌ {self.name} process exited immediately")
                    return False
                    
        except Exception as e:
            log.error(f"❌ Failed to start {self.name}: {e}")
            self.status = "failed"
            return False
    
    def stop(self) -> bool:
        """Stop the service."""
        try:
            if self.process:
                log.info(f"Stopping {self.name}...")
                
                # Try graceful shutdown first
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                    log.info(f"✅ {self.name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    log.warning(f"Force killing {self.name}...")
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    self.process.wait()
                    log.info(f"✅ {self.name} force stopped")
                
                self.process = None
                self.status = "stopped"
                return True
        except Exception as e:
            log.error(f"Error stopping {self.name}: {e}")
            
        self.status = "stopped"
        return False
    
    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        if not self.process or self.process.poll() is not None:
            return False
        
        if self.health_check_url:
            try:
                response = requests.get(self.health_check_url, timeout=2)
                return response.status_code == 200
            except:
                return False
        
        # If no health check URL, just check if process is running
        return True
    
    def restart(self) -> bool:
        """Restart the service."""
        if self.restart_count >= self.max_restarts:
            log.error(f"❌ {self.name} has exceeded maximum restart attempts ({self.max_restarts})")
            return False
        
        log.info(f"Restarting {self.name} (attempt {self.restart_count + 1})...")
        self.restart_count += 1
        
        self.stop()
        time.sleep(2)  # Brief pause between stop and start
        return self.start()

class StartupCoordinator:
    """Coordinates the startup of all services."""
    
    def __init__(self):
        self.services: Dict[str, ServiceManager] = {}
        self.startup_order = []
        self.running = False
        self.data_dir = Path("data")
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Initialize services
        self._setup_services()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        log.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_all()
        sys.exit(0)
    
    def _setup_services(self):
        """Setup service configurations."""
        
        # Model Service
        self.services["model_service"] = ServiceManager(
            name="Model Service",
            command=[sys.executable, "-m", "src.sc_gen5.rag.v2.model_service"],
            health_check_url=None  # Uses file-based status
        )
        
        # API Service
        self.services["api_service"] = ServiceManager(
            name="API Service",
            command=[sys.executable, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"],
            health_check_url="http://localhost:8000/"
        )
        
        # Startup order: model service first, then API
        self.startup_order = ["model_service", "api_service"]
    
    def check_model_service_health(self) -> bool:
        """Check model service health via status file."""
        status_file = self.data_dir / "model_service_status.json"
        try:
            if not status_file.exists():
                return False
            
            with open(status_file, 'r') as f:
                status = json.load(f)
            
            # Check if service is running and responsive
            last_heartbeat = status.get("last_heartbeat", 0)
            current_time = time.time()
            
            # Service is healthy if heartbeat is within last 30 seconds
            return (current_time - last_heartbeat) < 30
            
        except Exception:
            return False
    
    def wait_for_model_service(self, timeout: int = 60) -> bool:
        """Wait for model service to be ready."""
        log.info("Waiting for model service to be ready...")
        
        for i in range(timeout):
            if self.check_model_service_health():
                log.info(f"✅ Model service ready after {i}s")
                return True
            time.sleep(1)
        
        log.error(f"❌ Model service not ready within {timeout}s")
        return False
    
    def start_all_services(self, staggered: bool = True) -> bool:
        """Start all services in the correct order."""
        log.info("🚀 Starting all services...")
        
        success_count = 0
        total_services = len(self.startup_order)
        
        for i, service_name in enumerate(self.startup_order):
            service = self.services[service_name]
            
            log.info(f"Starting service {i+1}/{total_services}: {service.name}")
            
            if service_name == "model_service":
                # Model service - start and wait for readiness
                if service.start(wait_for_health=False, timeout=30):
                    if self.wait_for_model_service(timeout=90):
                        success_count += 1
                        log.info(f"✅ {service.name} is ready")
                    else:
                        log.error(f"❌ {service.name} failed to become ready")
                        break
                else:
                    log.error(f"❌ Failed to start {service.name}")
                    break
                    
            elif service_name == "api_service":
                # API service - standard health check
                if service.start(wait_for_health=True, timeout=60):
                    success_count += 1
                    log.info(f"✅ {service.name} is ready")
                else:
                    log.error(f"❌ Failed to start {service.name}")
                    break
            
            # Staggered startup - wait between services
            if staggered and i < total_services - 1:
                log.info("Waiting before starting next service...")
                time.sleep(5)
        
        self.running = success_count == total_services
        
        if self.running:
            log.info(f"🎉 All {total_services} services started successfully!")
            self._log_startup_summary()
        else:
            log.error(f"❌ Only {success_count}/{total_services} services started successfully")
        
        return self.running
    
    def _log_startup_summary(self):
        """Log startup performance summary."""
        log.info("\n" + "="*50)
        log.info("📊 STARTUP PERFORMANCE SUMMARY")
        log.info("="*50)
        
        total_time = 0
        for service_name in self.startup_order:
            service = self.services[service_name]
            log.info(f"{service.name}: {service.startup_time:.2f}s")
            total_time += service.startup_time
        
        log.info(f"Total startup time: {total_time:.2f}s")
        log.info("="*50)
    
    def monitor_services(self, interval: int = 30):
        """Monitor service health and restart if needed."""
        log.info(f"Starting service monitoring (check every {interval}s)...")
        
        while self.running:
            try:
                for service_name, service in self.services.items():
                    if service.status == "running":
                        if service_name == "model_service":
                            healthy = self.check_model_service_health()
                        else:
                            healthy = service.is_healthy()
                        
                        if not healthy:
                            log.warning(f"⚠ {service.name} appears unhealthy, attempting restart...")
                            if not service.restart():
                                log.error(f"❌ Failed to restart {service.name}")
                                self.running = False
                                break
                            else:
                                log.info(f"✅ {service.name} restarted successfully")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                log.info("Monitoring interrupted by user")
                break
            except Exception as e:
                log.error(f"Error in service monitoring: {e}")
                time.sleep(interval)
    
    def shutdown_all(self):
        """Shutdown all services gracefully."""
        log.info("🛑 Shutting down all services...")
        
        # Shutdown in reverse order
        for service_name in reversed(self.startup_order):
            service = self.services[service_name]
            if service.status == "running":
                service.stop()
        
        self.running = False
        log.info("✅ All services stopped")
    
    def get_status(self) -> Dict:
        """Get status of all services."""
        status = {
            "coordinator_running": self.running,
            "services": {}
        }
        
        for name, service in self.services.items():
            status["services"][name] = {
                "status": service.status,
                "startup_time": service.startup_time,
                "restart_count": service.restart_count,
                "pid": service.process.pid if service.process else None
            }
        
        return status

def main():
    """Main entry point for startup coordinator."""
    coordinator = StartupCoordinator()
    
    try:
        # Start all services
        if coordinator.start_all_services(staggered=True):
            log.info("✅ System startup complete - all services running")
            
            # Monitor services
            coordinator.monitor_services(interval=30)
        else:
            log.error("❌ System startup failed")
            coordinator.shutdown_all()
            return 1
            
    except KeyboardInterrupt:
        log.info("Startup coordinator interrupted by user")
    except Exception as e:
        log.error(f"Startup coordinator error: {e}")
        return 1
    finally:
        coordinator.shutdown_all()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())