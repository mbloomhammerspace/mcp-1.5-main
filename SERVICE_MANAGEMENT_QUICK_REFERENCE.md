# Hammerspace MCP Services Management

## Quick Commands

```bash
# Start all services
./manage_hammerspace_services.sh start
# or
hs-services start

# Stop all services  
./manage_hammerspace_services.sh stop
# or
hs-services stop

# Restart all services
./manage_hammerspace_services.sh restart
# or
hs-services restart

# Check status
./manage_hammerspace_services.sh status
# or
hs-services status

# View logs
./manage_hammerspace_services.sh logs webui    # Web UI logs
./manage_hammerspace_services.sh logs mcp      # MCP Server logs
./manage_hammerspace_services.sh logs all      # All logs

# Clean up old logs
./manage_hammerspace_services.sh cleanup
```

## Service URLs

- **Web UI**: http://localhost:5000
- **Web UI (LAN)**: http://10.0.0.236:5000

## What the Script Manages

1. **MCP Server** (`src/aiq_hstk_mcp_server.py`)
   - Core Hammerspace MCP functionality
   - File monitoring and auto-tagging
   - HSTK CLI integration

2. **Web UI** (`web_ui/app.py`)
   - Flask web interface
   - Chat interface with Claude
   - Debug console and logs

## Key Benefits

- ✅ **No systemd restrictions** - Runs with full user permissions
- ✅ **HSTK CLI works properly** - No read-only filesystem errors
- ✅ **Single command management** - Start/stop/restart everything
- ✅ **Automatic dependency checking** - Verifies all components
- ✅ **Process monitoring** - Tracks PIDs and status
- ✅ **Log management** - Centralized logging and cleanup
- ✅ **Graceful shutdown** - Proper process termination

## Troubleshooting

If services fail to start:

1. **Check dependencies**:
   ```bash
   ./manage_hammerspace_services.sh status
   ```

2. **View logs**:
   ```bash
   ./manage_hammerspace_services.sh logs all
   ```

3. **Restart services**:
   ```bash
   ./manage_hammerspace_services.sh restart
   ```

4. **Check mount status**:
   ```bash
   mount | grep anvil
   ```

## File Locations

- **Script**: `/home/ubuntu/mcp-1.5-main/manage_hammerspace_services.sh`
- **PIDs**: `/home/ubuntu/mcp-1.5-main/pids/`
- **Logs**: `/home/ubuntu/mcp-1.5-main/logs/`
- **MCP Server**: `/home/ubuntu/mcp-1.5-main/src/aiq_hstk_mcp_server.py`
- **Web UI**: `/home/ubuntu/mcp-1.5-main/web_ui/app.py`

## Auto-start (Optional)

To start services automatically on boot, add to crontab:

```bash
crontab -e
# Add this line:
@reboot /home/ubuntu/mcp-1.5-main/manage_hammerspace_services.sh start
```

