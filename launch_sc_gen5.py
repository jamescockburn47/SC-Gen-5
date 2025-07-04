#!/usr/bin/env python3
"""
SC Gen 5 Launcher
Simple executable Python script
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

def main():
    print("🏛️ Strategic Counsel Gen 5 - Starting...")
    print("=" * 40)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    try:
        print("🛑 Stopping any existing services...")
        # Kill existing processes
        try:
            subprocess.run(["pkill", "-f", "uvicorn.*main:app"], check=False)
            subprocess.run(["pkill", "-f", "react-scripts"], check=False)
            time.sleep(2)
        except:
            pass
        
        print("📡 Starting FastAPI backend...")
        # Start backend
        backend = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "src.sc_gen5.api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
        
        print("⚛️ Starting React frontend...")
        # Start frontend
        frontend_dir = project_dir / "frontend"
        frontend = subprocess.Popen(["npm", "start"], cwd=frontend_dir)
        
        print("⏳ Waiting for services to start...")
        time.sleep(10)
        
        print("🌐 Opening browser...")
        webbrowser.open("http://localhost:3000")
        
        print("\n" + "=" * 40)
        print("✅ SC Gen 5 is now running!")
        print("   React UI: http://localhost:3000")
        print("   API Docs: http://localhost:8000/docs")
        print("   Claude CLI: Available in browser")
        print("=" * 40)
        print("\nPress Ctrl+C to stop all services")
        
        # Wait for user to stop
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping services...")
            backend.terminate()
            frontend.terminate()
            print("👋 SC Gen 5 stopped")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nManual commands:")
        print("Backend: python3 -m uvicorn src.sc_gen5.api.main:app --reload")
        print("Frontend: cd frontend && npm start")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()