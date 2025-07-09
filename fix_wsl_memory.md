# Fix WSL2 Memory Limitations

## Problem
Your WSL2 instance is limited to 32GB RAM instead of your full 64GB, causing:
- Device mismatch errors (CPU vs GPU tensors)
- OOM errors during model loading
- Poor performance with large models

## Solution

### Step 1: Create WSL2 Configuration File
Create a `.wslconfig` file in your Windows user directory:

```powershell
# In Windows PowerShell (not WSL)
notepad $env:USERPROFILE\.wslconfig
```

Add this content:
```ini
[wsl2]
memory=48GB
processors=8
swap=8GB
localhostForwarding=true
```

### Step 2: Restart WSL2
In Windows PowerShell (as Administrator):
```powershell
wsl --shutdown
wsl
```

### Step 3: Verify Memory Increase
In WSL2:
```bash
free -h
```

You should see ~48GB total memory instead of 31GB.

### Step 4: Update Model Loading Strategy
The current system is trying to load models on CPU but some tensors are on GPU, causing device mismatch. With more RAM, we can:

1. **Load utility model on GPU** (small model, fast inference)
2. **Load reasoning model on GPU** (large model, but with 48GB RAM we have space)
3. **Use proper device management**

### Alternative: Quick Fix for Current Setup
If you can't restart WSL2 right now, we can fix the device mismatch by ensuring all models use the same device:

```python
# Force all models to use CPU
device = "cpu"
# Or force all models to use GPU
device = "cuda"
```

## Expected Results
- 48GB RAM available instead of 31GB
- No more device mismatch errors
- Better performance with large models
- Stable RAG system operation

## Next Steps
1. Apply the WSL2 configuration
2. Restart WSL2
3. Test the system with full memory access
4. Optimize model loading strategy for 48GB RAM 