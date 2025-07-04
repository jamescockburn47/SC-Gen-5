#!/usr/bin/env python3
"""
Strategic Counsel Gen 5 - Sophisticated UI Startup Script
Modern React + WebSocket Terminal + FastAPI Backend
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

class StrategicCounselUI:
    """Advanced startup manager for Strategic Counsel Gen 5 sophisticated UI."""
    
    def __init__(self):
        self.processes = []
        self.root_dir = Path(__file__).parent
        self.frontend_dir = self.root_dir / "frontend"
        self.terminal_server_dir = self.root_dir / "terminal-server"
        
    def print_banner(self):
        """Print startup banner."""
        print("🏛️" + "="*70)
        print("⚖️  Strategic Counsel Gen 5 - Sophisticated UI System")
        print("🚀 Modern React + Native Terminal + FastAPI Backend")
        print("="*72)
        print()
        
    def check_dependencies(self):
        """Check if all dependencies are available."""
        print("🔍 Checking system dependencies...")
        
        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js: {result.stdout.strip()}")
            else:
                print("❌ Node.js not found")
                return False
        except FileNotFoundError:
            print("❌ Node.js not found")
            return False
            
        # Check npm
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ npm: {result.stdout.strip()}")
            else:
                print("❌ npm not found")
                return False
        except FileNotFoundError:
            print("❌ npm not found")
            return False
            
        # Check Python
        print(f"✅ Python: {sys.version.split()[0]}")
        
        # Check directories
        if not self.frontend_dir.exists():
            print("❌ Frontend directory not found")
            return False
        print("✅ React frontend directory found")
        
        if not self.terminal_server_dir.exists():
            print("❌ Terminal server directory not found")
            return False
        print("✅ Terminal server directory found")
        
        print()
        return True
        
    def install_dependencies(self):
        """Install missing dependencies."""
        print("📦 Installing/checking dependencies...")
        
        # Install frontend dependencies
        print("📦 Checking React frontend dependencies...")
        frontend_result = subprocess.run(
            ["npm", "install"],
            cwd=self.frontend_dir,
            capture_output=True,
            text=True
        )
        if frontend_result.returncode == 0:
            print("✅ Frontend dependencies ready")
        else:
            print("❌ Frontend dependency installation failed")
            print(frontend_result.stderr)
            
        # Install terminal server dependencies
        print("📦 Checking terminal server dependencies...")
        terminal_result = subprocess.run(
            ["npm", "install"],
            cwd=self.terminal_server_dir,
            capture_output=True,
            text=True
        )
        if terminal_result.returncode == 0:
            print("✅ Terminal server dependencies ready")
        else:
            print("❌ Terminal server dependency installation failed")
            print(terminal_result.stderr)
            
        print()
        
    def start_backend_services(self):
        """Start the existing FastAPI backend services."""
        print("🚀 Starting backend services...")
        
        # Start existing SC Gen 5 services
        try:
            backend_process = subprocess.Popen(
                ["python3", "run_services.py"],
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.processes.append(("Backend Services", backend_process))
            print("✅ Backend services starting...")
            
            # Give services time to start
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Failed to start backend services: {e}")
            
    def start_terminal_server(self):
        """Start the WebSocket terminal server."""
        print("🔗 Starting WebSocket terminal server...")
        
        try:
            terminal_process = subprocess.Popen(
                ["npm", "start"],
                cwd=self.terminal_server_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.processes.append(("Terminal Server", terminal_process))
            print("✅ Terminal server starting on port 3001...")
            
            # Give server time to start
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Failed to start terminal server: {e}")
            
    def start_react_frontend(self):
        """Start the React frontend."""
        print("🎨 Starting React frontend...")
        
        try:
            frontend_process = subprocess.Popen(
                ["npm", "start"],
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.processes.append(("React Frontend", frontend_process))
            print("✅ React frontend starting on port 3000...")
            
        except Exception as e:
            print(f"❌ Failed to start React frontend: {e}")
            
    def show_endpoints(self):
        """Show all running endpoints."""
        print("\n" + "="*72)
        print("🎉 Strategic Counsel Gen 5 - Sophisticated UI System Ready!")
        print("="*72)
        print()
        print("🌐 Frontend Endpoints:")
        print("   📊 React UI:              http://localhost:3000")
        print("   🔗 Terminal Server:       ws://localhost:3001")
        print()
        print("🔧 Backend Endpoints:")
        print("   🔍 Consult API:           http://localhost:8000")
        print("   🏢 Companies House API:   http://localhost:8001")
        print("   🤖 Ollama API:            http://localhost:11434")
        print()
        print("📖 API Documentation:")
        print("   📚 Consult API Docs:      http://localhost:8000/docs")
        print("   📚 Ingest API Docs:       http://localhost:8001/docs")
        print()
        print("✨ New Features:")
        print("   🎨 Modern Material-UI interface")
        print("   🖥️ Native terminal with xterm.js")
        print("   🤖 True Gemini CLI integration")
        print("   🔄 Real-time WebSocket communication")
        print("   📱 Responsive modular design")
        print("   ⚡ Easy to update/fix/tweak")
        print()
        print("⚠️  Press Ctrl+C to stop all services")
        print("="*72)
        
    def monitor_processes(self):
        """Monitor running processes."""
        def check_process(name, process):
            try:
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        print(f"[{name}] {output.strip()}")
            except Exception as e:
                print(f"❌ Error monitoring {name}: {e}")
                
        # Start monitoring threads
        for name, process in self.processes:
            monitor_thread = threading.Thread(
                target=check_process, 
                args=(name, process),
                daemon=True
            )
            monitor_thread.start()
            
    def cleanup(self):
        """Clean up processes on exit."""
        print("\n🛑 Shutting down Strategic Counsel Gen 5...")
        
        for name, process in self.processes:
            try:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"🔥 Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
                
        print("✅ All services stopped")
        
    def run(self):
        """Run the complete sophisticated system."""
        self.print_banner()
        
        if not self.check_dependencies():
            print("❌ Dependency check failed. Please install missing dependencies.")
            return
            
        self.install_dependencies()
        
        # Set up signal handler for cleanup
        def signal_handler(sig, frame):
            self.cleanup()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start all services
        self.start_backend_services()
        self.start_terminal_server()
        self.start_react_frontend()
        
        # Show endpoints
        self.show_endpoints()
        
        # Monitor processes
        self.monitor_processes()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()


if __name__ == "__main__":
    ui_system = StrategicCounselUI()
    ui_system.run() 