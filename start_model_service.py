#!/usr/bin/env python3
"""
Startup script for the independent model service.
This service can be started, stopped, and restarted without affecting the main API.
"""

import sys
import os
import subprocess
import signal
import time
import json
from pathlib import Path

def get_service_status():
    """Check if the model service is running."""
    status_file = Path("data/model_service_status.json")
    if not status_file.exists():
        return False, "Status file not found"
    
    try:
        # Check if status file is recent
        if time.time() - status_file.stat().st_mtime > 30:
            return False, "Status file too old"
        
        with open(status_file, 'r') as f:
            status = json.load(f)
        
        last_heartbeat = status.get("last_heartbeat", 0)
        if time.time() - last_heartbeat > 30:
            return False, "Service heartbeat too old"
        
        return True, f"Service {status.get('service_id', 'unknown')} running"
        
    except Exception as e:
        return False, f"Error reading status: {e}"

def start_service():
    """Start the model service."""
    print("Starting model service...")
    
    # Check if already running
    running, status = get_service_status()
    if running:
        print(f"Model service already running: {status}")
        return True
    
    try:
        # Start the service as a subprocess
        process = subprocess.Popen([
            sys.executable, "-m", "src.sc_gen5.rag.v2.model_service"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for startup
        time.sleep(3)
        
        # Check if it started successfully
        if process.poll() is None:  # Still running
            running, status = get_service_status()
            if running:
                print(f"✓ Model service started successfully: {status}")
                return True
            else:
                print(f"⚠ Model service process started but not responding: {status}")
                return False
        else:
            # Process exited
            stdout, stderr = process.communicate()
            print(f"✗ Model service failed to start:")
            print(f"  Exit code: {process.returncode}")
            if stdout:
                print(f"  Stdout: {stdout.decode()}")
            if stderr:
                print(f"  Stderr: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"✗ Error starting model service: {e}")
        return False

def stop_service():
    """Stop the model service."""
    print("Stopping model service...")
    
    # Check if running
    running, status = get_service_status()
    if not running:
        print("Model service not running")
        return True
    
    try:
        # Try to find and stop the process
        # This is a simple approach - in production you'd want proper PID management
        result = subprocess.run([
            "pkill", "-f", "model_service"
        ], capture_output=True)
        
        # Wait for shutdown
        time.sleep(2)
        
        # Check if stopped
        running, status = get_service_status()
        if not running:
            print("✓ Model service stopped")
            return True
        else:
            print(f"⚠ Model service still running: {status}")
            return False
            
    except Exception as e:
        print(f"✗ Error stopping model service: {e}")
        return False

def restart_service():
    """Restart the model service."""
    print("Restarting model service...")
    stop_service()
    time.sleep(1)
    return start_service()

def status_service():
    """Show model service status."""
    running, status = get_service_status()
    
    if running:
        print(f"✓ Model service running: {status}")
        
        # Show detailed status
        try:
            status_file = Path("data/model_service_status.json")
            with open(status_file, 'r') as f:
                detailed_status = json.load(f)
            
            print(f"  Service ID: {detailed_status.get('service_id', 'unknown')}")
            print(f"  Overall Status: {detailed_status.get('overall_status', 'unknown')}")
            print(f"  Crash Count: {detailed_status.get('crash_count', 0)}")
            
            models = detailed_status.get('models', {})
            print("  Model Status:")
            for model, state in models.items():
                print(f"    {model}: {state}")
            
            gpu_memory = detailed_status.get('gpu_memory')
            if gpu_memory:
                print(f"  GPU Memory: {gpu_memory.get('allocated_gb', 0):.1f}GB / {gpu_memory.get('total_gb', 0):.1f}GB")
            
        except Exception as e:
            print(f"  Error reading detailed status: {e}")
    else:
        print(f"✗ Model service not running: {status}")
    
    return running

def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("Usage: python start_model_service.py <command>")
        print("Commands:")
        print("  start   - Start the model service")
        print("  stop    - Stop the model service")
        print("  restart - Restart the model service")
        print("  status  - Show service status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        success = start_service()
        sys.exit(0 if success else 1)
    elif command == "stop":
        success = stop_service()
        sys.exit(0 if success else 1)
    elif command == "restart":
        success = restart_service()
        sys.exit(0 if success else 1)
    elif command == "status":
        running = status_service()
        sys.exit(0 if running else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()