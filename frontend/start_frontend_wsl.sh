#!/bin/bash
# Start React Frontend in WSL

echo "🎨 Starting React Frontend in WSL..."

# Fix permissions for react-scripts
echo "🔧 Fixing permissions..."
chmod +x node_modules/.bin/react-scripts

# Start React development server
echo "🚀 Starting React development server..."
npm start 