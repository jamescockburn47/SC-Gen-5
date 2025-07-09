#!/bin/bash

echo "🔧 Complete WSL Memory Fix Script"
echo "=================================="

# Step 1: Check current memory
echo "📊 Checking current memory configuration..."
free -h

# Step 2: Verify WSL config
echo "📝 Verifying WSL configuration..."
if [ -f ~/.wslconfig ]; then
    echo "✅ .wslconfig file found:"
    cat ~/.wslconfig
else
    echo "❌ .wslconfig file not found!"
    exit 1
fi

# Step 3: Kill any existing processes
echo "🔄 Cleaning up existing processes..."
pkill -f "python3 app.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Step 4: Clear any cached models
echo "🧹 Clearing model cache..."
rm -rf ~/.cache/huggingface 2>/dev/null || true
rm -rf /tmp/hf_cache 2>/dev/null || true

# Step 5: Start the backend
echo "🚀 Starting backend with new memory configuration..."
python3 app.py &

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 10

# Step 6: Test the system
echo "🧪 Testing system functionality..."

# Test backend status
echo "📡 Testing backend status..."
curl -s http://localhost:8001/api/rag/status | python3 -m json.tool 2>/dev/null || echo "❌ Backend not responding"

# Test document endpoint
echo "📄 Testing document endpoint..."
curl -s http://localhost:8001/api/rag/documents | python3 -m json.tool 2>/dev/null || echo "❌ Document endpoint not responding"

# Step 7: Show final status
echo "📊 Final system status:"
echo "Memory usage:"
free -h

echo "GPU memory (if available):"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv 2>/dev/null || echo "GPU not available"

echo "Backend processes:"
ps aux | grep -E "(python3|uvicorn)" | grep -v grep || echo "No backend processes found"

echo ""
echo "🎯 Next Steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Check the Dashboard for system status"
echo "3. Try uploading a document"
echo "4. Test question answering"
echo ""
echo "💡 If you see issues:"
echo "- Check the backend logs: tail -f app.log"
echo "- Restart the backend: pkill -f 'python3 app.py' && python3 app.py"
echo "- Verify memory: free -h (should show ~48GB)" 