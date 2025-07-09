#!/usr/bin/env python3
"""
Script to check and diagnose GPU setup for generator model loading.
"""

import torch
import subprocess
import sys
import os

def check_gpu_setup():
    """Check GPU setup and diagnose issues."""
    print("=== GPU Setup Diagnostics ===")
    
    # Check CUDA availability
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU count: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"GPU {i}: {props.name}")
            print(f"  Memory: {props.total_memory / 1024**3:.1f}GB")
            print(f"  Compute capability: {props.major}.{props.minor}")
    
    # Check llama-cpp-python installation
    print("\n=== Llama.cpp Installation Check ===")
    try:
        import llama_cpp
        print("✓ llama-cpp-python installed")
        
        # Check if CUDA is available in llama-cpp
        try:
            from llama_cpp import Llama
            print("✓ Llama class available")
        except Exception as e:
            print(f"❌ Llama class error: {e}")
            
    except ImportError as e:
        print(f"❌ llama-cpp-python not installed: {e}")
    
    # Check for CUDA extensions
    print("\n=== CUDA Extensions Check ===")
    try:
        import auto_gptq
        print("✓ auto-gptq installed")
        
        # Check CUDA extension
        try:
            from auto_gptq.nn_modules.qlinear import qlinear_cuda
            print("✓ CUDA extension available")
        except Exception as e:
            print(f"❌ CUDA extension error: {e}")
            
    except ImportError as e:
        print(f"❌ auto-gptq not installed: {e}")
    
    # Check model file
    print("\n=== Model File Check ===")
    model_path = "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    if os.path.exists(model_path):
        size = os.path.getsize(model_path) / 1024**3
        print(f"✓ Model file exists: {size:.1f}GB")
    else:
        print(f"❌ Model file not found: {model_path}")
    
    # Test GPU memory allocation
    print("\n=== GPU Memory Test ===")
    if torch.cuda.is_available():
        try:
            # Try to allocate some GPU memory
            test_tensor = torch.randn(1000, 1000, device='cuda')
            memory_allocated = torch.cuda.memory_allocated() / 1024**3
            print(f"✓ GPU memory allocation successful: {memory_allocated:.2f}GB")
            del test_tensor
            torch.cuda.empty_cache()
        except Exception as e:
            print(f"❌ GPU memory allocation failed: {e}")

def install_cuda_extensions():
    """Install CUDA extensions if needed."""
    print("\n=== Installing CUDA Extensions ===")
    
    try:
        # Install llama-cpp-python with CUDA support
        print("Installing llama-cpp-python with CUDA support...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "llama-cpp-python[cuda]", "--force-reinstall"
        ], check=True)
        print("✓ llama-cpp-python with CUDA installed")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install llama-cpp-python with CUDA: {e}")
    
    try:
        # Install auto-gptq with CUDA support
        print("Installing auto-gptq with CUDA support...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "auto-gptq[cuda]", "--force-reinstall"
        ], check=True)
        print("✓ auto-gptq with CUDA installed")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install auto-gptq with CUDA: {e}")

def test_model_loading():
    """Test model loading with different configurations."""
    print("\n=== Model Loading Test ===")
    
    try:
        from llama_cpp import Llama
        
        model_path = "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
        
        if not os.path.exists(model_path):
            print(f"❌ Model file not found: {model_path}")
            return
        
        # Test CPU loading
        print("Testing CPU loading...")
        try:
            model_cpu = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=4,
                n_gpu_layers=0,
                verbose=False
            )
            print("✓ CPU loading successful")
            
            # Test generation
            response = model_cpu("[INST] Test. [/INST]", max_tokens=10)
            if isinstance(response, dict) and 'choices' in response:
                print("✓ CPU generation successful")
            else:
                print("❌ CPU generation failed")
                
        except Exception as e:
            print(f"❌ CPU loading failed: {e}")
        
        # Test GPU loading if available
        if torch.cuda.is_available():
            print("Testing GPU loading...")
            try:
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                gpu_layers = 10 if gpu_memory >= 6.0 else 5
                
                model_gpu = Llama(
                    model_path=model_path,
                    n_ctx=2048,
                    n_threads=4,
                    n_gpu_layers=gpu_layers,
                    verbose=False
                )
                print(f"✓ GPU loading successful with {gpu_layers} layers")
                
                # Test generation
                response = model_gpu("[INST] Test. [/INST]", max_tokens=10)
                if isinstance(response, dict) and 'choices' in response:
                    print("✓ GPU generation successful")
                else:
                    print("❌ GPU generation failed")
                    
            except Exception as e:
                print(f"❌ GPU loading failed: {e}")
        
    except ImportError as e:
        print(f"❌ llama-cpp-python not available: {e}")

if __name__ == "__main__":
    print("🔍 GPU Setup Diagnostics")
    print("=" * 40)
    
    check_gpu_setup()
    
    # Ask user if they want to install CUDA extensions
    response = input("\nInstall CUDA extensions? (y/n): ")
    if response.lower() == 'y':
        install_cuda_extensions()
        print("\nRe-running diagnostics...")
        check_gpu_setup()
    
    test_model_loading()
    
    print("\n✅ Diagnostics completed!") 