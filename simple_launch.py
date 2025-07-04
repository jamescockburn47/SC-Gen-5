#!/usr/bin/env python3
"""
Simple SC Gen 5 Launcher - Just start the backend and open browser
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def main():
    print("🚀 Starting SC Gen 5 Backend...")
    
    # Start the FastAPI backend
    try:
        process = subprocess.Popen([
            sys.executable, "test_server.py"
        ])
        
        print("✅ Backend started successfully!")
        print("📖 API Documentation: http://localhost:8000/docs")
        print("🔗 Backend API: http://localhost:8000")
        
        # Wait a moment for the server to start
        time.sleep(3)
        
        # Open browser to API docs
        try:
            webbrowser.open("http://localhost:8000/docs")
            print("🌐 Browser opened to API documentation")
        except:
            print("⚠️ Could not open browser automatically")
            print("Please open: http://localhost:8000/docs")
        
        print("\n🎉 SC Gen 5 is running!")
        print("Press Ctrl+C to stop the server")
        
        # Keep the process running
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            process.terminate()
            process.wait()
            print("✅ Server stopped")
            
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're in the SC Gen 5 directory")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Check if the consult_service.py file exists")

if __name__ == "__main__":
    main() 