#!/usr/bin/env python3
"""
Recovery automation system for critical failures.
Monitors system health and automatically recovers from various failure scenarios.
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
import signal
import os
import psutil
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('recovery_automation.log')
    ]
)
log = logging.getLogger("recovery_automation")

class HealthMonitor:
    """Monitors system health and detects failure conditions."""
    
    def __init__(self):
        self.api_url = "http://localhost:8000"
        self.data_dir = Path("data")
        self.status_file = self.data_dir / "model_service_status.json"
        self.health_history = []
        self.max_history = 10
        
        # Health check thresholds
        self.api_timeout = 10
        self.service_heartbeat_threshold = 60  # seconds
        self.memory_threshold = 0.9  # 90% of GPU memory
        self.consecutive_failures_threshold = 3
    
    def check_api_health(self) -> Dict[str, Any]:
        """Check API server health."""
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_url}/api/v2/rag/status", timeout=self.api_timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "healthy": True,
                    "response_time": response_time,
                    "status": data,
                    "error": None
                }
            else:
                return {
                    "healthy": False,
                    "response_time": response_time,
                    "status": None,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "healthy": False,
                "response_time": None,
                "status": None,
                "error": str(e)
            }
    
    def check_model_service_health(self) -> Dict[str, Any]:
        """Check model service health via status file."""
        try:
            if not self.status_file.exists():
                return {
                    "healthy": False,
                    "error": "Status file not found",
                    "status": None
                }
            
            # Check file age
            file_age = time.time() - self.status_file.stat().st_mtime
            if file_age > self.service_heartbeat_threshold:
                return {
                    "healthy": False,
                    "error": f"Status file too old ({file_age:.1f}s)",
                    "status": None
                }
            
            with open(self.status_file, 'r') as f:
                status = json.load(f)
            
            # Check heartbeat
            last_heartbeat = status.get("last_heartbeat", 0)
            heartbeat_age = time.time() - last_heartbeat
            
            if heartbeat_age > self.service_heartbeat_threshold:
                return {
                    "healthy": False,
                    "error": f"Heartbeat too old ({heartbeat_age:.1f}s)",
                    "status": status
                }
            
            # Check overall status
            overall_status = status.get("overall_status", "unknown")
            if overall_status not in ["running", "starting"]:
                return {
                    "healthy": False,
                    "error": f"Service status: {overall_status}",
                    "status": status
                }
            
            return {
                "healthy": True,
                "error": None,
                "status": status,
                "heartbeat_age": heartbeat_age
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": f"Status check failed: {e}",
                "status": None
            }
    
    def check_memory_health(self) -> Dict[str, Any]:
        """Check system memory health."""
        try:
            import torch
            
            if not torch.cuda.is_available():
                return {
                    "healthy": True,
                    "gpu_available": False,
                    "error": None
                }
            
            allocated = torch.cuda.memory_allocated() / (1024**3)
            total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            utilization = allocated / total
            
            return {
                "healthy": utilization < self.memory_threshold,
                "gpu_available": True,
                "allocated_gb": allocated,
                "total_gb": total,
                "utilization": utilization,
                "error": f"High memory usage: {utilization:.1%}" if utilization >= self.memory_threshold else None
            }
            
        except Exception as e:
            return {
                "healthy": True,  # Don't fail if we can't check GPU
                "gpu_available": False,
                "error": f"Memory check failed: {e}"
            }
    
    def check_process_health(self) -> Dict[str, Any]:
        """Check for running processes."""
        try:
            api_processes = []
            model_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    
                    if 'uvicorn' in cmdline and 'app:app' in cmdline:
                        api_processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline
                        })
                    elif 'model_service' in cmdline:
                        model_processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                "healthy": len(api_processes) > 0,  # At least API should be running
                "api_processes": api_processes,
                "model_processes": model_processes,
                "error": "No API processes found" if len(api_processes) == 0 else None
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": f"Process check failed: {e}"
            }
    
    def comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check."""
        log.info("Running comprehensive health check...")
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_healthy": True,
            "checks": {}
        }
        
        # Check API health
        api_health = self.check_api_health()
        health_report["checks"]["api"] = api_health
        if not api_health["healthy"]:
            health_report["overall_healthy"] = False
            log.warning(f"API health issue: {api_health['error']}")
        
        # Check model service health
        model_health = self.check_model_service_health()
        health_report["checks"]["model_service"] = model_health
        if not model_health["healthy"]:
            log.warning(f"Model service health issue: {model_health['error']}")
        
        # Check memory health
        memory_health = self.check_memory_health()
        health_report["checks"]["memory"] = memory_health
        if not memory_health["healthy"]:
            health_report["overall_healthy"] = False
            log.warning(f"Memory health issue: {memory_health['error']}")
        
        # Check process health
        process_health = self.check_process_health()
        health_report["checks"]["processes"] = process_health
        if not process_health["healthy"]:
            health_report["overall_healthy"] = False
            log.warning(f"Process health issue: {process_health['error']}")
        
        # Update health history
        self.health_history.append(health_report)
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
        
        if health_report["overall_healthy"]:
            log.info("✅ All health checks passed")
        else:
            log.error("❌ Health check failures detected")
        
        return health_report

class RecoveryActions:
    """Implements various recovery actions."""
    
    def __init__(self):
        self.data_dir = Path("data")
    
    def restart_api_service(self) -> bool:
        """Restart the API service."""
        log.info("🔄 Restarting API service...")
        
        try:
            # Kill existing API processes
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'uvicorn' in cmdline and 'app:app' in cmdline:
                        log.info(f"Killing API process {proc.info['pid']}")
                        proc.kill()
                        proc.wait(timeout=10)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            time.sleep(3)  # Wait for cleanup
            
            # Start new API process
            log.info("Starting new API process...")
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "app:app", 
                "--host", "0.0.0.0", "--port", "8000"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for API to be responsive
            for i in range(30):
                try:
                    response = requests.get("http://localhost:8000/", timeout=2)
                    if response.status_code == 200:
                        log.info(f"✅ API service restarted successfully (PID: {process.pid})")
                        return True
                except:
                    pass
                time.sleep(1)
            
            log.error("❌ API service restart failed - not responsive")
            return False
            
        except Exception as e:
            log.error(f"❌ API service restart failed: {e}")
            return False
    
    def restart_model_service(self) -> bool:
        """Restart the model service."""
        log.info("🔄 Restarting model service...")
        
        try:
            # Kill existing model service processes
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'model_service' in cmdline:
                        log.info(f"Killing model service process {proc.info['pid']}")
                        proc.kill()
                        proc.wait(timeout=10)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Clean up service files
            status_file = self.data_dir / "model_service_status.json"
            for file_path in [status_file, 
                            self.data_dir / "model_service_requests.json",
                            self.data_dir / "model_service_responses.json"]:
                if file_path.exists():
                    file_path.unlink()
            
            time.sleep(3)  # Wait for cleanup
            
            # Start new model service process
            log.info("Starting new model service process...")
            process = subprocess.Popen([
                sys.executable, "-m", "src.sc_gen5.rag.v2.model_service"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for service to be ready
            for i in range(60):
                if status_file.exists():
                    try:
                        with open(status_file, 'r') as f:
                            status = json.load(f)
                        last_heartbeat = status.get("last_heartbeat", 0)
                        if time.time() - last_heartbeat < 30:
                            log.info(f"✅ Model service restarted successfully (PID: {process.pid})")
                            return True
                    except:
                        pass
                time.sleep(1)
            
            log.error("❌ Model service restart failed - not ready")
            return False
            
        except Exception as e:
            log.error(f"❌ Model service restart failed: {e}")
            return False
    
    def clear_gpu_memory(self) -> bool:
        """Clear GPU memory."""
        log.info("🧹 Clearing GPU memory...")
        
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                
                # Check if memory was freed
                allocated = torch.cuda.memory_allocated() / (1024**3)
                log.info(f"✅ GPU memory cleared, allocated: {allocated:.2f}GB")
                return True
            else:
                log.info("No GPU available for memory clearing")
                return True
                
        except Exception as e:
            log.error(f"❌ GPU memory clear failed: {e}")
            return False
    
    def emergency_cleanup(self) -> bool:
        """Perform emergency cleanup of all resources."""
        log.info("🚨 Performing emergency cleanup...")
        
        success = True
        
        # Clear GPU memory
        if not self.clear_gpu_memory():
            success = False
        
        # Clean up service files
        try:
            for file_path in [self.data_dir / "model_service_status.json",
                            self.data_dir / "model_service_requests.json", 
                            self.data_dir / "model_service_responses.json"]:
                if file_path.exists():
                    file_path.unlink()
            log.info("✅ Service files cleaned up")
        except Exception as e:
            log.error(f"❌ Service file cleanup failed: {e}")
            success = False
        
        # Kill stuck processes
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if any(keyword in cmdline for keyword in ['model_service', 'sc_gen5']):
                        proc.kill()
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_count > 0:
                log.info(f"✅ Killed {killed_count} stuck processes")
        except Exception as e:
            log.error(f"❌ Process cleanup failed: {e}")
            success = False
        
        return success

class RecoveryAutomation:
    """Main recovery automation system."""
    
    def __init__(self):
        self.health_monitor = HealthMonitor()
        self.recovery_actions = RecoveryActions()
        self.running = False
        self.failure_count = 0
        self.last_recovery_time = None
        self.recovery_cooldown = 300  # 5 minutes between recoveries
        self.max_recovery_attempts = 5
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        log.info(f"Received signal {signum}, stopping recovery automation...")
        self.running = False
    
    def should_attempt_recovery(self) -> bool:
        """Check if recovery should be attempted."""
        if self.failure_count >= self.max_recovery_attempts:
            log.error(f"Maximum recovery attempts ({self.max_recovery_attempts}) exceeded")
            return False
        
        if (self.last_recovery_time and 
            time.time() - self.last_recovery_time < self.recovery_cooldown):
            log.info(f"Recovery cooldown active, waiting...")
            return False
        
        return True
    
    def execute_recovery_plan(self, health_report: Dict[str, Any]) -> bool:
        """Execute appropriate recovery plan based on health report."""
        if not self.should_attempt_recovery():
            return False
        
        log.info("🚑 Executing recovery plan...")
        self.failure_count += 1
        self.last_recovery_time = time.time()
        
        checks = health_report["checks"]
        recovery_success = True
        
        # Recovery strategy based on specific failures
        if not checks["memory"]["healthy"]:
            log.info("🧠 Memory issue detected, clearing GPU memory...")
            if not self.recovery_actions.clear_gpu_memory():
                recovery_success = False
        
        if not checks["model_service"]["healthy"]:
            log.info("🤖 Model service issue detected, restarting...")
            if not self.recovery_actions.restart_model_service():
                recovery_success = False
        
        if not checks["api"]["healthy"]:
            log.info("🌐 API issue detected, restarting...")
            if not self.recovery_actions.restart_api_service():
                recovery_success = False
        
        if not checks["processes"]["healthy"]:
            log.info("⚙️ Process issue detected, performing cleanup...")
            if not self.recovery_actions.emergency_cleanup():
                recovery_success = False
        
        if recovery_success:
            log.info("✅ Recovery plan executed successfully")
            self.failure_count = max(0, self.failure_count - 1)  # Reduce failure count on success
        else:
            log.error("❌ Recovery plan failed")
        
        return recovery_success
    
    def monitor_and_recover(self, check_interval: int = 60):
        """Main monitoring and recovery loop."""
        log.info(f"🔍 Starting health monitoring and recovery automation...")
        log.info(f"Check interval: {check_interval}s")
        log.info(f"Recovery cooldown: {self.recovery_cooldown}s")
        log.info(f"Max recovery attempts: {self.max_recovery_attempts}")
        
        self.running = True
        consecutive_failures = 0
        
        while self.running:
            try:
                # Run health check
                health_report = self.health_monitor.comprehensive_health_check()
                
                if health_report["overall_healthy"]:
                    consecutive_failures = 0
                    log.info("💚 System healthy")
                else:
                    consecutive_failures += 1
                    log.warning(f"💔 System unhealthy (consecutive failures: {consecutive_failures})")
                    
                    # Attempt recovery if threshold exceeded
                    if consecutive_failures >= self.health_monitor.consecutive_failures_threshold:
                        log.error(f"🚨 Consecutive failure threshold exceeded, attempting recovery...")
                        
                        if self.execute_recovery_plan(health_report):
                            log.info("🎯 Recovery attempted, resetting failure counter")
                            consecutive_failures = 0
                        else:
                            log.error("💥 Recovery failed, system may need manual intervention")
                
                # Sleep until next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                log.info("Monitoring interrupted by user")
                break
            except Exception as e:
                log.error(f"Error in monitoring loop: {e}")
                time.sleep(check_interval)
        
        log.info("🛑 Recovery automation stopped")

def main():
    """Main entry point for recovery automation."""
    recovery_system = RecoveryAutomation()
    
    try:
        # Run monitoring and recovery
        recovery_system.monitor_and_recover(check_interval=30)
    except Exception as e:
        log.error(f"Recovery automation error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())