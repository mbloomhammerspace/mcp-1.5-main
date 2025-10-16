#!/bin/bash
# Stop script for Volume Canvas MCP Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_DIR/pids/mcp_server.pid"

echo -e "${BLUE}🛑 Stopping Volume Canvas MCP Server...${NC}"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  No PID file found. Server may not be running.${NC}"
    exit 0
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Process with PID $PID is not running. Removing stale PID file.${NC}"
    rm -f "$PID_FILE"
    exit 0
fi

echo -e "${BLUE}📋 Found server process with PID: $PID${NC}"

# Try graceful shutdown first
echo -e "${BLUE}🔄 Attempting graceful shutdown...${NC}"
kill -TERM "$PID"

# Wait for graceful shutdown
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server stopped gracefully${NC}"
        rm -f "$PID_FILE"
        exit 0
    fi
    echo -e "${BLUE}⏳ Waiting for graceful shutdown... ($i/10)${NC}"
    sleep 1
done

# Force kill if graceful shutdown failed
echo -e "${YELLOW}⚠️  Graceful shutdown failed. Force killing process...${NC}"
kill -KILL "$PID"

# Wait a moment and verify
sleep 1
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Server stopped forcefully${NC}"
    rm -f "$PID_FILE"
else
    echo -e "${RED}❌ Failed to stop server${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Volume Canvas MCP Server stopped successfully!${NC}"
