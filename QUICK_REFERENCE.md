# MCP 1.5 Quick Reference Guide

This guide provides quick access to the most commonly used commands and operations in the MCP 1.5 system.

## 🚀 Quick Start

```bash
# Start all services
./start_all_services.sh start

# Check status
./start_all_services.sh status

# Access Web UI
open http://localhost:5000
```

## 📋 Service Management Commands

### Basic Operations
```bash
./start_all_services.sh start      # Start all services
./start_all_services.sh stop       # Stop all services
./start_all_services.sh restart    # Restart all services
./start_all_services.sh status     # Show service status
```

### Logs and Debugging
```bash
./start_all_services.sh logs web-ui        # Web UI logs
./start_all_services.sh logs file-monitor  # File monitor logs
./start_all_services.sh logs hammerspace-mcp # Hammerspace MCP logs
./start_all_services.sh logs milvus-mcp     # Milvus MCP logs
```

### Screen Sessions
```bash
./start_all_services.sh attach web-ui      # Attach to Web UI
./start_all_services.sh attach file-monitor # Attach to File Monitor
screen -list                                # List all sessions
screen -r web-ui                           # Attach to web-ui session
```

### Maintenance
```bash
./start_all_services.sh cleanup            # Clean up old logs
./start_all_services.sh install-service   # Install systemd service
./start_all_services.sh remove-service    # Remove systemd service
```

## 🌐 Service URLs

- **Web UI**: http://localhost:5000
- **Web UI (LAN)**: http://10.0.0.236:5000
- **Milvus MCP**: http://localhost:9902/sse
- **Kubernetes MCP**: http://localhost:9903/sse (not implemented)

## 📁 File Operations

### Supported File Types
- **Documents**: PDF, DOCX, PPTX, TXT, MD, HTML, JSON
- **Images**: JPEG, PNG, BMP, TIFF
- **Audio**: MP3
- **Scripts**: SH

### File Monitoring
- **Polling Interval**: 5 seconds (fast), 30 seconds (retroactive)
- **Watch Path**: `/mnt/anvil/hub/`
- **Auto-tagging**: MD5 hash, MIME type, embedding tag
- **Tier Management**: Automatic tier0 promotion/demotion

## 🔧 Natural Language Commands

### File Tagging
```
Tag all files in /mnt/anvil/hub/my-folder as modelsetid=my-demo
Tag all PDF files in /mnt/anvil/hub/ as project=gtc-2025
Tag the entire /mnt/anvil/hub/documents folder recursively
```

### Tier Management
```
Promote all modelsetid=my-demo tagged files to tier0
Remove the Place-on-tier0 objective from /mnt/anvil/hub/my-folder
Check alignment status of files tagged with modelsetid=my-demo
List all objectives for /mnt/anvil/hub/my-folder
```

### System Operations
```
Refresh Hammerspace mounts
Start the file monitor daemon
Check file monitor status
View recent file ingestion events
Stop the file monitor
```

## 📊 Monitoring Commands

### Web UI Endpoints
```bash
# Service status
curl http://localhost:5000/api/monitor/status

# Recent events
curl http://localhost:5000/api/monitor/events

# Event streaming
curl http://localhost:5000/api/monitor/events/stream

# Debug logs
curl http://localhost:5000/api/logs/stream
```

### Event Filtering
```bash
# Filter by event type
curl "http://localhost:5000/api/monitor/events?event_type=NEW_FILE"

# Filter by file pattern
curl "http://localhost:5000/api/monitor/events?file_pattern=.pdf"

# Filter by timestamp
curl "http://localhost:5000/api/monitor/events?since=2025-10-23T14:00:00Z"
```

## 🐛 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check port conflicts
./start_all_services.sh status

# Kill conflicting processes
sudo lsof -ti:5000 | xargs kill -9

# Restart services
./start_all_services.sh restart
```

#### File Monitor Issues
```bash
# Check if monitor is running
ps aux | grep file_monitor_daemon

# View monitor logs
./start_all_services.sh logs file-monitor

# Attach to monitor session
./start_all_services.sh attach file-monitor
```

#### NFS Mount Issues
```bash
# Check mounts
mount | grep anvil

# Refresh mounts
./refresh_mounts.sh

# Or via Web UI
"Refresh Hammerspace mounts"
```

#### Unicode Errors
```bash
# Check log encoding
file logs/web_ui.log

# The system now handles Unicode automatically
# No manual intervention required
```

### Service Health Checks

#### Web UI
```bash
curl http://localhost:5000/api/monitor/status
```

#### Milvus MCP
```bash
curl http://localhost:9902/health
```

#### File Monitor
```bash
./start_all_services.sh logs file-monitor | tail -20
```

## 📝 Log Files

### Log Locations
- **Web UI**: `logs/web_ui.log`
- **File Monitor**: `logs/file_monitor_daemon.log`
- **Hammerspace MCP**: `logs/hammerspace_mcp.log`
- **Milvus MCP**: `logs/milvus_mcp.log`
- **Kubernetes MCP**: `logs/kubernetes_mcp.log`

### Log Monitoring
```bash
# Real-time log viewing
tail -f logs/web_ui.log
tail -f logs/file_monitor_daemon.log

# Search logs
grep "ERROR" logs/*.log
grep "NEW_FILE" logs/file_monitor_daemon.log
```

## 🔄 Event Types

### File Events
- `NEW_FILE` - New file detected
- `FOLDER_INGEST_SUCCESS` - Folder processed successfully
- `FOLDER_INGEST_FAILURE` - Folder processing failed

### Tier Events
- `TIER0_PROMOTION_BY_TAG` - Files promoted to tier0
- `TIER0_DEMOTION_BY_TAG` - Files demoted from tier0
- `TIER0_PROMOTION` - Individual file tier0 promotion
- `TIER0_DEMOTION` - Individual file tier0 demotion

### Milvus Events
- `MILVUS_CONFIRMATION` - File confirmed in Milvus
- `MILVUS_CONFIRMATION_FAILURE` - Milvus confirmation failed

## 🎯 Performance Tips

### File Processing
- **Recursive Tagging**: Use folder-level tagging for 40x speedup
- **Batch Processing**: Files are processed in 15-second batches
- **Multi-format Support**: All supported types processed together

### Service Management
- **Screen Sessions**: Services persist across SSH disconnections
- **Auto-restart**: Services restart automatically if they crash
- **Systemd Integration**: Optional auto-start on boot

### Monitoring
- **Event Filtering**: Use specific filters to reduce noise
- **Log Rotation**: Automatic cleanup of old logs
- **Health Checks**: Regular service health monitoring

## 📚 Additional Resources

### Documentation
- [README.md](README.md) - Complete system documentation
- [SERVICE_MANAGEMENT.md](SERVICE_MANAGEMENT.md) - Service management guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API reference

### Guides
- [Integration Guide](docs/INTEGRATION_GUIDE.md) - Connect to Cursor, Windsurf
- [Tag Search Guide](docs/TAG_SEARCH_GUIDE.md) - Advanced tag operations
- [Tier Management Guide](docs/TIER_MANAGEMENT_GUIDE.md) - Tier operations
- [Testing Guide](web_ui/TESTING_GUIDE.md) - Web UI testing

### Support
- **GitHub Issues**: [Repository Issues](https://github.com/mbloomhammerspace/mcp-1.5/issues)
- **Documentation**: Check the `docs/` folder
- **Troubleshooting**: Review the troubleshooting section above

---

**MCP 1.5 Quick Reference** - Your go-to guide for common operations and troubleshooting.

