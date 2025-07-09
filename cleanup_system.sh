#!/bin/bash
# SC Gen 5 - Comprehensive System Cleanup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}   SC Gen 5 - System Cleanup Script${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# Function to log messages
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Kill all related processes
log "Step 1: Killing all related processes..."

# Kill Python processes
pkill -f "python3 app.py" 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true

# Kill Node processes
pkill -f "react-scripts" 2>/dev/null || true
pkill -f "node.*start.js" 2>/dev/null || true

# Kill processes on specific ports
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

sleep 3
success "Process cleanup completed"

# Step 2: Clean up redundant test files
log "Step 2: Cleaning up redundant test files..."

# Remove test files that are not in the tests directory
find . -maxdepth 1 -name "test_*.py" -type f -delete
find . -maxdepth 1 -name "test_*.sh" -type f -delete
find . -maxdepth 1 -name "test_*.bat" -type f -delete

# Remove redundant documentation files
find . -maxdepth 1 -name "*_SUMMARY.md" -type f -delete
find . -maxdepth 1 -name "*_FIXES.md" -type f -delete
find . -maxdepth 1 -name "*_GUIDE.md" -type f -delete

# Remove redundant log files (keep only recent ones)
find . -maxdepth 1 -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true

# Remove redundant startup scripts (keep only the main one)
find . -maxdepth 1 -name "start_*.bat" -not -name "start_sc_gen5.sh" -type f -delete
find . -maxdepth 1 -name "START_*.bat" -type f -delete

success "File cleanup completed"

# Step 3: Clean up Python cache
log "Step 3: Cleaning up Python cache..."

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.pyc" -delete 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

success "Python cache cleanup completed"

# Step 4: Clean up Node modules cache (if needed)
log "Step 4: Cleaning up Node modules cache..."

if [ -d "frontend/node_modules" ]; then
    cd frontend
    npm cache clean --force 2>/dev/null || true
    cd ..
fi

success "Node cache cleanup completed"

# Step 5: Verify core files exist
log "Step 5: Verifying core files..."

required_files=("app.py" "start_sc_gen5.sh" "frontend/package.json" "frontend/src/App.tsx")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    success "All core files present"
else
    error "Missing core files: ${missing_files[*]}"
    exit 1
fi

# Step 6: Test ports are free
log "Step 6: Testing ports are free..."

if lsof -ti:8001 >/dev/null 2>&1; then
    error "Port 8001 is still in use"
    lsof -ti:8001 | xargs kill -9
else
    success "Port 8001 is free"
fi

if lsof -ti:3000 >/dev/null 2>&1; then
    error "Port 3000 is still in use"
    lsof -ti:3000 | xargs kill -9
else
    success "Port 3000 is free"
fi

# Step 7: Final verification
log "Step 7: Final verification..."

echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}   Cleanup Summary${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""

# Check if processes are killed
if pgrep -f "python.*app.py" >/dev/null; then
    warning "Some Python processes may still be running"
else
    success "All Python processes killed"
fi

if pgrep -f "react-scripts" >/dev/null; then
    warning "Some Node processes may still be running"
else
    success "All Node processes killed"
fi

# Check ports
if ! lsof -ti:8001 >/dev/null 2>&1; then
    success "Port 8001 is free"
else
    error "Port 8001 is still in use"
fi

if ! lsof -ti:3000 >/dev/null 2>&1; then
    success "Port 3000 is free"
else
    error "Port 3000 is still in use"
fi

echo ""
echo -e "${GREEN}System cleanup completed successfully!${NC}"
echo -e "${BLUE}You can now run: ./start_sc_gen5.sh start${NC}"
echo "" 