#!/bin/bash
# SC Gen 5 Cache Clear Script - React Frontend

echo "🧹 Clearing SC Gen 5 caches..."

# Python caches (for FastAPI backend)
echo "Clearing Python __pycache__..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
rm -rf .mypy_cache

# React/Node caches  
echo "Clearing React development cache..."
rm -rf frontend/node_modules/.cache 2>/dev/null

# Browser cache reminder
echo "📱 Remember to hard refresh your browser:"
echo "   Ctrl + Shift + R (Linux/Windows)"
echo "   Cmd + Shift + R (Mac)"
echo ""
echo "✅ Cache clearing complete!"
echo ""
echo "🔄 Your React frontend will auto-refresh"
echo "   Main UI: http://localhost:3000"  
echo "   API: http://localhost:8000"