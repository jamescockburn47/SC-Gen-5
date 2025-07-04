#!/usr/bin/env python3
"""
WSL-aware launcher for SC Gen 5 - Handles WSL paths properly
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def is_wsl():
    """Check if running in WSL"""
    # Check if we're actually in WSL environment
    if sys.platform.startswith('win'):
        # We're in Windows, but accessing WSL files
        return False
    return os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()

def get_wsl_path():
    """Get the WSL path for the current directory"""
    if sys.platform.startswith('win'):
        # Convert Windows path to WSL path
        current_path = Path.cwd()
        if 'wsl.localhost' in str(current_path):
            # Extract the WSL path from Windows path
            parts = str(current_path).split('\\')
            wsl_index = parts.index('Ubuntu-22.04')
            wsl_path = '/'.join(parts[wsl_index + 1:])
            return f"/home/{wsl_path}"
    return str(Path.cwd())

def run_wsl_command(command, cwd=None):
    """Run a command in WSL"""
    wsl_cmd = ['wsl'] + command
    if cwd:
        wsl_cmd = ['wsl', '-d', 'Ubuntu-22.04', '--cd', cwd] + command
    return subprocess.run(wsl_cmd, capture_output=True, text=True)

def main():
    print("🚀 SC Gen 5 WSL Launcher")
    print("=" * 40)
    
    # Check if we're in WSL or Windows
    if is_wsl():
        print("✅ Running in WSL environment")
        launcher_type = "wsl"
    else:
        print("⚠️ Running in Windows, will use WSL for services")
        launcher_type = "windows"
    
    # Get the project path
    if launcher_type == "windows":
        project_path = get_wsl_path()
        print(f"📁 Project path: {project_path}")
    else:
        project_path = str(Path.cwd())
        print(f"📁 Project path: {project_path}")
    
    print("\n🎯 Launch Options:")
    print("1. Start Backend Only (FastAPI)")
    print("2. Start Frontend Only (React)")
    print("3. Start Both (Backend + Frontend)")
    print("4. Install Dependencies")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        start_backend(launcher_type, project_path)
    elif choice == "2":
        start_frontend(launcher_type, project_path)
    elif choice == "3":
        start_both(launcher_type, project_path)
    elif choice == "4":
        install_dependencies(launcher_type, project_path)
    elif choice == "5":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice!")

def start_backend(launcher_type, project_path):
    """Start the FastAPI backend"""
    print("\n🔧 Starting FastAPI Backend...")
    
    if launcher_type == "windows":
        # Run in WSL
        cmd = ['python3', 'test_server.py']
        process = subprocess.Popen(['wsl', '-d', 'Ubuntu-22.04', '--cd', project_path] + cmd)
    else:
        # Run directly in WSL
        cmd = [sys.executable, 'test_server.py']
        process = subprocess.Popen(cmd)
    
    print("✅ Backend started!")
    print("📖 API Documentation: http://localhost:8000/docs")
    
    time.sleep(3)
    try:
        webbrowser.open("http://localhost:8000/docs")
    except:
        pass
    
    input("Press Enter to stop the backend...")
    process.terminate()

def start_frontend(launcher_type, project_path):
    """Start the React frontend"""
    print("\n🎨 Starting React Frontend...")
    
    frontend_path = f"{project_path}/frontend"
    
    if launcher_type == "windows":
        # Run in WSL
        cmd = ['npm', 'start']
        process = subprocess.Popen(['wsl', '-d', 'Ubuntu-22.04', '--cd', frontend_path] + cmd)
    else:
        # Run directly in WSL
        cmd = ['npm', 'start']
        process = subprocess.Popen(cmd, cwd=Path('frontend'))
    
    print("✅ Frontend started!")
    print("🌐 Frontend: http://localhost:3000")
    
    time.sleep(5)
    try:
        webbrowser.open("http://localhost:3000")
    except:
        pass
    
    input("Press Enter to stop the frontend...")
    process.terminate()

def start_both(launcher_type, project_path):
    """Start both backend and frontend"""
    print("\n🚀 Starting Full Stack...")
    
    # Start backend
    if launcher_type == "windows":
        backend_cmd = ['python3', '-m', 'uvicorn', 'sc_gen5.services.consult_service:app', '--host', '0.0.0.0', '--port', '8000']
        backend_process = subprocess.Popen(['wsl', '-d', 'Ubuntu-22.04', '--cd', project_path] + backend_cmd)
    else:
        backend_cmd = [sys.executable, '-m', 'uvicorn', 'sc_gen5.services.consult_service:app', '--host', '0.0.0.0', '--port', '8000']
        backend_process = subprocess.Popen(backend_cmd)
    
    print("✅ Backend started!")
    
    time.sleep(3)
    
    # Start frontend
    frontend_path = f"{project_path}/frontend"
    if launcher_type == "windows":
        frontend_cmd = ['npm', 'start']
        frontend_process = subprocess.Popen(['wsl', '-d', 'Ubuntu-22.04', '--cd', frontend_path] + frontend_cmd)
    else:
        frontend_cmd = ['npm', 'start']
        frontend_process = subprocess.Popen(frontend_cmd, cwd=Path('frontend'))
    
    print("✅ Frontend started!")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🌐 Frontend: http://localhost:3000")
    
    time.sleep(5)
    try:
        webbrowser.open("http://localhost:3000")
    except:
        pass
    
    input("Press Enter to stop all services...")
    backend_process.terminate()
    frontend_process.terminate()

def install_dependencies(launcher_type, project_path):
    """Install dependencies"""
    print("\n📦 Installing Dependencies...")
    
    if launcher_type == "windows":
        # Install Python dependencies in WSL
        print("Installing Python dependencies...")
        result = run_wsl_command(['pip3', 'install', '-r', 'requirements.txt'], project_path)
        if result.returncode == 0:
            print("✅ Python dependencies installed")
        else:
            print(f"❌ Python dependencies failed: {result.stderr}")
        
        # Install Node.js dependencies in WSL
        print("Installing Node.js dependencies...")
        frontend_path = f"{project_path}/frontend"
        result = run_wsl_command(['npm', 'install'], frontend_path)
        if result.returncode == 0:
            print("✅ Node.js dependencies installed")
        else:
            print(f"❌ Node.js dependencies failed: {result.stderr}")
    else:
        # Install directly in WSL
        print("Installing Python dependencies...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        if result.returncode == 0:
            print("✅ Python dependencies installed")
        
        print("Installing Node.js dependencies...")
        result = subprocess.run(['npm', 'install'], cwd=Path('frontend'))
        if result.returncode == 0:
            print("✅ Node.js dependencies installed")

if __name__ == "__main__":
    main() 