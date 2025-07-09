#!/usr/bin/env python3

import psutil
import torch

def check_memory():
    print("🔍 Memory Configuration Check")
    print("============================")
    
    # Check RAM
    ram_gb = psutil.virtual_memory().total / (1024**3)
    print(f"📊 Total RAM: {ram_gb:.1f}GB")
    
    # Check GPU
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"🎮 GPU Memory: {gpu_memory:.1f}GB")
    else:
        print("❌ CUDA not available")
    
    # Check if we have enough memory for models
    if ram_gb >= 40:
        print("✅ Sufficient RAM for large models")
    else:
        print("⚠️  Limited RAM - may cause OOM errors")
    
    print("\n💡 If RAM is still 31GB, restart WSL2:")
    print("   Windows PowerShell: wsl --shutdown && wsl")

if __name__ == "__main__":
    check_memory()
