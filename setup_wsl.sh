#!/bin/bash
# WSL Setup Script for SC Gen 5

echo "🚀 Setting up SC Gen 5 in WSL..."

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install Python 3 and pip
echo "🐍 Installing Python 3..."
sudo apt install -y python3 python3-pip python3-venv

# Install Node.js and npm
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install build tools (needed for some npm packages)
echo "🔧 Installing build tools..."
sudo apt install -y build-essential

# Verify installations
echo "✅ Verifying installations..."
python3 --version
node --version
npm --version

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

echo "🎉 Setup complete!"
echo ""
echo "To start the application:"
echo "1. Run: python3 wsl_launcher.py"
echo "2. Or run directly in WSL terminal"
echo ""
echo "The launcher will handle WSL/Windows path conversion automatically." 