#!/usr/bin/env python3
"""
Smart Launcher for SC Gen 5 - Handles multi-service architecture with fallbacks
"""

import os
import sys
import time
import json
import subprocess
import threading
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import psutil

@dataclass
class ServiceStatus:
    """Service status information"""
    name: str
    running: bool = False
    pid: Optional[int] = None
    port: Optional[int] = None
    health_url: Optional[str] = None
    last_check: Optional[float] = None
    error: Optional[str] = None

class SmartLauncher:
    """Smart launcher with service management and fallbacks"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.services: Dict[str, ServiceStatus] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = True
        
        # Define services
        self.service_configs = {
            "backend": {
                "name": "FastAPI Backend",
                "command": [sys.executable, "-m", "uvicorn", "sc_gen5.services.consult_service:app", "--host", "0.0.0.0", "--port", "8000"],
                "cwd": str(self.root_dir),
                "port": 8000,
                "health_url": "http://localhost:8000/health"
            },
            "frontend": {
                "name": "React Frontend", 
                "command": ["npm", "start"],
                "cwd": str(self.root_dir / "frontend"),
                "port": 3000,
                "health_url": "http://localhost:3000"
            },
            "terminal": {
                "name": "Terminal Server",
                "command": ["npm", "start"],
                "cwd": str(self.root_dir / "terminal-server"),
                "port": 3001,
                "health_url": "http://localhost:3001/health"
            }
        }
        
        # Initialize service status
        for service_id, config in self.service_configs.items():
            self.services[service_id] = ServiceStatus(
                name=config["name"],
                port=config.get("port"),
                health_url=config.get("health_url")
            )
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if required dependencies are available"""
        deps = {
            "python": True,  # We're running Python
            "node": False,
            "npm": False,
            "frontend_deps": False,
            "terminal_deps": False
        }
        
        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                deps["node"] = True
                self.log(f"✅ Node.js: {result.stdout.strip()}")
            else:
                self.log("❌ Node.js not found", "ERROR")
        except Exception:
            self.log("❌ Node.js not found", "ERROR")
        
        # Check npm
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                deps["npm"] = True
                self.log(f"✅ npm: {result.stdout.strip()}")
            else:
                self.log("❌ npm not found", "ERROR")
        except Exception:
            self.log("❌ npm not found", "ERROR")
        
        # Check frontend dependencies
        frontend_dir = self.root_dir / "frontend"
        if frontend_dir.exists() and (frontend_dir / "node_modules").exists():
            deps["frontend_deps"] = True
            self.log("✅ Frontend dependencies installed")
        else:
            self.log("⚠️ Frontend dependencies not installed", "WARNING")
        
        # Check terminal dependencies
        terminal_dir = self.root_dir / "terminal-server"
        if terminal_dir.exists() and (terminal_dir / "node_modules").exists():
            deps["terminal_deps"] = True
            self.log("✅ Terminal dependencies installed")
        else:
            self.log("⚠️ Terminal dependencies not installed", "WARNING")
        
        return deps
    
    def install_dependencies(self):
        """Install missing dependencies"""
        deps = self.check_dependencies()
        
        if not deps["node"] or not deps["npm"]:
            self.log("❌ Node.js and npm are required but not installed")
            self.log("Please install Node.js from: https://nodejs.org/")
            return False
        
        # Install frontend dependencies
        if not deps["frontend_deps"]:
            self.log("Installing frontend dependencies...")
            frontend_dir = self.root_dir / "frontend"
            if frontend_dir.exists():
                try:
                    subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
                    self.log("✅ Frontend dependencies installed")
                except subprocess.CalledProcessError as e:
                    self.log(f"❌ Failed to install frontend dependencies: {e}", "ERROR")
                    return False
        
        # Install terminal dependencies
        if not deps["terminal_deps"]:
            self.log("Installing terminal dependencies...")
            terminal_dir = self.root_dir / "terminal-server"
            if terminal_dir.exists():
                try:
                    subprocess.run(["npm", "install"], cwd=terminal_dir, check=True)
                    self.log("✅ Terminal dependencies installed")
                except subprocess.CalledProcessError as e:
                    self.log(f"❌ Failed to install terminal dependencies: {e}", "ERROR")
                    return False
        
        return True
    
    def start_service(self, service_id: str) -> bool:
        """Start a specific service"""
        if service_id not in self.service_configs:
            self.log(f"❌ Unknown service: {service_id}", "ERROR")
            return False
        
        config = self.service_configs[service_id]
        service = self.services[service_id]
        
        if service.running:
            self.log(f"⚠️ {service.name} is already running")
            return True
        
        self.log(f"Starting {service.name}...")
        
        try:
            process = subprocess.Popen(
                config["command"],
                cwd=config["cwd"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.processes[service_id] = process
            service.running = True
            service.pid = process.pid
            service.error = None
            
            self.log(f"✅ {service.name} started (PID: {process.pid})")
            return True
            
        except Exception as e:
            service.error = str(e)
            self.log(f"❌ Failed to start {service.name}: {e}", "ERROR")
            return False
    
    def stop_service(self, service_id: str) -> bool:
        """Stop a specific service"""
        if service_id not in self.processes:
            return True
        
        service = self.services[service_id]
        process = self.processes[service_id]
        
        self.log(f"Stopping {service.name}...")
        
        try:
            process.terminate()
            process.wait(timeout=10)
            
            del self.processes[service_id]
            service.running = False
            service.pid = None
            
            self.log(f"✅ {service.name} stopped")
            return True
            
        except subprocess.TimeoutExpired:
            self.log(f"Force killing {service.name}...")
            process.kill()
            del self.processes[service_id]
            service.running = False
            service.pid = None
            return True
            
        except Exception as e:
            self.log(f"❌ Error stopping {service.name}: {e}", "ERROR")
            return False
    
    def check_service_health(self, service_id: str) -> bool:
        """Check if a service is healthy"""
        service = self.services[service_id]
        
        if not service.running:
            return False
        
        if not service.health_url:
            # Just check if process is running
            return service_id in self.processes and self.processes[service_id].poll() is None
        
        try:
            import requests
            response = requests.get(service.health_url, timeout=5)
            service.last_check = time.time()
            return response.status_code == 200
        except Exception:
            service.last_check = time.time()
            return False
    
    def show_status(self):
        """Show current service status"""
        print("\n" + "="*60)
        print("SC Gen 5 - Service Status")
        print("="*60)
        
        for service_id, service in self.services.items():
            status = "🟢 Running" if service.running else "🔴 Stopped"
            health = "✅ Healthy" if self.check_service_health(service_id) else "❌ Unhealthy"
            
            print(f"{service.name:20} | {status:12} | {health:12}")
            if service.error:
                print(f"  Error: {service.error}")
        
        print("="*60)
    
    def launch_mode_1_full_stack(self):
        """Launch full stack (all services)"""
        self.log("🚀 Launching SC Gen 5 Full Stack...")
        
        # Check dependencies
        if not self.install_dependencies():
            self.log("❌ Dependency installation failed", "ERROR")
            return False
        
        # Start backend first
        if not self.start_service("backend"):
            self.log("❌ Backend failed to start", "ERROR")
            return False
        
        time.sleep(3)  # Wait for backend to start
        
        # Start frontend
        if not self.start_service("frontend"):
            self.log("⚠️ Frontend failed to start, but backend is running", "WARNING")
        
        # Start terminal server
        if not self.start_service("terminal"):
            self.log("⚠️ Terminal server failed to start", "WARNING")
        
        # Open browser
        time.sleep(5)
        try:
            webbrowser.open("http://localhost:3000")
            self.log("✅ Browser opened to dashboard")
        except Exception:
            self.log("⚠️ Could not open browser automatically")
        
        return True
    
    def launch_mode_2_backend_only(self):
        """Launch backend only (for API testing)"""
        self.log("🔧 Launching SC Gen 5 Backend Only...")
        
        if not self.start_service("backend"):
            self.log("❌ Backend failed to start", "ERROR")
            return False
        
        self.log("✅ Backend started successfully")
        self.log("📖 API Documentation: http://localhost:8000/docs")
        
        try:
            webbrowser.open("http://localhost:8000/docs")
        except Exception:
            pass
        
        return True
    
    def launch_mode_3_streamlit_fallback(self):
        """Launch Streamlit fallback (if available)"""
        self.log("📊 Launching Streamlit Fallback...")
        
        streamlit_app = self.root_dir / "src" / "sc_gen5" / "ui" / "app.py"
        if not streamlit_app.exists():
            self.log("❌ Streamlit app not found", "ERROR")
            return False
        
        try:
            subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", str(streamlit_app),
                "--server.port", "8501"
            ])
            
            time.sleep(3)
            webbrowser.open("http://localhost:8501")
            self.log("✅ Streamlit app launched")
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to launch Streamlit: {e}", "ERROR")
            return False
    
    def interactive_menu(self):
        """Interactive menu for service management"""
        while self.running:
            print("\n" + "="*50)
            print("SC Gen 5 - Smart Launcher")
            print("="*50)
            print("1. Launch Full Stack (All Services)")
            print("2. Launch Backend Only (API Testing)")
            print("3. Launch Streamlit Fallback")
            print("4. Show Service Status")
            print("5. Start Individual Service")
            print("6. Stop Individual Service")
            print("7. Install Dependencies")
            print("8. Exit")
            print("="*50)
            
            try:
                choice = input("Enter your choice (1-8): ").strip()
                
                if choice == "1":
                    self.launch_mode_1_full_stack()
                elif choice == "2":
                    self.launch_mode_2_backend_only()
                elif choice == "3":
                    self.launch_mode_3_streamlit_fallback()
                elif choice == "4":
                    self.show_status()
                elif choice == "5":
                    service_id = input("Enter service ID (backend/frontend/terminal): ").strip()
                    self.start_service(service_id)
                elif choice == "6":
                    service_id = input("Enter service ID (backend/frontend/terminal): ").strip()
                    self.stop_service(service_id)
                elif choice == "7":
                    self.install_dependencies()
                elif choice == "8":
                    self.cleanup()
                    break
                else:
                    print("Invalid choice!")
                    
            except KeyboardInterrupt:
                self.cleanup()
                break
            except Exception as e:
                self.log(f"Menu error: {e}", "ERROR")
    
    def cleanup(self):
        """Cleanup all services"""
        self.log("Cleaning up services...")
        for service_id in list(self.processes.keys()):
            self.stop_service(service_id)
        self.running = False

def main():
    """Main function"""
    launcher = SmartLauncher()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "full":
            launcher.launch_mode_1_full_stack()
        elif mode == "backend":
            launcher.launch_mode_2_backend_only()
        elif mode == "streamlit":
            launcher.launch_mode_3_streamlit_fallback()
        else:
            print("Usage: python smart_launcher.py [full|backend|streamlit]")
    else:
        # Interactive mode
        launcher.interactive_menu()

if __name__ == "__main__":
    main() 