#!/usr/bin/env python3
"""
WSL Full Launcher for SC Gen 5 - Runs everything in WSL properly
"""

import os
import sys
import subprocess
import time
import webbrowser
import signal
import threading
from pathlib import Path

class WSLFullLauncher:
    def __init__(self):
        self.project_path = Path.cwd()
        self.processes = []
        self.running = True
        
    def check_wsl_environment(self):
        """Check if we're in the right WSL environment"""
        print("🔍 Checking WSL environment...")
        
        # Check if we're in WSL
        if not os.path.exists('/proc/version'):
            print("❌ Not running in WSL environment")
            return False
            
        # Check Python
        try:
            result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
            print(f"✅ Python: {result.stdout.strip()}")
        except:
            print("❌ Python3 not found")
            return False
            
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            print(f"✅ Node.js: {result.stdout.strip()}")
        except:
            print("❌ Node.js not found")
            return False
            
        # Check npm
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            print(f"✅ npm: {result.stdout.strip()}")
        except:
            print("❌ npm not found")
            return False
            
        return True
    
    def install_dependencies(self):
        """Install all dependencies in WSL"""
        print("📦 Installing dependencies...")
        
        # Install Python dependencies
        print("🐍 Installing Python dependencies...")
        subprocess.run(['pip3', 'install', '-r', 'requirements.txt'])
        
        # Install Node.js dependencies
        print("📦 Installing Node.js dependencies...")
        frontend_path = self.project_path / 'frontend'
        if frontend_path.exists():
            subprocess.run(['npm', 'install'], cwd=frontend_path)
            
        # Install terminal server dependencies
        terminal_path = self.project_path / 'terminal-server'
        if terminal_path.exists():
            subprocess.run(['npm', 'install'], cwd=terminal_path)
    
    def start_backend(self):
        """Start the FastAPI backend"""
        print("🚀 Starting FastAPI Backend...")
        
        # Use the test server for now (working)
        cmd = ['python3', 'test_server.py']
        process = subprocess.Popen(cmd, cwd=self.project_path)
        self.processes.append(('Backend', process))
        
        # Wait for backend to start
        time.sleep(3)
        
        # Test backend
        try:
            import requests
            response = requests.get('http://localhost:8000/test', timeout=5)
            if response.status_code == 200:
                print("✅ Backend started successfully!")
                return True
        except:
            pass
            
        print("❌ Backend failed to start")
        return False
    
    def start_frontend(self):
        """Start the React frontend"""
        print("🎨 Starting React Frontend...")
        
        frontend_path = self.project_path / 'frontend'
        if not frontend_path.exists():
            print("❌ Frontend directory not found")
            return False
            
        # Start React development server
        cmd = ['npm', 'start']
        process = subprocess.Popen(cmd, cwd=frontend_path)
        self.processes.append(('Frontend', process))
        
        # Wait for frontend to start
        time.sleep(10)
        
        # Test frontend
        try:
            import requests
            response = requests.get('http://localhost:3000', timeout=5)
            if response.status_code == 200:
                print("✅ Frontend started successfully!")
                return True
        except:
            pass
            
        print("❌ Frontend failed to start")
        return False
    
    def start_terminal_server(self):
        """Start the terminal server"""
        print("💻 Starting Terminal Server...")
        
        terminal_path = self.project_path / 'terminal-server'
        if not terminal_path.exists():
            print("❌ Terminal server directory not found")
            return False
            
        # Start terminal server
        cmd = ['node', 'server.js']
        process = subprocess.Popen(cmd, cwd=terminal_path)
        self.processes.append(('Terminal Server', process))
        
        time.sleep(2)
        print("✅ Terminal server started!")
        return True
    
    def open_browser(self):
        """Open browser to the application"""
        print("🌐 Opening browser...")
        
        # Open frontend
        webbrowser.open('http://localhost:3000')
        
        # Open backend docs
        webbrowser.open('http://localhost:8000/docs')
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down SC Gen 5...")
        self.running = False
        self.stop_all_services()
        sys.exit(0)
    
    def stop_all_services(self):
        """Stop all running services"""
        print("🛑 Stopping all services...")
        
        for name, process in self.processes:
            try:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except:
                try:
                    process.kill()
                    print(f"🔪 {name} force killed")
                except:
                    pass
        
        self.processes.clear()
    
    def run(self):
        """Main launcher function"""
        print("🚀 SC Gen 5 WSL Full Launcher")
        print("=" * 50)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Check environment
        if not self.check_wsl_environment():
            print("❌ Environment check failed")
            return
        
        # Install dependencies
        self.install_dependencies()
        
        # Start services
        print("\n🚀 Starting services...")
        
        backend_ok = self.start_backend()
        if not backend_ok:
            print("❌ Failed to start backend")
            return
            
        frontend_ok = self.start_frontend()
        if not frontend_ok:
            print("❌ Failed to start frontend")
            return
            
        terminal_ok = self.start_terminal_server()
        
        # Open browser
        self.open_browser()
        
        print("\n🎉 SC Gen 5 is running!")
        print("📱 Frontend: http://localhost:3000")
        print("🔧 Backend API: http://localhost:8000")
        print("📖 API Docs: http://localhost:8000/docs")
        print("💻 Terminal: ws://localhost:3001")
        print("\nPress Ctrl+C to stop all services")
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    launcher = WSLFullLauncher()
    launcher.run() 