#!/bin/bash

echo "🔧 Fixing WSL2 Memory and Device Issues"
echo "========================================"

# Step 1: Create WSL2 configuration file
echo "📝 Creating WSL2 configuration file..."
cat > ~/.wslconfig << 'EOF'
[wsl2]
memory=48GB
processors=8
swap=8GB
localhostForwarding=true
EOF

echo "✅ WSL2 configuration created"

# Step 2: Fix device mismatch issues in the RAG system
echo "🔧 Fixing device mismatch issues..."

# Create a backup of the original models.py
cp src/sc_gen5/rag/v2/models.py src/sc_gen5/rag/v2/models.py.backup

# Fix the device handling in the utility model loading
sed -i 's/device_map="cpu"/device_map="auto"/g' src/sc_gen5/rag/v2/models.py

# Ensure consistent device handling in the test functions
sed -i 's/if torch.cuda.is_available() and hasattr(utility_model, .device.):/if torch.cuda.is_available() and hasattr(utility_model, "device"):/g' src/sc_gen5/rag/v2/models.py

echo "✅ Device mismatch fixes applied"

# Step 3: Create a restart script
echo "📝 Creating restart script..."
cat > restart_with_memory_fix.sh << 'EOF'
#!/bin/bash

echo "🔄 Restarting WSL2 with memory fix..."
echo "Please run this in Windows PowerShell as Administrator:"
echo ""
echo "wsl --shutdown"
echo "wsl"
echo ""
echo "Then run this script again to verify the fix."
EOF

chmod +x restart_with_memory_fix.sh

# Step 4: Create verification script
echo "📝 Creating verification script..."
cat > verify_memory_fix.py << 'EOF'
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
EOF

chmod +x verify_memory_fix.py

echo "✅ All fixes applied!"
echo ""
echo "📋 Next Steps:"
echo "1. Run: ./restart_with_memory_fix.sh"
echo "2. In Windows PowerShell (as Administrator):"
echo "   wsl --shutdown"
echo "   wsl"
echo "3. Run: python3 verify_memory_fix.py"
echo "4. Start the server: python3 app.py"
echo ""
echo "🎯 Expected Results:"
echo "- RAM should show ~48GB instead of 31GB"
echo "- Device mismatch errors should be resolved"
echo "- GPU memory usage should be optimized" 