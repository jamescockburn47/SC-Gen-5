#!/usr/bin/env python3
"""
SC Gen 5 Service Runner
Starts all required services for the SC Gen 5 application.
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServiceRunner:
    def __init__(self):
        self.processes = []
        self.project_root = Path(__file__).parent
        
    def start_fastapi_backend(self):
        """Start the FastAPI backend server."""
        try:
            logger.info("Starting FastAPI backend...")
            
            # Set environment variables
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.project_root)
            
            # Start FastAPI server
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "src.sc_gen5.api.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ]
            
            process = subprocess.Popen(
                cmd,
                env=env,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append(("FastAPI Backend", process))
            logger.info(f"FastAPI backend started with PID: {process.pid}")
            
            # Wait a moment for startup
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start FastAPI backend: {e}")
            return False
    
    def start_react_frontend(self):
        """Start the React frontend development server."""
        try:
            frontend_dir = self.project_root / "frontend"
            if not frontend_dir.exists():
                logger.error("Frontend directory not found")
                return False
                
            logger.info("Starting React frontend...")
            
            # Check if node_modules exists
            node_modules = frontend_dir / "node_modules"
            if not node_modules.exists():
                logger.info("Installing frontend dependencies...")
                subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            
            # Start React development server
            cmd = ["npm", "start"]
            process = subprocess.Popen(
                cmd,
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append(("React Frontend", process))
            logger.info(f"React frontend started with PID: {process.pid}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start React frontend: {e}")
            return False
    
    def start_streamlit_ui(self):
        """Start the Streamlit UI (optional alternative)."""
        try:
            logger.info("Starting Streamlit UI...")
            
            # Set environment variables
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.project_root)
            
            # Start Streamlit
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                "src/sc_gen5/ui/streamlit_app.py",
                "--server.port", "8501",
                "--server.address", "0.0.0.0"
            ]
            
            process = subprocess.Popen(
                cmd,
                env=env,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes.append(("Streamlit UI", process))
            logger.info(f"Streamlit UI started with PID: {process.pid}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Streamlit UI: {e}")
            return False
    
    def monitor_processes(self):
        """Monitor running processes and restart if needed."""
        logger.info("Monitoring services...")
        
        while True:
            for name, process in self.processes[:]:
                if process.poll() is not None:
                    logger.warning(f"{name} process terminated unexpectedly")
                    self.processes.remove((name, process))
                    
                    # Restart the service
                    if "FastAPI" in name:
                        self.start_fastapi_backend()
                    elif "React" in name:
                        self.start_react_frontend()
                    elif "Streamlit" in name:
                        self.start_streamlit_ui()
            
            time.sleep(5)
    
    def stop_all(self):
        """Stop all running processes."""
        logger.info("Stopping all services...")
        
        for name, process in self.processes:
            try:
                logger.info(f"Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {name}...")
                process.kill()
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
        
        self.processes.clear()
        logger.info("All services stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop_all()
        sys.exit(0)

def main():
    """Main entry point."""
    runner = ServiceRunner()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, runner.signal_handler)
    signal.signal(signal.SIGTERM, runner.signal_handler)
    
    try:
        # Start services
        services_started = 0
        
        if runner.start_fastapi_backend():
            services_started += 1
            
        if runner.start_react_frontend():
            services_started += 1
            
        # Optionally start Streamlit UI
        # if runner.start_streamlit_ui():
        #     services_started += 1
        
        if services_started == 0:
            logger.error("No services started successfully")
            return 1
        
        logger.info(f"Started {services_started} services successfully")
        logger.info("Services are running:")
        logger.info("- FastAPI Backend: http://localhost:8000")
        logger.info("- React Frontend: http://localhost:3000")
        logger.info("- API Documentation: http://localhost:8000/docs")
        logger.info("")
        logger.info("Press Ctrl+C to stop all services")
        
        # Monitor processes
        runner.monitor_processes()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        runner.stop_all()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 