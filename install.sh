#!/bin/bash
# MCP 1.5 Server Installer
# Standalone installer for the Volume Canvas MCP Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 MCP 1.5 Server Installer${NC}"
echo -e "${BLUE}============================${NC}"

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python $PYTHON_VERSION is installed, but Python $REQUIRED_VERSION or higher is required.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Get installation directory
INSTALL_DIR=${1:-"/opt/mcp-1.5"}
echo -e "${BLUE}📁 Installation directory: $INSTALL_DIR${NC}"

# Create installation directory
sudo mkdir -p "$INSTALL_DIR"
sudo chown $USER:$USER "$INSTALL_DIR"

# Copy files
echo -e "${BLUE}📦 Copying files...${NC}"
cp -r . "$INSTALL_DIR/"
cd "$INSTALL_DIR"

# Create virtual environment
echo -e "${BLUE}🐍 Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}📥 Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service
echo -e "${BLUE}⚙️  Creating systemd service...${NC}"
sudo tee /etc/systemd/system/mcp-1.5.service > /dev/null << EOF
[Unit]
Description=MCP 1.5 Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/scripts/start_aiq_mcp_server.py --host 0.0.0.0 --port 9901
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create environment file template
echo -e "${BLUE}📝 Creating environment configuration...${NC}"
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# NVIDIA AI Q Toolkit Configuration
NVIDIA_AIQ_API_KEY=your_nvidia_api_key_here

# MCP Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=9901
MCP_SERVER_PATH=/sse

# Hammerspace Configuration
HAMMERSPACE_BASE_URL=https://your-hammerspace-host:8443/mgmt/v1.2/rest/
HAMMERSPACE_USERNAME=admin
HAMMERSPACE_PASSWORD=your_password_here
HAMMERSPACE_VERIFY_SSL=false
HAMMERSPACE_TIMEOUT=30

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/mcp_1_5.log

# Development Configuration
DEBUG=false
TEST_MODE=false
EOF
    echo -e "${YELLOW}⚠️  Please edit $INSTALL_DIR/.env with your actual credentials${NC}"
fi

# Create logs directory
mkdir -p logs

# Set permissions
chmod +x start_server.sh
chmod +x stop_server.sh
chmod +x install.sh

# Reload systemd
sudo systemctl daemon-reload

echo -e "${GREEN}✅ Installation completed successfully!${NC}"
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "${BLUE}  1. Edit $INSTALL_DIR/.env with your credentials${NC}"
echo -e "${BLUE}  2. Start the service: sudo systemctl start mcp-1.5${NC}"
echo -e "${BLUE}  3. Enable auto-start: sudo systemctl enable mcp-1.5${NC}"
echo -e "${BLUE}  4. Check status: sudo systemctl status mcp-1.5${NC}"
echo -e "${BLUE}  5. View logs: journalctl -u mcp-1.5 -f${NC}"
echo -e "${BLUE}  6. Test endpoint: curl http://localhost:9901/health${NC}"
echo -e "${GREEN}🎉 MCP 1.5 Server is ready!${NC}"
