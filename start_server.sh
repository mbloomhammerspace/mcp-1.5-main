#!/bin/bash
# Startup script for Volume Canvas MCP Server with NVIDIA AI Q Toolkit

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
CONFIG_FILE="$PROJECT_DIR/config/aiq_volume_canvas_config.yml"
ENV_FILE="$PROJECT_DIR/.env"
PID_FILE="$PROJECT_DIR/pids/mcp_server.pid"

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$PROJECT_DIR/pids"
mkdir -p "$PROJECT_DIR/reports"

echo -e "${BLUE}🚀 Starting Volume Canvas MCP Server with NVIDIA AI Q Toolkit${NC}"
echo -e "${BLUE}Project Directory: $PROJECT_DIR${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed or not in PATH${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv "$PROJECT_DIR/venv"
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source "$PROJECT_DIR/venv/bin/activate"

# Install/update dependencies
echo -e "${BLUE}📥 Installing dependencies...${NC}"
pip install -q -r "$PROJECT_DIR/requirements.txt"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cat > "$ENV_FILE" << 'EOF'
# NVIDIA AI Q Toolkit Configuration
NVIDIA_AIQ_API_KEY=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

# MCP Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=9901
MCP_SERVER_PATH=/sse

# Hammerspace Configuration
HAMMERSPACE_BASE_URL=https://10.200.10.120:8443/mgmt/v1.2/rest/
HAMMERSPACE_USERNAME=admin
HAMMERSPACE_PASSWORD=H@mmerspace123!
HAMMERSPACE_VERIFY_SSL=false
HAMMERSPACE_TIMEOUT=30

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/hs_1_5_nvidia.log

# Development Configuration
DEBUG=true
TEST_MODE=false
EOF
    echo -e "${GREEN}✅ .env file created. Please update with your actual credentials.${NC}"
fi

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Configuration file not found: $CONFIG_FILE${NC}"
    exit 1
fi

# Check if server is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Server is already running with PID $PID${NC}"
        echo -e "${BLUE}To stop the server, run: ./stop_server.sh${NC}"
        exit 1
    else
        echo -e "${YELLOW}⚠️  Stale PID file found. Removing...${NC}"
        rm -f "$PID_FILE"
    fi
fi

# Check if port is available
if netstat -tlnp 2>/dev/null | grep -q ":9901 "; then
    echo -e "${RED}❌ Port 9901 is already in use${NC}"
    echo -e "${BLUE}Please stop the service using port 9901 or change the port in the configuration${NC}"
    exit 1
fi

# Start the server
echo -e "${BLUE}🚀 Starting MCP Server...${NC}"
echo -e "${BLUE}Configuration: $CONFIG_FILE${NC}"
echo -e "${BLUE}Logs: $LOG_DIR${NC}"
echo -e "${BLUE}Server URL: http://localhost:9901/sse${NC}"

# Start server in background
cd "$PROJECT_DIR"
nohup python3 scripts/start_aiq_mcp_server.py \
    --config "$CONFIG_FILE" \
    --host 0.0.0.0 \
    --port 9901 \
    --path /sse \
    > "$LOG_DIR/server_startup.log" 2>&1 &

# Save PID
echo $! > "$PID_FILE"

# Wait a moment for server to start
sleep 3

# Check if server started successfully
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Server started successfully!${NC}"
    echo -e "${GREEN}PID: $(cat $PID_FILE)${NC}"
    echo -e "${GREEN}Logs: $LOG_DIR/aiq_mcp_server.log${NC}"
    echo -e "${GREEN}Health Check: http://localhost:9901/health${NC}"
    echo -e "${GREEN}MCP Endpoint: http://localhost:9901/sse${NC}"
    
    # Run health check
    echo -e "${BLUE}🔍 Running health check...${NC}"
    sleep 2
    
    if curl -s http://localhost:9901/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Health check failed. Server may still be starting up.${NC}"
        echo -e "${BLUE}Check logs: tail -f $LOG_DIR/aiq_mcp_server.log${NC}"
    fi
    
    echo -e "${BLUE}📊 To monitor the server:${NC}"
    echo -e "${BLUE}  - Logs: tail -f $LOG_DIR/aiq_mcp_server.log${NC}"
    echo -e "${BLUE}  - Status: ps -p $(cat $PID_FILE)${NC}"
    echo -e "${BLUE}  - Stop: ./stop_server.sh${NC}"
    
else
    echo -e "${RED}❌ Failed to start server${NC}"
    echo -e "${BLUE}Check logs: cat $LOG_DIR/server_startup.log${NC}"
    rm -f "$PID_FILE"
    exit 1
fi

echo -e "${GREEN}🎉 Volume Canvas MCP Server is ready!${NC}"
