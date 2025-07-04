#!/bin/bash
# ===================================
# SC GEN 5 - SIMPLE LAUNCHER
# ===================================

echo "🏛️ STRATEGIC COUNSEL GEN 5"
echo "=========================="

cd "/home/jcockburn/SC Gen 5"

echo "🚀 Starting services..."

# Kill any existing services
pkill -f "uvicorn.*main:app" 2>/dev/null
pkill -f "react-scripts" 2>/dev/null
sleep 2

# Start backend
echo "📡 Starting API backend..."
python3 -m uvicorn src.sc_gen5.api.main:app --host 0.0.0.0 --port 8000 --reload &
sleep 3

# Start frontend
echo "⚛️ Starting React frontend..."
cd frontend
npm start &
cd ..

echo ""
echo "✅ LAUNCHING IN 10 SECONDS..."
echo "   React UI: http://localhost:3000"
echo "   Claude CLI: Available in browser"
echo ""

sleep 10

# Open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v wslview &> /dev/null; then
    wslview http://localhost:3000
else
    echo "🌐 Open browser manually: http://localhost:3000"
fi

echo "✨ SC Gen 5 is now running!"
echo "Press Ctrl+C to stop all services"

# Keep running
wait