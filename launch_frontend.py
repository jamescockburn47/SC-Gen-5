#!/usr/bin/env python3
"""
Launch SC Gen 5 React Frontend
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def main():
    print("🎨 Starting SC Gen 5 React Frontend...")
    
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        print("Make sure you're in the SC Gen 5 root directory")
        return
    
    # Check if node_modules exists
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            print("✅ Frontend dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            print("Make sure Node.js and npm are installed")
            return
        except FileNotFoundError:
            print("❌ npm not found. Please install Node.js from https://nodejs.org/")
            return
    else:
        print("✅ Frontend dependencies already installed")
    
    # Start the React development server
    print("🚀 Starting React development server...")
    try:
        process = subprocess.Popen(
            ["npm", "start"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        print("✅ React server started!")
        print("🌐 Frontend will be available at: http://localhost:3000")
        
        # Wait a moment for the server to start
        time.sleep(5)
        
        # Open browser
        try:
            webbrowser.open("http://localhost:3000")
            print("🌐 Browser opened to React frontend")
        except:
            print("⚠️ Could not open browser automatically")
            print("Please open: http://localhost:3000")
        
        print("\n🎉 React Frontend is running!")
        print("Press Ctrl+C to stop the server")
        
        # Keep the process running and show output
        try:
            if process.stdout:
                for line in process.stdout:
                    print(line.rstrip())
        except KeyboardInterrupt:
            print("\n🛑 Stopping React server...")
            process.terminate()
            process.wait()
            print("✅ React server stopped")
            
    except Exception as e:
        print(f"❌ Failed to start React server: {e}")

if __name__ == "__main__":
    main() 