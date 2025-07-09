#!/usr/bin/env python3
"""
Setup script for Mistral-7B-Instruct-v0.2 GGUF model with llama.cpp
"""

import os
import subprocess
import sys
from pathlib import Path

def install_llama_cpp():
    """Install llama-cpp-python."""
    print("Installing llama-cpp-python...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "llama-cpp-python", "--upgrade"
        ], check=True)
        print("✓ llama-cpp-python installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install llama-cpp-python: {e}")
        return False
    return True

def download_model():
    """Download the Mistral-7B-Instruct-v0.2 GGUF model."""
    print("Downloading Mistral-7B-Instruct-v0.2 GGUF model...")
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    model_path = models_dir / "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    
    if model_path.exists():
        print(f"✓ Model already exists at {model_path}")
        return True
    
    # Download from Hugging Face
    model_url = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    
    try:
        import requests
        print(f"Downloading from {model_url}...")
        
        response = requests.get(model_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rDownload progress: {percent:.1f}%", end='', flush=True)
        
        print(f"\n✓ Model downloaded successfully to {model_path}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to download model: {e}")
        print("Please download manually from:")
        print("https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF")
        return False

def test_model():
    """Test the model to ensure it works."""
    print("Testing model...")
    try:
        from llama_cpp import Llama
        
        model_path = Path("models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
        if not model_path.exists():
            print("✗ Model file not found")
            return False
        
        # Load model
        llm = Llama(
            model_path=str(model_path),
            n_ctx=4096,
            n_threads=8,
            n_gpu_layers=0,
            verbose=False
        )
        
        # Test generation
        test_prompt = "[INST] What is 2+2? [/INST]"
        response = llm(test_prompt, max_tokens=50, temperature=0.1)
        
        if hasattr(response, 'choices') and response.choices:
            generated_text = response.choices[0].text
            print(f"✓ Model test successful. Generated: {generated_text[:100]}...")
            return True
        else:
            print("✗ Model test failed - no response generated")
            return False
            
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("Setting up Mistral-7B-Instruct-v0.2 GGUF model...")
    print("=" * 50)
    
    # Install llama-cpp-python
    if not install_llama_cpp():
        return False
    
    # Download model
    if not download_model():
        return False
    
    # Test model
    if not test_model():
        return False
    
    print("\n" + "=" * 50)
    print("✓ Setup completed successfully!")
    print("The model is ready to use with llama.cpp")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 