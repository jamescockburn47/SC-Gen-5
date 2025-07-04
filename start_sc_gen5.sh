#!/bin/bash
# SC Gen 5 Startup Script

echo "🏛️ Strategic Counsel Gen 5 - Starting..."
cd "/home/jcockburn/SC Gen 5"

# Check if services are running
echo "🔍 Checking services..."

# Start API if not running
if ! curl -s http://localhost:8000 >/dev/null 2>&1; then
    echo "📡 Starting FastAPI backend..."
    python3 -m uvicorn src.sc_gen5.api.main:app --host 0.0.0.0 --port 8000 --reload &
    echo "✅ Backend starting..."
else
    echo "✅ Backend already running"
fi

# Start React if not running  
if ! curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "⚛️ Starting React frontend..."
    cd frontend
    npm start &
    cd ..
    echo "✅ Frontend starting..."
else
    echo "✅ Frontend already running"
fi

echo "⏳ Waiting for services..."
sleep 3

echo ""
echo "🎉 Strategic Counsel Gen 5 Ready!"
echo "   React UI: http://localhost:3000"
echo "   API: http://localhost:8000"
echo "   Claude CLI: Available in browser"
echo ""
echo "Press Ctrl+C to stop"

# Keep script running
wait