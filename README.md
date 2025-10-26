# MCP 1.5 - Advanced Hammerspace Storage Management with AI

A production-ready Model Context Protocol (MCP) server for Hammerspace storage management with natural language interface, automatic file ingestion, and comprehensive monitoring capabilities.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Linux system (Ubuntu 20.04+ recommended)
- Hammerspace storage cluster (HSTK CLI installed)
- Anthropic API key (for natural language UI)
- NVIDIA API key (optional, for AI features)
- Kubernetes cluster (for automatic file ingestion)
- Milvus vector database (for document embeddings)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mbloomhammerspace/mcp-1.5.git
   cd mcp-1.5
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   Set the following:
   ```bash
   # Hammerspace Configuration
   HS_ANVIL=10.200.120.90
   
   # Anthropic API (for Web UI)
   ANTHROPIC_API_KEY=your_anthropic_key_here
   
   # NVIDIA API (optional)
   NVIDIA_API_KEY=your_nvidia_key_here
   ```

4. **Start all services with one command**:
   ```bash
   ./start_all_services.sh start
   ```
   
   Access Web UI at: `http://localhost:5000`

## 📋 Features

### 🤖 Natural Language Interface
- **Web-based UI** powered by Claude AI at `http://localhost:5000`
- **Direct MCP integration** for all Hammerspace operations
- **Real-time debug log viewer** at `/debug`
- **File ingest monitor dashboard** at `/monitor`
- **Action-oriented responses** - executes commands, reports results

### 📁 Advanced File Ingestion System
- **Multi-format support** - BMP, DOCX, HTML, JPEG, JSON, MD, PDF, PNG, PPTX, SH, TIFF, TXT, MP3
- **Real-time file monitoring** - Polling-based detection on NFS 4.2 mounts
- **Folder-based processing** - New folders trigger batch processing of all supported files
- **Kubernetes job deployment** - Automatic file ingestion jobs with ConfigMaps
- **Milvus vector database integration** - Automatic embedding generation and storage
- **Intelligent collection naming** - Collections named after folders or sequential numbering
- **Tag-based tier management** - Automatic tier0 promotion for embedding files
- **Event streaming** - Real-time monitoring of ingestion pipeline

### 📊 Comprehensive Monitoring UI
- **Real-time event streaming** - Watch files being ingested live
- **Event filtering** - Filter by event type, file pattern, or timestamp
- **Toast notifications** - Get notified when new files arrive
- **Status dashboard** - Monitor service health, file counts, CPU usage
- **Interactive UI** - Beautiful, modern interface for tracking ingestion pipelines
- **Multi-service monitoring** - Track all MCP servers and services

### 🔧 Persistent Service Management
- **Unified startup script** - Start all services with one command
- **Screen session persistence** - Services survive SSH disconnections
- **Auto-restart capability** - Services automatically restart if they crash
- **Systemd integration** - Optional auto-start on boot
- **Comprehensive logging** - Detailed logs for all services
- **Health monitoring** - Real-time service status and port monitoring

### API Endpoints
- **`/api/monitor/status`** - Get monitor service status
- **`/api/monitor/events`** - Query ingestion events with filters
- **`/api/monitor/events/stream`** - Server-Sent Events for real-time updates
- **`/api/chat`** - Natural language chat interface
- **`/api/tools`** - List available MCP tools
- **`/api/logs/stream`** - Stream debug logs in real-time

### Core MCP Tools
All tools use **real HSTK CLI commands** (no mock data):

- **`tag_directory_recursive`** - Tag files and directories recursively
- **`check_tagged_files_alignment`** - Check if tagged files are aligned to their objectives
- **`apply_objective_to_path`** - Apply Hammerspace objectives (e.g., "Place-on-tier0", "placeonvolumes")
- **`remove_objective_from_path`** - Remove objectives from paths
- **`list_objectives_for_path`** - List all objectives applied to a path
- **`ingest_new_files`** - Find new files by ctime/mtime, tag them, and place on Tier 1
- **`refresh_mounts`** - Refresh NFS mounts to resolve stale file handles

### Advanced Features
- **Automatic file monitoring** - Polling service that auto-tags new files with MD5 hash and MIME type
- **Automatic stale file handle recovery** - Detects and automatically refreshes mounts
- **Share-relative path support** - Use `/modelstore/dir` instead of `/mnt/se-lab/modelstore/dir`
- **Multi-tier support** - Tier 0 (high-performance) and Tier 1 (default storage)
- **Tag-based workflows** - Tag files and manage them as collections
- **Intelligent batching** - Groups file events (15 sec) or processes immediately if traffic is light

## 🆕 Advanced File Ingestion Workflow

### How It Works

1. **File Detection**: The file monitor polls NFS mounts every 5 seconds for new files
2. **Tagging**: New files are automatically tagged with:
   - `user.ingestid=<md5hash>` - MD5 hash for deduplication
   - `user.mimeid=<mimetype>` - MIME type for classification
   - `user.embedding` - Tag for files requiring embedding
3. **Multi-format Processing**: All supported file types trigger Kubernetes ingestion jobs
4. **Collection Management**: Files are organized into Milvus collections:
   - **Folder-based**: Collections named after folder (e.g., `cold_0011`)
   - **Sequential**: Collections named `intel_1`, `intel_2`, etc.
5. **Tier Management**: Files tagged for embedding are automatically promoted to tier0
6. **Embedding Generation**: Files are processed into vector embeddings
7. **Storage**: Embeddings stored in Milvus for semantic search
8. **Tier Demotion**: After embedding, files are moved back to default tier

### Folder Processing

When a new folder is detected:
- All supported files in the folder are processed as a batch
- A single Milvus collection is created named after the folder
- Collection names are sanitized (e.g., `cold-0011` → `cold_0011`)
- All files in the folder are uploaded to the same collection
- Files are tagged with `embedding` and promoted to tier0 for processing
- After embedding, tier0 objective is removed

### Configuration

The file monitor supports:
- **Polling intervals**: 5 seconds (fast) during business hours, 30 seconds during retroactive hours
- **Retroactive tagging**: Configurable time windows (default: disabled for testing)
- **Path monitoring**: Monitors `/mnt/anvil/hub/` by default
- **File filtering**: Processes all supported file types (BMP, DOCX, HTML, JPEG, JSON, MD, PDF, PNG, PPTX, SH, TIFF, TXT, MP3)
- **Recursive folder tagging**: Tags entire folder hierarchies for 40x performance improvement

### Kubernetes Integration

- **Job Templates**: Uses `k8s-templates/ingest.yaml` for PDF processing
- **ConfigMaps**: File lists passed to jobs via Kubernetes ConfigMaps
- **PVC Integration**: Uses `hammerspace-hub-pvc` for persistent storage
- **Path Mapping**: Container paths mapped from `/mnt/anvil/hub/` to `/data/`

## 🎯 Usage

### Example Commands (Web UI)

Try these in the natural language interface:

```
Tag all files in /modelstore/nvidia-test-thurs as modelsetid=my-demo
Promote all modelsetid=my-demo tagged files to tier0
Check alignment status of files tagged with modelsetid=my-demo
Remove the Place-on-tier0 objective from /modelstore/nvidia-test-thurs
List all objectives for /modelstore/incoming-models
Refresh Hammerspace mounts
```

### 🆕 File Ingestion Commands

```
Start the file monitor daemon
Check file monitor status
View recent file ingestion events
Stop the file monitor
```

### Direct MCP Server Usage

Add to your MCP client configuration (e.g., Cursor IDE):

```json
{
  "mcpServers": {
    "hammerspace": {
      "command": "python",
      "args": ["/home/mike/mcp-1.5/src/aiq_hstk_mcp_server.py"],
      "env": {
        "PYTHONPATH": "/home/mike/mcp-1.5"
      }
    }
  }
}
```

### Available MCP Tools

#### Tag Management
- **`tag_directory_recursive`** - Recursively tag all files in a directory
  ```json
  {
    "path": "/mnt/se-lab/modelstore/my-models",
    "tag_name": "user.modelsetid",
    "tag_value": "my-tag-value"
  }
  ```

- **`check_tagged_files_alignment`** - Find and check alignment of tagged files
  ```json
  {
    "tag_name": "user.modelsetid",
    "tag_value": "my-tag-value",
    "share_path": "/mnt/se-lab/modelstore/"
  }
  ```

#### Tier Management
- **`apply_objective_to_path`** - Apply objectives like tier promotion
  ```json
  {
    "objective_name": "Place-on-tier0",
    "path": "/mnt/se-lab/modelstore/my-models"
  }
  ```

- **`remove_objective_from_path`** - Remove objectives
  ```json
  {
    "objective_name": "Place-on-tier0",
    "path": "/mnt/se-lab/modelstore/my-models"
  }
  ```

#### File Ingestion
- **`ingest_new_files`** - Find new files, tag them, and place on Tier 1
  ```json
  {
    "path": "/mnt/se-lab/modelstore/",
    "tag_name": "user.modelsetid",
    "tag_value": "new-batch",
    "age_minutes": 60
  }
  ```

#### System Utilities
- **`refresh_mounts`** - Refresh NFS mounts to resolve stale file handles
  ```json
  {
    "mount_type": "all"
  }
  ```

#### File Monitoring & Ingestion
- **`start_inotify_monitor`** - Start automated file monitoring service
  ```json
  {}
  ```
  
  Monitors all Hammerspace shares, automatically tags new files with:
  - `user.ingestid=<md5hash>` - MD5 hash for deduplication
  - `user.mimeid=<mimetype>` - MIME type for classification
  
  Events are batched every 15 seconds or processed immediately if traffic is light.

- **`get_file_monitor_status`** - Get monitor status
  ```json
  {}
  ```
  
  Returns: running state, watched paths, pending events, files tagged, CPU usage

- **`get_file_ingest_events`** - Query file ingest/tagging events
  ```json
  {
    "limit": 100,
    "event_type": "NEW_FILE",
    "file_pattern": ".pdf",
    "since_timestamp": "2025-10-09T20:00:00"
  }
  ```
  
  Returns recent file ingestion events with full metadata including:
  - Event type (NEW_FILE or RETROACTIVE_TAG)
  - File path and name
  - MD5 hash (ingestid)
  - MIME type (mimeid)
  - File size and timestamp
  
  **Use Cases:**
  - Track which files have been ingested
  - Build automated workflows based on file events
  - Monitor ingestion pipelines
  - Audit file processing

- **`stop_inotify_monitor`** - Stop monitoring service
  ```json
  {}
  ```

- **`list_objectives_for_path`** - List all objectives for a path
  ```json
  {
    "path": "/mnt/se-lab/modelstore/my-models"
  }
  ```

## 🔧 Architecture

### Components

1. **MCP Server** (`src/aiq_hstk_mcp_server.py`)
   - Implements MCP protocol
   - Executes Hammerspace HSTK CLI commands
   - Handles automatic retry on stale file handles
   - Uses real HSTK operations (no mock data)

2. **Web UI** (`web_ui/app.py`)
   - Flask-based natural language interface
   - Anthropic Claude integration for NL understanding
   - MCP client for tool execution
   - Real-time debug log streaming

3. **🆕 File Monitor** (`src/file_monitor.py`)
   - Polling-based file detection for NFS 4.2 mounts
   - Automatic tagging with MD5 and MIME type
   - Folder-based batch processing
   - Kubernetes job deployment for PDF ingestion
   - Milvus collection management

4. **🆕 File Monitor Daemon** (`src/file_monitor_daemon.py`)
   - Standalone daemon for running file monitor
   - Background service for continuous monitoring
   - Logging and error handling

5. **Mount Refresh Script** (`refresh_mounts.sh`)
   - Unmounts and remounts Hammerspace NFS shares
   - Resolves stale file handle errors
   - Supports selective mount refresh

### Data Flow

```
User Input (NL) → Claude AI → MCP Tool Selection → HSTK CLI → Hammerspace
                     ↓
                 MCP Server
                     ↓
              Real Operations
```

### 🆕 File Ingestion Data Flow

```
New File/Folder → File Monitor → Tagging → Kubernetes Job → PDF Processing → Milvus Collection
                     ↓
                 Event Logging → Web UI Dashboard → Real-time Monitoring
```

## 🧪 Testing

### Web UI Tests

```bash
cd tests
./test_web_ui_curl.sh
python test_web_ui.py
```

### Single Command Test

```bash
cd tests
./test_single_question.sh "Tag all files in /modelstore/test as modelsetid=test123"
```

### 🆕 File Ingestion Tests

```bash
# Start file monitor daemon
python3 src/file_monitor_daemon.py

# Check monitor status
curl http://localhost:5000/api/monitor/status

# View ingestion events
curl http://localhost:5000/api/monitor/events

# Test with new files
cp test.pdf /mnt/anvil/hub/
```

## 🛠️ Service Management

### Unified Service Management

```bash
# Start all services with one command
./start_all_services.sh start

# Check service status
./start_all_services.sh status

# Stop all services
./start_all_services.sh stop

# Restart all services
./start_all_services.sh restart
```

### Individual Service Management

```bash
# View logs for specific services
./start_all_services.sh logs web-ui
./start_all_services.sh logs file-monitor
./start_all_services.sh logs hammerspace-mcp
./start_all_services.sh logs milvus-mcp

# Attach to service screen sessions
./start_all_services.sh attach web-ui
./start_all_services.sh attach file-monitor

# Clean up old logs
./start_all_services.sh cleanup
```

### Service URLs

Once started, services are available at:
- **Web UI**: http://localhost:5000
- **Web UI (LAN)**: http://10.0.0.236:5000
- **Hammerspace MCP**: stdio-based (no HTTP endpoint)
- **Milvus MCP**: http://localhost:9902/sse (if Milvus is running)
- **Kubernetes MCP**: http://localhost:9903/sse (not implemented)

### View Logs

```bash
# Web UI logs
tail -f logs/web_ui.log

# MCP Server logs
tail -f logs/aiq_hstk_mcp.log

# File monitor logs
tail -f logs/retroactive_fully_disabled.log

# Real-time streaming (in browser)
# Visit http://localhost:5000/debug
```

## 🐛 Troubleshooting

### Stale File Handle Errors

The MCP server automatically detects and retries operations when stale file handles occur. If issues persist:

```bash
# Manual mount refresh
./refresh_mounts.sh

# Or via Web UI
"Refresh Hammerspace mounts"
```

### Tag Operations Not Working

1. Ensure you're targeting a mounted directory
2. Verify the HSTK CLI is accessible: `/home/mike/hs-mcp-1.0/.venv/bin/hs --version`
3. Check mounts: `mount | grep hammerspace`

### 🆕 File Ingestion Issues

1. **Files not detected**: Check if file monitor is running
   ```bash
   ps aux | grep file_monitor_daemon
   ```

2. **Kubernetes jobs failing**: Check pod status
   ```bash
   kubectl get pods -l app=pdf-ingest
   kubectl logs -l app=pdf-ingest
   ```

3. **Empty Milvus collections**: Check ingest service logs
   ```bash
   kubectl logs -l app=ingestor-server
   ```

4. **NFS mount issues**: Verify mount points
   ```bash
   mount | grep anvil
   ls -la /mnt/anvil/hub/
   ```

### Common Tag Formats

Tags in Hammerspace use the format: `namespace.key=value`

Examples:
- `user.modelsetid=my-demo`
- `user.project=gtc-2025`
- `user.tier=critical`

## 📚 Documentation

### **🚀 Quick Start**
- **[Quick Reference Guide](QUICK_REFERENCE.md)** - Your go-to guide for common operations
- **[Service Management](SERVICE_MANAGEMENT.md)** - Complete service management guide

### **🏗️ Architecture & API**
- **[Architecture Documentation](ARCHITECTURE.md)** - Comprehensive system architecture
- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference for all MCP servers

### **🔗 Integration Guides**
- **[Integration Guide](docs/INTEGRATION_GUIDE.md)** - Connect to Cursor, Windsurf, NVIDIA Playground

### **📖 Feature Guides**
- [Complete Feature Documentation](docs/VOLUME_CANVAS_FEATURES.md)
- [Tag Search Guide](docs/TAG_SEARCH_GUIDE.md)
- [Tier Management Guide](docs/TIER_MANAGEMENT_GUIDE.md)
- [Tag to Objectives Workflow](docs/TAG_TO_OBJECTIVES_GUIDE.md)
- [Guides Index](docs/GUIDES_INDEX.md)

### **🧪 Testing Guides**
- [Web UI Testing Guide](web_ui/TESTING_GUIDE.md)

## 🔒 Production Deployment

### Security Considerations

- Run the Web UI behind a reverse proxy (nginx, Apache)
- Use HTTPS for production deployments
- Restrict access with authentication
- Review and limit MCP tool permissions

### Performance Tuning

- Adjust `max_files_to_check` for large filesystems (default: 500)
- Use specific `share_path` parameters to limit search scope
- Monitor log files for performance issues

## 📞 Support

For support and questions:
- Create an issue in the [GitHub repository](https://github.com/mbloomhammerspace/mcp-1.5)
- Check the documentation in the `docs/` folder
- Review the troubleshooting section above

## 🎉 Recent Updates

### 🆕 October 23, 2025 - Advanced Service Management + Multi-Format Support
- ✅ **NEW**: Unified service management script (`start_all_services.sh`) for all MCP services
- ✅ **NEW**: Screen session persistence - services survive SSH disconnections
- ✅ **NEW**: Auto-restart capability for crashed services
- ✅ **NEW**: Systemd integration for auto-start on boot
- ✅ **NEW**: Multi-format file support (BMP, DOCX, HTML, JPEG, JSON, MD, PDF, PNG, PPTX, SH, TIFF, TXT, MP3)
- ✅ **NEW**: Tag-based tier management with automatic tier0 promotion/demotion
- ✅ **NEW**: Recursive folder tagging for 40x performance improvement
- ✅ **NEW**: Enhanced event filtering and monitoring UI
- ✅ **NEW**: Comprehensive health monitoring and port conflict resolution
- ✅ **FIXED**: Unicode handling in logs and CLI output
- ✅ **FIXED**: NFS timing issues with retry mechanisms
- ✅ **FIXED**: Hammerspace CLI tag operations with fallback methods
- ✅ **FIXED**: Individual file vs folder-level tagging optimization

### 🆕 October 16, 2025 - Automatic File Ingestion + Kubernetes + MCP
- ✅ **NEW**: Complete automatic file ingestion system with Kubernetes integration
- ✅ **NEW**: Polling-based file monitoring for NFS 4.2 mounts (inotify not supported)
- ✅ **NEW**: Folder-based batch processing - new folders trigger collection creation
- ✅ **NEW**: Milvus vector database integration for PDF embeddings
- ✅ **NEW**: Kubernetes job deployment with ConfigMaps for file processing
- ✅ **NEW**: Intelligent collection naming (folder-based and sequential)
- ✅ **NEW**: Real-time event streaming and monitoring dashboard
- ✅ **NEW**: Standalone file monitor daemon for continuous operation
- ✅ **FIXED**: NFS compatibility issues with polling-only approach
- ✅ **FIXED**: Kubernetes PVC integration and path mapping
- ✅ **FIXED**: Milvus collection naming conventions (underscores vs hyphens)
- ✅ **FIXED**: File path handling in container environments
- ✅ **FIXED**: Job completion tracking and error handling
- ✅ **FIXED**: Retroactive tagging time window configuration
- ✅ **FIXED**: Threading and async operation coordination

### October 9, 2025 - File Ingestion Event System & Monitoring UI
- ✅ **NEW**: Agentic event consumption via `get_file_ingest_events` MCP tool
- ✅ **NEW**: Real-time monitoring dashboard at `/monitor` with live event streaming
- ✅ **NEW**: API endpoints for event querying and monitoring
- ✅ **FIXED**: Duplicate file processing - files now tagged exactly once
- ✅ **FIXED**: In-memory tracking prevents repeated tagging of same files
- ✅ Deduplication verification tools: `check_duplicates.sh` and `find-dup.sh`
- ✅ Full event metadata: timestamp, file path, MD5 hash, MIME type, file size
- ✅ Event filtering: by type, file pattern, or timestamp
- ✅ Toast notifications for new file arrivals
- ✅ Automated file monitoring service with MD5/MIME tagging

### Previous Updates
- ✅ Added automatic mount refresh on stale file handle errors
- ✅ Suppressed Anthropic API deprecation warnings in logs
- ✅ Added copy buttons to all chat messages
- ✅ Fixed PARTIALLY ALIGNED status detection
- ✅ Web-based natural language console with Claude AI

---

**MCP 1.5** - Production-ready Hammerspace storage management with natural language interface and automatic file ingestion.
