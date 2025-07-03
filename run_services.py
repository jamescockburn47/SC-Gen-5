#!/usr/bin/env python3
"""Script to run SC Gen 5 services locally for development."""

import os
import subprocess
import sys
import time
from pathlib import Path


def check_ollama():
    """Check if Ollama is running."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def start_ollama():
    """Start Ollama if not running."""
    if check_ollama():
        print("✅ Ollama is already running")
        return True
    
    print("🚀 Starting Ollama...")
    try:
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for Ollama to start
        for i in range(30):
            if check_ollama():
                print("✅ Ollama started successfully")
                return True
            time.sleep(1)
            print(f"⏳ Waiting for Ollama... ({i+1}/30)")
        
        print("❌ Failed to start Ollama")
        return False
        
    except FileNotFoundError:
        print("❌ Ollama not found. Please install Ollama first:")
        print("   Visit: https://ollama.ai/download")
        return False


def pull_models():
    """Pull required Ollama models."""
    models = ["mixtral:latest", "mistral:latest", "phi3:latest"]
    
    for model in models:
        print(f"📥 Pulling model: {model}")
        try:
            result = subprocess.run(["ollama", "pull", model], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Successfully pulled {model}")
            else:
                print(f"⚠️  Failed to pull {model}: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Error pulling {model}: {e}")


def start_service(name, module, port, env_vars=None):
    """Start a service using uvicorn."""
    print(f"🚀 Starting {name} on port {port}")
    
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            module, 
            "--host", "0.0.0.0", 
            "--port", str(port),
            "--reload"
        ], env=env)
        
        print(f"✅ {name} started (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None


def start_streamlit():
    """Start Streamlit UI."""
    print("🚀 Starting Streamlit UI on port 8501")
    
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "src/sc_gen5/ui/app.py",
            "--server.address", "0.0.0.0",
            "--server.port", "8501"
        ])
        
        print(f"✅ Streamlit UI started (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Failed to start Streamlit UI: {e}")
        return None


def main():
    """Main function to orchestrate service startup."""
    print("🏛️  Strategic Counsel Gen 5 - Development Server")
    print("=" * 50)
    
    # Add local bin to PATH for streamlit and other tools
    import os
    local_bin = os.path.expanduser("~/.local/bin")
    if local_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH', '')}"
    
    # Set PYTHONPATH to include src directory
    src_path = str(Path.cwd() / "src")
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    if src_path not in current_pythonpath:
        os.environ["PYTHONPATH"] = f"{src_path}:{current_pythonpath}" if current_pythonpath else src_path
    
    # Check if we're in the right directory
    if not Path("src/sc_gen5").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Step 1: Start Ollama
    if not start_ollama():
        print("❌ Cannot proceed without Ollama")
        sys.exit(1)
    
    # Step 2: Pull models (optional)
    pull_choice = input("\n📥 Pull Ollama models? (y/N): ").lower().strip()
    if pull_choice in ['y', 'yes']:
        pull_models()
    
    # Step 3: Start services
    print("\n🚀 Starting SC Gen 5 services...")
    
    processes = []
    
    # Consult Service
    consult_process = start_service(
        "Consult Service", 
        "sc_gen5.services.consult_service:app", 
        8000
    )
    if consult_process:
        processes.append(("Consult Service", consult_process))
    
    time.sleep(2)
    
    # Ingest Service  
    ingest_process = start_service(
        "Companies House Ingest Service",
        "sc_gen5.services.ch_ingest_service:app",
        8001
    )
    if ingest_process:
        processes.append(("Ingest Service", ingest_process))
    
    time.sleep(2)
    
    # Streamlit UI
    ui_process = start_streamlit()
    if ui_process:
        processes.append(("Streamlit UI", ui_process))
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 SC Gen 5 services started!")
    print("\nEndpoints:")
    print("📊 Streamlit UI:          http://localhost:8501")
    print("🔍 Consult API:           http://localhost:8000")
    print("🏢 Companies House API:   http://localhost:8001") 
    print("🤖 Ollama API:            http://localhost:11434")
    print("\nAPI Documentation:")
    print("📚 Consult API Docs:      http://localhost:8000/docs")
    print("📚 Ingest API Docs:       http://localhost:8001/docs")
    
    print("\n⚠️  Press Ctrl+C to stop all services")
    
    try:
        # Wait for user interrupt
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        
        for name, process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ Stopped {name}")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔪 Force killed {name}")
            except Exception as e:
                print(f"⚠️  Error stopping {name}: {e}")
        
        print("👋 All services stopped. Goodbye!")


if __name__ == "__main__":
    main() 