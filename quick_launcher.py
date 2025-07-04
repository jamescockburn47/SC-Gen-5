#!/usr/bin/env python3
"""
SC Gen 5 Quick Launcher - Simple desktop launcher
Starts React frontend and FastAPI backend
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

def main():
    """Quick launcher for SC Gen 5."""
    print("🏛️ Strategic Counsel Gen 5 - Quick Launcher")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    try:
        # Check if services are already running
        print("🔍 Checking for running services...")
        
        # Check if React is running (port 3000)
        try:
            import requests
            react_running = requests.get("http://localhost:3000", timeout=2).status_code == 200
        except:
            react_running = False
            
        # Check if API is running (port 8000)
        try:
            import requests
            api_running = requests.get("http://localhost:8000", timeout=2).status_code == 200
        except:
            api_running = False
        
        if react_running and api_running:
            print("✅ Services already running!")
            print("   React Frontend: http://localhost:3000")
            print("   FastAPI Backend: http://localhost:8000")
            print("🌐 Opening browser...")
            webbrowser.open("http://localhost:3000")
            return
        
        print("🚀 Starting services...")
        
        # Start FastAPI backend if not running
        if not api_running:
            print("📡 Starting FastAPI backend...")
            subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "src.sc_gen5.api.main:app", 
                "--host", "0.0.0.0", 
                "--port", "8000", 
                "--reload"
            ])
            print("✅ FastAPI backend starting...")
        else:
            print("✅ FastAPI backend already running")
        
        # Start React frontend if not running
        if not react_running:
            print("⚛️ Starting React frontend...")
            # Change to frontend directory
            frontend_dir = project_dir / "frontend"
            subprocess.Popen([
                "npm", "start"
            ], cwd=frontend_dir)
            print("✅ React frontend starting...")
        else:
            print("✅ React frontend already running")
        
        # Wait for services to start
        print("⏳ Waiting for services to initialize...")
        time.sleep(5)
        
        # Open browser
        print("🌐 Opening Strategic Counsel Gen 5...")
        webbrowser.open("http://localhost:3000")
        
        print("\n" + "=" * 50)
        print("🎉 Strategic Counsel Gen 5 is starting!")
        print("   Main Interface: http://localhost:3000")
        print("   API Docs: http://localhost:8000/docs")
        print("   Claude CLI: Available in browser interface")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n👋 Launcher interrupted by user")
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        print("Try running manually:")
        print("   Backend: python3 -m uvicorn src.sc_gen5.api.main:app --reload")
        print("   Frontend: cd frontend && npm start")

if __name__ == "__main__":
    main()