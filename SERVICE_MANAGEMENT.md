# MCP Services Management

This document describes how to manage all MCP services using the unified startup script with enhanced persistence, auto-restart, and systemd integration.

## Quick Start

```bash
# Start all services with enhanced persistence
./start_all_services.sh start

# Check comprehensive service status
./start_all_services.sh status

# Stop all services gracefully
./start_all_services.sh stop

# Restart all services
./start_all_services.sh restart

# Install systemd service for auto-start on boot
./start_all_services.sh install-service
```

## Services

The startup script manages the following services with enhanced persistence and auto-restart capabilities:

### Core Services (Always Started)
- **File Monitor Daemon** - Monitors NFS mounts for new files and triggers ingestion
  - Multi-format support (BMP, DOCX, HTML, JPEG, JSON, MD, PDF, PNG, PPTX, SH, TIFF, TXT, MP3)
  - Tag-based tier management with automatic tier0 promotion/demotion
  - Recursive folder tagging for 40x performance improvement
- **Web UI Server** - Flask web interface for monitoring and control
  - Real-time event streaming and monitoring dashboard
  - Enhanced event filtering and multi-service monitoring
- **Hammerspace MCP Server** - MCP server for Hammerspace operations (stdio-based)
  - Enhanced Unicode handling and error recovery
  - Improved tag operations with fallback methods

### Optional Services (Started if Available)
- **Milvus MCP Server** - MCP server for Milvus vector database operations
  - Requires Milvus database to be running
  - Graceful handling of connection failures
- **Kubernetes MCP Server** - MCP server for Kubernetes operations (not yet implemented)
  - Logs as "optional service failed to start (this is OK if not needed)"

## Screen Sessions

All services run in persistent screen sessions that survive logouts:

- `file-monitor` - File Monitor Daemon
- `web-ui` - Web UI Server  
- `hs-mcp` - Hammerspace MCP Server
- `milvus-mcp` - Milvus MCP Server
- `k8s-mcp` - Kubernetes MCP Server

## Commands

### Basic Operations
```bash
./start_all_services.sh start     # Start all services
./start_all_services.sh stop      # Stop all services
./start_all_services.sh restart   # Restart all services
./start_all_services.sh status    # Show service status
```

### Logs and Debugging
```bash
./start_all_services.sh logs web-ui        # Show Web UI logs
./start_all_services.sh logs file-monitor  # Show File Monitor logs
./start_all_services.sh logs hammerspace-mcp # Show Hammerspace MCP logs
./start_all_services.sh logs milvus-mcp    # Show Milvus MCP logs
```

### Screen Session Management
```bash
./start_all_services.sh attach web-ui      # Attach to Web UI screen session
./start_all_services.sh attach file-monitor # Attach to File Monitor screen session

# Manual screen commands
screen -list                    # List all screen sessions
screen -r web-ui               # Attach to web-ui session
screen -r file-monitor         # Attach to file-monitor session
```

### Maintenance
```bash
./start_all_services.sh cleanup  # Clean up old log entries
```

### Systemd Integration
```bash
# Install systemd service for auto-start on boot
./start_all_services.sh install-service

# Remove systemd service
./start_all_services.sh remove-service

# Check systemd service status
sudo systemctl status mcp-services
```

## Service URLs

Once started, services are available at:

- **Web UI**: http://localhost:5000
- **Web UI (LAN)**: http://10.0.0.236:5000
- **Hammerspace MCP**: stdio-based (no HTTP endpoint)
- **Milvus MCP**: http://localhost:9902/sse (if Milvus is running)
- **Kubernetes MCP**: http://localhost:9903/sse (not implemented)

## Log Files

All services write logs to `/home/ubuntu/mcp-1.5-main/logs/`:

- `web_ui.log` - Web UI server logs
- `file_monitor_daemon.log` - File monitor logs
- `hammerspace_mcp.log` - Hammerspace MCP server logs
- `milvus_mcp.log` - Milvus MCP server logs
- `kubernetes_mcp.log` - Kubernetes MCP server logs

## Troubleshooting

### Port Conflicts
The script automatically kills processes using required ports before starting services.

### Service Failures
- Check logs: `./start_all_services.sh logs <service-name>`
- Attach to screen session: `./start_all_services.sh attach <service-name>`
- Check status: `./start_all_services.sh status`

### Screen Sessions
- List sessions: `screen -list`
- Attach to session: `screen -r <session-name>`
- Detach from session: `Ctrl+A` then `D`

### Dependencies
- **Screen**: Required for persistent sessions (auto-installed if missing)
- **Python 3**: Required for all services
- **Hammerspace CLI**: Required for file operations
- **Milvus**: Required for Milvus MCP server (optional)

## Enhanced Persistence Features

### Auto-Restart Capability
All services include robust auto-restart functionality:
- **Crash Detection**: Services automatically detect when they crash
- **Restart Logic**: Services restart automatically after a 5-second delay
- **Clean Exit Handling**: Services that exit cleanly (code 0) are not restarted
- **Logging**: All restart events are logged with timestamps

### Screen Session Persistence
All services run in screen sessions that persist across:
- SSH disconnections
- Terminal closures
- User logouts
- System reboots (if screen sessions are configured to survive reboots)

### Systemd Integration
For production deployments, you can install a systemd service:
```bash
# Install systemd service for auto-start on boot
./start_all_services.sh install-service

# This creates /etc/systemd/system/mcp-services.service
# Services will start automatically on boot
# Services will restart if they fail
```

### Alternative Persistence Methods
If you prefer not to use systemd:
1. Add to crontab: `@reboot /home/ubuntu/mcp-1.5-main/start_all_services.sh start`
2. Add to shell profile (`.bashrc`, `.profile`)
3. Use `nohup` with the startup script

## Examples

```bash
# Start everything
./start_all_services.sh start

# Check what's running
./start_all_services.sh status

# View Web UI logs
./start_all_services.sh logs web-ui

# Attach to file monitor to see real-time activity
./start_all_services.sh attach file-monitor

# Restart after making changes
./start_all_services.sh restart

# Stop everything
./start_all_services.sh stop
```
