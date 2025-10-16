#!/bin/bash

# Hammerspace MCP Services Management Script
# Handles: MCP Server, Web UI, File Monitor, and all dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/home/ubuntu/mcp-1.5-main"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"

# Ensure directories exist
mkdir -p "$LOG_DIR" "$PID_DIR"

# Service PIDs
MCP_PID_FILE="$PID_DIR/mcp_server.pid"
WEBUI_PID_FILE="$PID_DIR/web_ui.pid"
MONITOR_PID_FILE="$PID_DIR/file_monitor.pid"

# Log files
MCP_LOG="$LOG_DIR/mcp_server.log"
WEBUI_LOG="$LOG_DIR/web_ui.log"
MONITOR_LOG="$LOG_DIR/file_monitor.log"

# Python paths
PYTHON3="/usr/bin/python3"
MCP_SERVER="$PROJECT_ROOT/src/aiq_hstk_mcp_server.py"
WEBUI_APP="$PROJECT_ROOT/web_ui/app.py"

log_message() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error_message() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

success_message() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

warning_message() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check if a process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Kill a process by PID file
kill_process() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_message "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            
            # Wait for graceful shutdown
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                warning_message "$service_name didn't stop gracefully, forcing kill..."
                kill -9 "$pid"
                sleep 1
            fi
            
            rm -f "$pid_file"
            success_message "$service_name stopped"
        else
            rm -f "$pid_file"
            warning_message "$service_name was not running (stale PID file removed)"
        fi
    else
        log_message "$service_name was not running"
    fi
}

# Start MCP Server
start_mcp_server() {
    if is_running "$MCP_PID_FILE"; then
        log_message "MCP Server is already running (PID: $(cat $MCP_PID_FILE))"
        return 0
    fi
    
    log_message "Starting MCP Server..."
    cd "$PROJECT_ROOT"
    
    # Set environment variables
    export PYTHONPATH="$PROJECT_ROOT"
    export HOME="/home/ubuntu"
    
    # Start MCP server in background
    nohup "$PYTHON3" "$MCP_SERVER" > "$MCP_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$MCP_PID_FILE"
    
    # Wait a moment to see if it started successfully
    sleep 2
    if ps -p "$pid" > /dev/null 2>&1; then
        success_message "MCP Server started (PID: $pid)"
        log_message "MCP Server log: $MCP_LOG"
    else
        error_message "Failed to start MCP Server"
        rm -f "$MCP_PID_FILE"
        return 1
    fi
}

# Start Web UI
start_web_ui() {
    if is_running "$WEBUI_PID_FILE"; then
        log_message "Web UI is already running (PID: $(cat $WEBUI_PID_FILE))"
        return 0
    fi
    
    log_message "Starting Web UI..."
    cd "$PROJECT_ROOT/web_ui"
    
    # Set environment variables
    export PYTHONPATH="$PROJECT_ROOT"
    export HOME="/home/ubuntu"
    
    # Start Web UI in background
    nohup "$PYTHON3" "$WEBUI_APP" > "$WEBUI_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$WEBUI_PID_FILE"
    
    # Wait a moment to see if it started successfully
    sleep 3
    if ps -p "$pid" > /dev/null 2>&1; then
        success_message "Web UI started (PID: $pid)"
        log_message "Web UI available at: http://localhost:5000"
        log_message "Web UI log: $WEBUI_LOG"
    else
        error_message "Failed to start Web UI"
        rm -f "$WEBUI_PID_FILE"
        return 1
    fi
}

# Check system dependencies
check_dependencies() {
    log_message "Checking system dependencies..."
    
    # Check Python
    if ! command -v "$PYTHON3" > /dev/null 2>&1; then
        error_message "Python3 not found at $PYTHON3"
        return 1
    fi
    
    # Check HSTK CLI
    if ! command -v "/home/ubuntu/.local/bin/hs" > /dev/null 2>&1; then
        error_message "HSTK CLI not found at /home/ubuntu/.local/bin/hs"
        return 1
    fi
    
    # Check if files exist
    if [ ! -f "$MCP_SERVER" ]; then
        error_message "MCP Server not found at $MCP_SERVER"
        return 1
    fi
    
    if [ ! -f "$WEBUI_APP" ]; then
        error_message "Web UI app not found at $WEBUI_APP"
        return 1
    fi
    
    # Check if Anvil mounts are accessible
    if [ ! -d "/mnt/anvil/hub" ]; then
        warning_message "Anvil hub mount not found at /mnt/anvil/hub"
    fi
    
    if [ ! -d "/mnt/anvil/modelstore" ]; then
        warning_message "Anvil modelstore mount not found at /mnt/anvil/modelstore"
    fi
    
    success_message "Dependencies check completed"
}

# Check service status
status() {
    echo -e "${BLUE}=== Hammerspace MCP Services Status ===${NC}"
    
    if is_running "$MCP_PID_FILE"; then
        echo -e "MCP Server:    ${GREEN}RUNNING${NC} (PID: $(cat $MCP_PID_FILE))"
    else
        echo -e "MCP Server:    ${RED}STOPPED${NC}"
    fi
    
    if is_running "$WEBUI_PID_FILE"; then
        echo -e "Web UI:        ${GREEN}RUNNING${NC} (PID: $(cat $WEBUI_PID_FILE))"
    else
        echo -e "Web UI:        ${RED}STOPPED${NC}"
    fi
    
    echo -e "\n${BLUE}=== Service URLs ===${NC}"
    echo -e "Web UI:        http://localhost:5000"
    echo -e "Web UI (LAN):  http://10.0.0.236:5000"
    
    echo -e "\n${BLUE}=== Log Files ===${NC}"
    echo -e "MCP Server:    $MCP_LOG"
    echo -e "Web UI:        $WEBUI_LOG"
    
    echo -e "\n${BLUE}=== Mount Status ===${NC}"
    mount | grep -E "(anvil|10.0.0.165)" | grep nfs4 | wc -l | xargs -I {} echo "Active Anvil mounts: {}"
}

# Start all services
start_all() {
    log_message "Starting Hammerspace MCP Services..."
    
    # Check dependencies first
    if ! check_dependencies; then
        error_message "Dependency check failed"
        exit 1
    fi
    
    # Start services in order
    start_mcp_server
    sleep 2
    start_web_ui
    
    success_message "All services started successfully!"
    
    # Show status
    echo
    status
}

# Stop all services
stop_all() {
    log_message "Stopping Hammerspace MCP Services..."
    
    # Stop services in reverse order
    kill_process "$WEBUI_PID_FILE" "Web UI"
    kill_process "$MCP_PID_FILE" "MCP Server"
    
    success_message "All services stopped"
}

# Restart all services
restart_all() {
    log_message "Restarting Hammerspace MCP Services..."
    stop_all
    sleep 2
    start_all
}

# Show logs
show_logs() {
    local service=$1
    case $service in
        "mcp")
            echo -e "${BLUE}=== MCP Server Logs (last 50 lines) ===${NC}"
            tail -50 "$MCP_LOG"
            ;;
        "webui"|"web")
            echo -e "${BLUE}=== Web UI Logs (last 50 lines) ===${NC}"
            tail -50 "$WEBUI_LOG"
            ;;
        "all")
            echo -e "${BLUE}=== All Service Logs (last 20 lines each) ===${NC}"
            echo -e "${YELLOW}--- MCP Server ---${NC}"
            tail -20 "$MCP_LOG"
            echo -e "\n${YELLOW}--- Web UI ---${NC}"
            tail -20 "$WEBUI_LOG"
            ;;
        *)
            echo "Usage: $0 logs {mcp|webui|all}"
            exit 1
            ;;
    esac
}

# Clean up old logs
cleanup_logs() {
    log_message "Cleaning up old log files..."
    
    # Keep last 1000 lines of each log
    for log_file in "$MCP_LOG" "$WEBUI_LOG"; do
        if [ -f "$log_file" ]; then
            tail -1000 "$log_file" > "${log_file}.tmp" && mv "${log_file}.tmp" "$log_file"
        fi
    done
    
    success_message "Log cleanup completed"
}

# Main script logic
case "${1:-}" in
    "start")
        start_all
        ;;
    "stop")
        stop_all
        ;;
    "restart")
        restart_all
        ;;
    "status")
        status
        ;;
    "logs")
        show_logs "${2:-all}"
        ;;
    "cleanup")
        cleanup_logs
        ;;
    *)
        echo -e "${BLUE}Hammerspace MCP Services Management Script${NC}"
        echo
        echo "Usage: $0 {start|stop|restart|status|logs|cleanup}"
        echo
        echo "Commands:"
        echo "  start     - Start all services (MCP Server + Web UI)"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  status    - Show service status and URLs"
        echo "  logs      - Show logs (usage: logs {mcp|webui|all})"
        echo "  cleanup   - Clean up old log entries"
        echo
        echo "Examples:"
        echo "  $0 start                    # Start all services"
        echo "  $0 restart                  # Restart all services"
        echo "  $0 logs webui               # Show Web UI logs"
        echo "  $0 status                   # Check service status"
        exit 1
        ;;
esac

