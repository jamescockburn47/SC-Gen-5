#!/bin/bash
# Start the FastAPI backend and React frontend for SC Gen 5
# Usage: Run this script from WSL or via a Windows shortcut

PROJECT_DIR="/home/jcockburn/SC Gen 5"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Start FastAPI backend (run_services.py launches all backend services)
echo "Starting FastAPI backend..."
cd "$PROJECT_DIR"
nohup python3 run_services.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID"

# Wait a few seconds to ensure backend is up
sleep 5

# Start React frontend
echo "Starting React frontend..."
cd "$FRONTEND_DIR"
nohup npm start > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID $FRONTEND_PID"

# Wait for frontend to start
sleep 8

# Open React UI in Windows default browser (wslview)
echo "Opening React UI in browser..."
wslview http://localhost:3000

echo "All services started. You can close this window if you like." 