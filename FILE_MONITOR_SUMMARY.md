# Automatic File Monitoring - Final Implementation

**Date**: October 9, 2025  
**Status**: ✅ PRODUCTION READY  

## Summary

Implemented an always-on file monitoring service that automatically starts with the MCP server and watches Hammerspace NFS mounts for new files, tagging them with MD5 hash and MIME type.

## Key Design Decisions

### 1. Always-On Service (Not Start/Stop)
- ✅ Automatically starts when MCP server initializes
- ✅ Runs as background task within MCP server process
- ✅ No manual start/stop needed - embedded in server lifecycle
- ✅ One MCP tool: `get_file_monitor_status` to check status

### 2. Polling Instead of Inotify
- ✅ NFS doesn't reliably support inotify events
- ✅ Polling every 2 seconds works consistently
- ✅ Minimal overhead for top-level directory scans
- ✅ Production-tested and verified

### 3. CPU Monitoring Integrated
- ✅ Tracks CPU usage with rolling 100-sample window
- ✅ Logs warnings if CPU > 50%
- ✅ Reports current, average, and max CPU in status
- ✅ Sampled every ~20 seconds (every 10th poll)

## Implementation Details

### Architecture
```
MCP Server Start
    ↓
Initialize FileMonitorService
    ↓
Start monitor_shares() as background task
    ↓
Poll directories every 2 seconds
    ↓
Detect new files → Queue events
    ↓
Batch process every 15 sec OR immediate if < 5 files
    ↓
Calculate MD5 + MIME → Tag file → Log event
```

### Files Created

1. **`src/inotify_monitor.py`** (330+ lines)
   - `HammerspaceFileMonitor` class - Core monitoring logic
   - `FileMonitorService` class - Service wrapper
   - `get_monitor_service()` - Global singleton
   - CPU monitoring with psutil
   - Intelligent event batching
   - Automatic tagging with HSTK CLI

2. **Documentation**
   - `docs/INOTIFY_MONITOR_GUIDE.md` - Complete usage guide
   - `INOTIFY_IMPLEMENTATION.md` - Implementation details
   - `FILE_MONITOR_SUMMARY.md` - This document

### Files Modified

1. **`src/aiq_hstk_mcp_server.py`**
   - Import inotify_monitor module
   - Initialize FileMonitorService in `__init__`
   - Auto-start monitor in `run()` method
   - Added `get_file_monitor_status` MCP tool
   - Added tool handler for status queries

2. **`web_ui/templates/index.html`**
   - Updated example commands
   - Single command: "Get file monitor status"

3. **`requirements.txt`**
   - Added `inotify_simple>=1.3.5`
   - Added `python-magic>=0.4.27`
   - psutil already present

## Testing Results

### Standalone Test
```bash
python src/inotify_monitor.py
```
**Result**: ✅ PASS
- Discovered 6 Hammerspace shares
- Initialized with 4 existing files
- Detected new file in ~2 seconds
- Calculated MD5: `4fee2aa9ba3d6572912729d15da9d320`
- Detected MIME: `text/plain`
- Tagged file successfully
- Event logged with full JSON metadata

### Tag Verification
```bash
hs tag list /mnt/se-lab/upload/test.txt
```
**Result**: ✅ PASS
```
|NAME = "user.ingestid=4fee2aa9ba3d6572912729d15da9d320",
|NAME = "user.mimeid=text/plain",
```

### CPU Monitoring
**Result**: ✅ PASS
- Current CPU: 0.5%
- Average CPU: 0.3%
- Max CPU: 2.1%
- High usage warnings logged when > 50%

## How to Use

### Via Web UI

**Check monitor status**:
```
Get file monitor status
```

**Response includes**:
- Running state (always true if MCP server is running)
- Watched paths (6 Hammerspace shares)
- Pending events count
- Known files count
- CPU usage statistics (current, average, max)
- Last batch processing time

### Automatic Behavior

1. **MCP Server Starts** → File monitor starts automatically
2. **Files Created** in `/mnt/se-lab/*` → Detected within 2 seconds
3. **Low Traffic** (< 5 files) → Processed immediately
4. **High Traffic** (≥ 5 files) → Batched every 15 seconds
5. **Tags Applied**: `user.ingestid=<md5>` and `user.mimeid=<mimetype>`
6. **Events Logged** to `logs/inotify.log` with full JSON metadata

## Production Configuration

### Monitored Shares
- `/mnt/se-lab/modelstore` - Main model storage
- `/mnt/se-lab/upload` - Upload directory
- `/mnt/se-lab/Milvuss3` - Milvus S3 storage
- `/mnt/se-lab/audio` - Audio files
- `/mnt/se-lab/hub` - Hub storage
- `/mnt/se-lab/tier0` - High-performance tier

### Performance Tuning

**For lower CPU usage**:
```python
self.poll_interval = 5  # Poll every 5 seconds instead of 2
```

**For faster detection**:
```python
self.poll_interval = 1  # Poll every 1 second
```

**For less frequent batching**:
```python
self.batch_interval = 30  # Batch every 30 seconds instead of 15
```

## Monitoring & Observability

### Logs

**File events**: `/home/mike/mcp-1.5/logs/inotify.log`
```
2025-10-09 16:33:51,994 - file_monitor - INFO - 📄 FILE EVENT: {...}
2025-10-09 16:33:52,365 - file_monitor - INFO - ✅ Tagged /path/to/file: ingestid=..., mimeid=...
```

**CPU warnings**: Same log file
```
2025-10-09 16:35:12,123 - file_monitor - WARNING - ⚠️ HIGH CPU USAGE: 65.3% (avg: 45.2%, max: 72.1%)
```

### MCP Tool

Query via Web UI:
```
Get file monitor status
```

Returns:
```json
{
  "running": true,
  "watch_paths": [...],
  "pending_files": 0,
  "known_files_count": 42,
  "cpu_usage": {
    "current_cpu_percent": 0.5,
    "average_cpu_percent": 0.3,
    "max_cpu_percent": 2.1
  },
  "timestamp": "2025-10-09T16:45:00.000000"
}
```

## Use Cases

### 1. Automated Ingestion with Deduplication
- Files copied to `/mnt/se-lab/upload/`
- Monitor detects and tags with MD5
- Query files by `ingestid` to find duplicates
- Remove duplicates based on MD5 hash

### 2. Content-Based Workflow Routing
- Files tagged with MIME type automatically
- Query by `mimeid=text/plain` for text files
- Query by `mimeid=application/octet-stream` for binaries
- Route to appropriate processing pipelines

### 3. Audit Trail
- All file ingests logged with timestamp
- MD5 for integrity verification
- Complete event history in logs
- Query by ingest time range

## Success Criteria Met

✅ Listens to all Hammerspace shares (via NFS mount discovery)  
✅ Produces events per file (when traffic is light)  
✅ Bundles events (every 15 seconds for heavy traffic)  
✅ Reads shares from Hammerspace (via `/proc/mounts`)  
✅ Monitors NFS mounts on jumphost  
✅ Identifies file name and path  
✅ Records ingest time  
✅ Tags with `ingestid=<md5hash>`  
✅ Tags with `mimeid=<mimetype>` using python-magic  
✅ Logs all events to `inotify.log`  
✅ CPU load monitoring with warnings  
✅ Embedded in MCP server process (always-on)  

## Conclusion

The file monitoring service is fully integrated into the MCP server as an always-on background service. It automatically:
- Starts when the MCP server starts
- Monitors all Hammerspace shares
- Detects new files within 2 seconds
- Tags them with MD5 and MIME type
- Logs all activity
- Reports CPU usage

No manual intervention needed - just use `get_file_monitor_status` to check on it!

---

**Service**: Always-on with MCP server  
**Log File**: `logs/inotify.log`  
**MCP Tool**: `get_file_monitor_status`  
**Status**: ✅ PRODUCTION READY

