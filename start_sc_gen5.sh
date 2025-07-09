#!/bin/bash
# SC Gen 5 - LexCognito AI Platform Startup Script
# Sophisticated startup script with process management and error handling

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
BACKEND_PORT=8001
FRONTEND_PORT=3000
MAX_STARTUP_ATTEMPTS=60
STARTUP_TIMEOUT=60

# Logging
LOG_FILE="$PROJECT_DIR/startup.log"
ERROR_LOG="$PROJECT_DIR/error.log"

# Function to log messages
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$ERROR_LOG"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill processes on a port
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        log "Killing processes on port $port: $pids"
        kill -9 $pids 2>/dev/null || true
        sleep 2
    fi
}

# Function to check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 is not installed"
        return 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed"
        return 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "$PROJECT_DIR/app.py" ]; then
        error "app.py not found. Please run this script from the SC Gen 5 root directory"
        return 1
    fi
    
    # Check if .env exists
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        warning ".env file not found. Some features may not work properly"
    fi
    
    success "Dependencies check completed"
    return 0
}

# Function to clean up existing processes
cleanup_processes() {
    log "Cleaning up existing processes..."
    
    # Kill processes on our ports
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    
    # Kill any existing Python processes for this project
    local python_pids=$(ps aux | grep "python.*app.py" | grep -v grep | awk '{print $2}')
    if [ ! -z "$python_pids" ]; then
        log "Killing existing Python processes: $python_pids"
        kill -9 $python_pids 2>/dev/null || true
    fi
    
    # Kill any existing Node processes for this project
    local node_pids=$(ps aux | grep "node.*react-scripts" | grep -v grep | awk '{print $2}')
    if [ ! -z "$node_pids" ]; then
        log "Killing existing Node processes: $node_pids"
        kill -9 $node_pids 2>/dev/null || true
    fi
    
    sleep 3
    success "Process cleanup completed"
}

# Function to start backend
start_backend() {
    log "Starting backend server..."
    
    # Check if backend port is free
    if check_port $BACKEND_PORT; then
        error "Port $BACKEND_PORT is already in use"
        return 1
    fi
    
    # Start backend in background
    cd "$PROJECT_DIR"
    nohup python3 app.py > backend.log 2>&1 &
    local backend_pid=$!
    
    # Wait for backend to start
    local attempts=0
    while [ $attempts -lt $MAX_STARTUP_ATTEMPTS ]; do
        if check_port $BACKEND_PORT; then
            success "Backend started successfully (PID: $backend_pid)"
            return 0
        fi
        
        attempts=$((attempts + 1))
        log "Waiting for backend to start... (attempt $attempts/$MAX_STARTUP_ATTEMPTS)"
        sleep 5
        
        # Check if process is still running
        if ! kill -0 $backend_pid 2>/dev/null; then
            error "Backend process died unexpectedly"
            cat backend.log
            return 1
        fi
    done
    
    error "Backend failed to start after $MAX_STARTUP_ATTEMPTS attempts"
    cat backend.log
    return 1
}

# Function to start frontend
start_frontend() {
    log "Starting frontend server..."
    
    # Check if frontend port is free
    if check_port $FRONTEND_PORT; then
        warning "Port $FRONTEND_PORT is already in use. Frontend may not start properly."
    fi
    
    # Start frontend in background
    cd "$PROJECT_DIR/frontend"
    nohup npm start > ../frontend.log 2>&1 &
    local frontend_pid=$!
    
    # Wait for frontend to start
    local attempts=0
    while [ $attempts -lt $MAX_STARTUP_ATTEMPTS ]; do
        if check_port $FRONTEND_PORT; then
            success "Frontend started successfully (PID: $frontend_pid)"
            return 0
        fi
        
        attempts=$((attempts + 1))
        log "Waiting for frontend to start... (attempt $attempts/$MAX_STARTUP_ATTEMPTS)"
        sleep 2
        
        # Check if process is still running
        if ! kill -0 $frontend_pid 2>/dev/null; then
            error "Frontend process died unexpectedly"
            cat ../frontend.log
            return 1
        fi
    done
    
    warning "Frontend may not have started properly. Check frontend.log for details."
    return 0
}

# Function to test backend health
test_backend() {
    log "Testing backend health..."
    
    local attempts=0
    while [ $attempts -lt 30 ]; do
        if curl -s http://localhost:$BACKEND_PORT/api/cloud-consultation/health > /dev/null 2>&1; then
            success "Backend health check passed"
            return 0
        fi
        
        attempts=$((attempts + 1))
        log "Waiting for backend health check... (attempt $attempts/30)"
        sleep 5
    done
    
    error "Backend health check failed"
    return 1
}

# Function to display status
show_status() {
    echo ""
    echo "================================================"
    echo "   SC Gen 5 - LexCognito AI Platform Status"
    echo "================================================"
    echo ""
    
    # Backend status
    if check_port $BACKEND_PORT; then
        echo -e "${GREEN}✓ Backend${NC} - Running on port $BACKEND_PORT"
        if curl -s http://localhost:$BACKEND_PORT/api/cloud-consultation/health > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓ Health check passed${NC}"
        else
            echo -e "  ${YELLOW}⚠ Health check failed${NC}"
        fi
    else
        echo -e "${RED}✗ Backend${NC} - Not running"
    fi
    
    # Frontend status
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend${NC} - Running on port $FRONTEND_PORT"
    else
        echo -e "${RED}✗ Frontend${NC} - Not running"
    fi
    
    echo ""
    echo "Access URLs:"
    echo "  Backend API: http://localhost:$BACKEND_PORT"
    echo "  Frontend:    http://localhost:$FRONTEND_PORT"
    echo ""
}

# Function to handle shutdown
shutdown() {
    log "Shutting down SC Gen 5..."
    
    # Kill processes on our ports
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    
    # Kill any remaining processes
    local pids=$(ps aux | grep -E "(python.*app.py|node.*react-scripts)" | grep -v grep | awk '{print $2}')
    if [ ! -z "$pids" ]; then
        log "Killing remaining processes: $pids"
        kill -9 $pids 2>/dev/null || true
    fi
    
    success "Shutdown completed"
}

# Function to show help
show_help() {
    echo "SC Gen 5 - LexCognito AI Platform Startup Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  start     Start SC Gen 5 (default)"
    echo "  stop      Stop SC Gen 5"
    echo "  restart   Restart SC Gen 5"
    echo "  status    Show current status"
    echo "  clean     Clean up processes and ports"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start     # Start the platform"
    echo "  $0 status    # Check current status"
    echo "  $0 stop      # Stop the platform"
}

# Main function
main() {
    local action=${1:-start}
    
    # Create log files
    touch "$LOG_FILE"
    touch "$ERROR_LOG"
    
    # Clear old logs
    echo "" > "$LOG_FILE"
    echo "" > "$ERROR_LOG"
    
    log "================================================"
    log "   SC Gen 5 - LexCognito AI Platform Startup"
    log "================================================"
    log ""
    
    case $action in
        start)
            log "Starting SC Gen 5..."
            
            # Check dependencies
            if ! check_dependencies; then
                error "Dependency check failed"
                exit 1
            fi
            
            # Clean up existing processes
            cleanup_processes
            
            # Start backend
            if ! start_backend; then
                error "Backend startup failed"
                shutdown
                exit 1
            fi
            
            # Test backend health
            if ! test_backend; then
                error "Backend health check failed"
                shutdown
                exit 1
            fi
            
            # Start frontend
            if ! start_frontend; then
                warning "Frontend startup may have failed"
            fi
            
            # Show final status
            show_status
            
            success "SC Gen 5 startup completed"
            log "Check the logs for any issues:"
            log "  Backend: $PROJECT_DIR/backend.log"
            log "  Frontend: $PROJECT_DIR/frontend.log"
            log "  Startup: $LOG_FILE"
            log "  Errors: $ERROR_LOG"
            ;;
            
        stop)
            log "Stopping SC Gen 5..."
            shutdown
            success "SC Gen 5 stopped"
            ;;
            
        restart)
            log "Restarting SC Gen 5..."
            shutdown
            sleep 2
            $0 start
            ;;
            
        status)
            show_status
            ;;
            
        clean)
            log "Cleaning up processes and ports..."
            cleanup_processes
            success "Cleanup completed"
            ;;
            
        help)
            show_help
            ;;
            
        *)
            error "Unknown action: $action"
            show_help
            exit 1
            ;;
    esac
}

# Trap signals for graceful shutdown (only for explicit shutdown)
trap 'log "Received interrupt signal"; shutdown; exit 1' INT TERM

# Run main function
main "$@"