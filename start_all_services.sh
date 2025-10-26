#!/bin/bash
# Comprehensive startup script for all MCP services
# Launches all services in screen sessions for persistence across logouts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/home/ubuntu/mcp-1.5-main"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"

# Ensure directories exist
mkdir -p "$LOG_DIR" "$PID_DIR"

# Service configurations
declare -A SERVICES=(
    ["hammerspace-mcp"]="Hammerspace MCP Server"
    ["milvus-mcp"]="Milvus MCP Server"
    ["kubernetes-mcp"]="Kubernetes MCP Server"
    ["file-monitor"]="File Monitor Daemon"
    ["web-ui"]="Web UI Server"
    ["milvus-port-forward"]="Milvus Port Forward"
)

# Screen session names
declare -A SCREEN_SESSIONS=(
    ["hammerspace-mcp"]="hs-mcp"
    ["milvus-mcp"]="milvus-mcp"
    ["kubernetes-mcp"]="k8s-mcp"
    ["file-monitor"]="file-monitor"
    ["web-ui"]="web-ui"
    ["milvus-port-forward"]="milvus-pf"
)

# Service commands
declare -A SERVICE_COMMANDS=(
    ["hammerspace-mcp"]="cd $PROJECT_ROOT && python3 src/aiq_hstk_mcp_server.py"
    ["milvus-mcp"]="cd $PROJECT_ROOT/mcp-server-milvus && python3 -m mcp_server_milvus.server"
    ["kubernetes-mcp"]="echo 'Kubernetes MCP server not implemented yet'"
    ["file-monitor"]="cd $PROJECT_ROOT && python3 src/file_monitor_daemon.py"
    ["web-ui"]="cd $PROJECT_ROOT/web_ui && python3 app.py"
    ["milvus-port-forward"]="kubectl port-forward svc/milvus 19530:19530"
)

# Service ports (for health checks)
declare -A SERVICE_PORTS=(
    ["hammerspace-mcp"]=""  # Uses stdio, not HTTP
    ["milvus-mcp"]="9902"
    ["kubernetes-mcp"]="9903"
    ["file-monitor"]=""
    ["web-ui"]="5000"
    ["milvus-port-forward"]="19530"
)

# Log files
declare -A LOG_FILES=(
    ["hammerspace-mcp"]="$LOG_DIR/hammerspace_mcp.log"
    ["milvus-mcp"]="$LOG_DIR/milvus_mcp.log"
    ["kubernetes-mcp"]="$LOG_DIR/kubernetes_mcp.log"
    ["file-monitor"]="$LOG_DIR/file_monitor_daemon.log"
    ["web-ui"]="$LOG_DIR/web_ui.log"
    ["milvus-port-forward"]="$LOG_DIR/milvus_port_forward.log"
)

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

info_message() {
    echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Check if screen is installed
check_screen() {
    if ! command -v screen &> /dev/null; then
        error_message "Screen is not installed. Installing screen..."
        sudo apt-get update && sudo apt-get install -y screen
    fi
}

# Kill processes using required ports
kill_port_conflicts() {
    log_message "Checking for port conflicts..."
    
    for service in "${!SERVICE_PORTS[@]}"; do
        local port="${SERVICE_PORTS[$service]}"
        if [ -n "$port" ]; then
            local pid=$(lsof -ti:$port 2>/dev/null || true)
            if [ -n "$pid" ]; then
                warning_message "Killing process $pid using port $port for ${SERVICES[$service]}"
                kill -9 "$pid" 2>/dev/null || true
                sleep 1
            fi
        fi
    done
}

# Check if a screen session exists
screen_session_exists() {
    local session_name=$1
    screen -list | grep -q "$session_name"
}

# Kill a screen session
kill_screen_session() {
    local session_name=$1
    if screen_session_exists "$session_name"; then
        log_message "Killing screen session: $session_name"
        screen -S "$session_name" -X quit 2>/dev/null || true
        sleep 1
    fi
}

# Start a service in a screen session
start_service() {
    local service=$1
    local session_name="${SCREEN_SESSIONS[$service]}"
    local command="${SERVICE_COMMANDS[$service]}"
    local log_file="${LOG_FILES[$service]}"
    local port="${SERVICE_PORTS[$service]}"
    
    log_message "Starting ${SERVICES[$service]}..."
    
    # Kill existing session if it exists
    kill_screen_session "$session_name"
    
    # Create a robust startup script that handles restarts
    local startup_script="/tmp/start_${service}.sh"
    cat > "$startup_script" << EOF
#!/bin/bash
# Auto-restart script for ${SERVICES[$service]}
# This script ensures the service restarts if it crashes

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT"
export HOME="/home/ubuntu"

# Function to log with timestamp
log_with_time() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S') \$1" >> "$log_file"
}

log_with_time "🚀 Starting ${SERVICES[$service]} in persistent screen session"
log_with_time "📁 Working directory: \$(pwd)"
log_with_time "🐍 Python path: \$PYTHONPATH"

# Start the service with auto-restart capability
while true; do
    log_with_time "🔄 Executing: $command"
    
    # Execute the command
    $command >> "$log_file" 2>&1
    exit_code=\$?
    
    log_with_time "⚠️ Service exited with code \$exit_code"
    
    # If it's a clean exit (0), don't restart
    if [ \$exit_code -eq 0 ]; then
        log_with_time "✅ Service stopped cleanly"
        break
    fi
    
    # Otherwise, wait and restart
    log_with_time "🔄 Restarting service in 5 seconds..."
    sleep 5
done

log_with_time "🏁 Service session ended"
EOF
    
    chmod +x "$startup_script"
    
    # Start the service in a screen session with the robust startup script
    screen -dmS "$session_name" bash -c "$startup_script"
    
    # Wait a moment for the service to start
    sleep 3
    
    # Check if the screen session is running
    if screen_session_exists "$session_name"; then
        success_message "${SERVICES[$service]} started in screen session '$session_name'"
        info_message "Log file: $log_file"
        
        # Health check for services with ports
        if [ -n "$port" ]; then
            sleep 2
            if ss -tlnp 2>/dev/null | grep -q ":$port "; then
                success_message "${SERVICES[$service]} is listening on port $port"
            else
                warning_message "${SERVICES[$service]} may not be ready yet (port $port not listening)"
            fi
        fi
        
        return 0
    else
        error_message "Failed to start ${SERVICES[$service]}"
        return 1
    fi
}

# Stop a service
stop_service() {
    local service=$1
    local session_name="${SCREEN_SESSIONS[$service]}"
    
    log_message "Stopping ${SERVICES[$service]}..."
    
    if screen_session_exists "$session_name"; then
        kill_screen_session "$session_name"
        success_message "${SERVICES[$service]} stopped"
    else
        info_message "${SERVICES[$service]} was not running"
    fi
}

# Check service status
check_service_status() {
    local service=$1
    local session_name="${SCREEN_SESSIONS[$service]}"
    local port="${SERVICE_PORTS[$service]}"
    
    if screen_session_exists "$session_name"; then
        echo -e "${GREEN}✓${NC} ${SERVICES[$service]}"
        if [ -n "$port" ]; then
            if ss -tlnp 2>/dev/null | grep -q ":$port "; then
                echo -e "  ${GREEN}✓${NC} Port $port listening"
            else
                echo -e "  ${YELLOW}⚠${NC} Port $port not listening"
            fi
        fi
        echo -e "  ${BLUE}Screen:${NC} $session_name"
        echo -e "  ${BLUE}Log:${NC} ${LOG_FILES[$service]}"
    else
        echo -e "${RED}✗${NC} ${SERVICES[$service]}"
    fi
}

# Show all service status
show_status() {
    echo -e "${PURPLE}=== MCP Services Status ===${NC}"
    echo
    
    for service in "${!SERVICES[@]}"; do
        check_service_status "$service"
        echo
    done
    
    echo -e "${PURPLE}=== Service URLs ===${NC}"
    echo -e "Web UI:        http://localhost:5000"
    echo -e "Web UI (LAN):  http://10.0.0.236:5000"
    echo -e "Hammerspace:   http://localhost:9901/sse"
    echo -e "Milvus:        http://localhost:9902/sse"
    echo -e "Kubernetes:    http://localhost:9903/sse"
    
    echo
    echo -e "${PURPLE}=== Screen Sessions ===${NC}"
    screen -list | grep -E "(hs-mcp|milvus-mcp|k8s-mcp|file-monitor|web-ui)" || echo "No MCP screen sessions found"
}

# Show logs for a service
show_logs() {
    local service=$1
    local log_file="${LOG_FILES[$service]}"
    
    if [ -z "$service" ]; then
        echo "Available services: ${!SERVICES[*]}"
        return 1
    fi
    
    if [ ! -f "$log_file" ]; then
        error_message "Log file not found: $log_file"
        return 1
    fi
    
    echo -e "${BLUE}=== ${SERVICES[$service]} Logs (last 50 lines) ===${NC}"
    tail -50 "$log_file"
}

# Attach to a service screen session
attach_service() {
    local service=$1
    local session_name="${SCREEN_SESSIONS[$service]}"
    
    if [ -z "$service" ]; then
        echo "Available services: ${!SERVICES[*]}"
        return 1
    fi
    
    if screen_session_exists "$session_name"; then
        info_message "Attaching to ${SERVICES[$service]} screen session..."
        echo -e "${YELLOW}Press Ctrl+A then D to detach from screen session${NC}"
        screen -r "$session_name"
    else
        error_message "${SERVICES[$service]} is not running"
        return 1
    fi
}

# Start all services
start_all() {
    log_message "Starting all MCP services..."
    
    # Check dependencies
    check_screen
    
    # Kill any port conflicts
    kill_port_conflicts
    
    # Start services in order (prioritize core services first)
    local failed_services=()
    local core_services=("milvus-port-forward" "file-monitor" "web-ui" "hammerspace-mcp")
    local optional_services=("milvus-mcp" "kubernetes-mcp")
    
    # Start core services first
    for service in "${core_services[@]}"; do
        if ! start_service "$service"; then
            failed_services+=("$service")
        fi
        sleep 2
    done
    
    # Start optional services
    for service in "${optional_services[@]}"; do
        if ! start_service "$service"; then
            failed_services+=("$service")
            warning_message "Optional service $service failed to start (this is OK)"
        fi
        sleep 2
    done
    
    echo
    if [ ${#failed_services[@]} -eq 0 ]; then
        success_message "All services started successfully!"
    else
        warning_message "Some services failed to start: ${failed_services[*]}"
    fi
    
    echo
    show_status
}

# Stop all services
stop_all() {
    log_message "Stopping all MCP services..."
    
    for service in "${!SERVICES[@]}"; do
        stop_service "$service"
    done
    
    success_message "All services stopped"
}

# Restart all services
restart_all() {
    log_message "Restarting all MCP services..."
    stop_all
    sleep 3
    start_all
}

# Clean up old logs
cleanup_logs() {
    log_message "Cleaning up old log files..."
    
    for log_file in "${LOG_FILES[@]}"; do
        if [ -f "$log_file" ]; then
            # Keep last 1000 lines
            tail -1000 "$log_file" > "${log_file}.tmp" && mv "${log_file}.tmp" "$log_file"
        fi
    done
    
    success_message "Log cleanup completed"
}

# Create systemd service for auto-start on boot
create_systemd_service() {
    log_message "Creating systemd service for auto-start on boot..."
    
    local service_file="/etc/systemd/system/mcp-services.service"
    
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=MCP Services (File Monitor, Web UI, Hammerspace MCP)
After=network.target
Wants=network.target

[Service]
Type=forking
User=ubuntu
Group=ubuntu
WorkingDirectory=$PROJECT_ROOT
ExecStart=$PROJECT_ROOT/start_all_services.sh start
ExecStop=$PROJECT_ROOT/start_all_services.sh stop
ExecReload=$PROJECT_ROOT/start_all_services.sh restart
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment variables
Environment=HOME=/home/ubuntu
Environment=PYTHONPATH=$PROJECT_ROOT

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable mcp-services.service
    
    success_message "Systemd service created and enabled"
    info_message "Services will now start automatically on boot"
    info_message "To manage: sudo systemctl start/stop/restart mcp-services"
}

# Remove systemd service
remove_systemd_service() {
    log_message "Removing systemd service..."
    
    sudo systemctl stop mcp-services.service 2>/dev/null || true
    sudo systemctl disable mcp-services.service 2>/dev/null || true
    sudo rm -f /etc/systemd/system/mcp-services.service
    sudo systemctl daemon-reload
    
    success_message "Systemd service removed"
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
        show_status
        ;;
    "logs")
        show_logs "${2:-}"
        ;;
    "attach")
        attach_service "${2:-}"
        ;;
    "cleanup")
        cleanup_logs
        ;;
    "install-service")
        create_systemd_service
        ;;
    "remove-service")
        remove_systemd_service
        ;;
    *)
        echo -e "${PURPLE}MCP Services Management Script${NC}"
        echo
        echo "Usage: $0 {start|stop|restart|status|logs|attach|cleanup|install-service|remove-service}"
        echo
        echo "Commands:"
        echo "  start                    - Start all services in screen sessions"
        echo "  stop                     - Stop all services"
        echo "  restart                  - Restart all services"
        echo "  status                   - Show service status and URLs"
        echo "  logs <service>           - Show logs for a service"
        echo "  attach <service>         - Attach to a service screen session"
        echo "  cleanup                  - Clean up old log entries"
        echo "  install-service          - Install systemd service for auto-start on boot"
        echo "  remove-service           - Remove systemd service"
        echo
        echo "Available services:"
        for service in "${!SERVICES[@]}"; do
            echo "  $service - ${SERVICES[$service]}"
        done
        echo
        echo "Examples:"
        echo "  $0 start                              # Start all services"
        echo "  $0 restart                            # Restart all services"
        echo "  $0 logs web-ui                        # Show Web UI logs"
        echo "  $0 attach file-monitor                # Attach to file monitor"
        echo "  $0 status                             # Check service status"
        echo
        echo "Screen sessions will persist even if you log out!"
        echo "Use 'screen -list' to see all sessions"
        echo "Use 'screen -r <session-name>' to attach to a session"
        exit 1
        ;;
esac
