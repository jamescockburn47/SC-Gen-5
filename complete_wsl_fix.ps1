# Complete WSL Memory Fix Script (PowerShell)
Write-Host "🔧 Complete WSL Memory Fix Script" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Step 1: Check if we're in WSL
if ($env:WSL_DISTRO_NAME) {
    Write-Host "✅ Running in WSL: $env:WSL_DISTRO_NAME" -ForegroundColor Green
    
    # Check memory
    Write-Host "📊 Checking memory configuration..." -ForegroundColor Yellow
    free -h
    
    # Verify WSL config
    Write-Host "📝 Verifying WSL configuration..." -ForegroundColor Yellow
    if (Test-Path ~/.wslconfig) {
        Write-Host "✅ .wslconfig file found:" -ForegroundColor Green
        Get-Content ~/.wslconfig
    } else {
        Write-Host "❌ .wslconfig file not found!" -ForegroundColor Red
        exit 1
    }
    
    # Kill existing processes
    Write-Host "🔄 Cleaning up existing processes..." -ForegroundColor Yellow
    pkill -f "python3 app.py" 2>$null
    pkill -f "uvicorn" 2>$null
    lsof -ti:8001 | xargs kill -9 2>$null
    lsof -ti:3000 | xargs kill -9 2>$null
    
    # Clear model cache
    Write-Host "🧹 Clearing model cache..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ~/.cache/huggingface -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force /tmp/hf_cache -ErrorAction SilentlyContinue
    
    # Start backend
    Write-Host "🚀 Starting backend with new memory configuration..." -ForegroundColor Yellow
    Start-Process -NoNewWindow python3 -ArgumentList "app.py"
    
    # Wait for backend
    Write-Host "⏳ Waiting for backend to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Test system
    Write-Host "🧪 Testing system functionality..." -ForegroundColor Yellow
    
    Write-Host "📡 Testing backend status..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8001/api/rag/status" -Method Get -TimeoutSec 5
        Write-Host "✅ Backend responding" -ForegroundColor Green
    } catch {
        Write-Host "❌ Backend not responding" -ForegroundColor Red
    }
    
    Write-Host "📄 Testing document endpoint..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8001/api/rag/documents" -Method Get -TimeoutSec 5
        Write-Host "✅ Document endpoint responding" -ForegroundColor Green
    } catch {
        Write-Host "❌ Document endpoint not responding" -ForegroundColor Red
    }
    
    # Final status
    Write-Host "📊 Final system status:" -ForegroundColor Yellow
    Write-Host "Memory usage:" -ForegroundColor Yellow
    free -h
    
    Write-Host "GPU memory (if available):" -ForegroundColor Yellow
    nvidia-smi --query-gpu=memory.used,memory.total --format=csv 2>$null
    
    Write-Host "Backend processes:" -ForegroundColor Yellow
    ps aux | grep -E "(python3|uvicorn)" | grep -v grep
    
} else {
    Write-Host "❌ Not running in WSL!" -ForegroundColor Red
    Write-Host "Please run this script from within WSL" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Green
Write-Host "1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "2. Check the Dashboard for system status" -ForegroundColor White
Write-Host "3. Try uploading a document" -ForegroundColor White
Write-Host "4. Test question answering" -ForegroundColor White
Write-Host ""
Write-Host "💡 If you see issues:" -ForegroundColor Yellow
Write-Host "- Check the backend logs: tail -f app.log" -ForegroundColor White
Write-Host "- Restart the backend: pkill -f 'python3 app.py' && python3 app.py" -ForegroundColor White
Write-Host "- Verify memory: free -h (should show ~48GB)" -ForegroundColor White 