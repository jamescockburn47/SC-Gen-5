#!/bin/bash
# Start React Frontend in WSL

echo "🎨 Starting React Frontend in WSL..."

cd "/home/jcockburn/SC Gen 5/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start React development server
echo "🚀 Starting React development server..."
npm start 