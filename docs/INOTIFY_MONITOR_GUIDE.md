# Hammerspace File Monitor Guide

## Overview

The Hammerspace File Monitor is an automated service that watches Hammerspace NFS mounts for new files and automatically tags them with ingest metadata.

## Features

- ✅ **Automatic File Detection**: Polls NFS mounts every 2 seconds for new files
- ✅ **Intelligent Batching**: Groups events and processes every 15 seconds OR immediately if traffic is light (< 5 files)
- ✅ **Automatic Tagging**: Tags files with `ingestid` (MD5 hash) and `mimeid` (MIME type)
- ✅ **Deduplication Protection**: In-memory tracking ensures files are only tagged once
- ✅ **NFS Compatible**: Uses polling instead of inotify (which doesn't work reliably with NFS)
- ✅ **Multi-Share Monitoring**: Watches all Hammerspace shares simultaneously
- ✅ **Detailed Logging**: All events logged to `logs/inotify.log` in JSON format
- ✅ **Agentic Event Consumption**: Query events via MCP tool for automated workflows
- ✅ **Real-time Web UI**: Monitor file ingestion at `/monitor` with live updates
- ✅ **RESTful API**: Access events via HTTP endpoints for integration

## MCP Tools

### 1. `start_inotify_monitor`

Starts the file monitoring service.

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "message": "File monitor started (polling mode - NFS compatible)",
  "watch_paths": [
    "/mnt/se-lab/modelstore",
    "/mnt/se-lab/upload",
    "/mnt/se-lab/tier0",
    ...
  ],
  "batch_interval": 15,
  "poll_interval": 2,
  "known_files": 42,
  "timestamp": "2025-10-09T16:33:31.820000"
}
```

**Example (Web UI)**:
```
Start inotify monitor to auto-tag new files
```

### 2. `get_file_monitor_status`

Gets current status of the monitoring service.

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "running": true,
  "watch_paths": [...],
  "batch_interval": 15,
  "poll_interval": 2,
  "pending_events": 3,
  "pending_files": 2,
  "known_files_count": 45,
  "tagged_files_count": 107,
  "files_tagged_retroactively": 50,
  "last_batch_time": "2025-10-09T16:33:51.977873",
  "last_untagged_scan": "2025-10-09T16:34:00.000000",
  "untagged_scan_interval": 5,
  "cpu_usage": {
    "current_cpu_percent": 0.5,
    "average_cpu_percent": 0.8,
    "max_cpu_percent": 5.2
  },
  "timestamp": "2025-10-09T16:34:05.123456"
}
```

**Example (Web UI)**:
```
Get file monitor status
```

### 3. `get_file_ingest_events`

Query recent file ingest and tagging events. **NEW** - Enables agentic consumption of file ingestion events.

**Parameters**:
```json
{
  "limit": 100,
  "event_type": "NEW_FILE",
  "file_pattern": ".pdf",
  "since_timestamp": "2025-10-09T20:00:00"
}
```

**Parameters Details**:
- `limit` (optional, default: 100): Maximum number of events to return
- `event_type` (optional): Filter by `NEW_FILE` or `RETROACTIVE_TAG`
- `file_pattern` (optional): Case-insensitive substring match on filename
- `since_timestamp` (optional): Only return events after this ISO timestamp

**Returns**:
```json
{
  "success": true,
  "events": [
    {
      "timestamp": "2025-10-09T22:32:16.182795",
      "event_type": "NEW_FILE",
      "file_name": "document.pdf",
      "file_path": "/mnt/se-lab/hub/incoming-pdfs/document.pdf",
      "md5_hash": "d8e8fca2dc0f896fd7cb4cb0031ba249",
      "mime_type": "application/pdf",
      "size_bytes": 2206196,
      "ingest_time": "2025-10-09T22:32:16.182795"
    }
  ],
  "count": 1,
  "limit": 100,
  "filters": {
    "event_type": "NEW_FILE",
    "file_pattern": ".pdf",
    "since_timestamp": "2025-10-09T20:00:00"
  }
}
```

**Example (Web UI)**:
```
Get the last 50 file ingest events for PDF files
Show me new files ingested in the last hour
Query file ingest events where filename contains 'model'
```

**Use Cases**:
- Build automated workflows based on file arrivals
- Track ingestion pipeline progress
- Audit file processing
- Trigger downstream processing when specific files arrive
- Generate reports on ingested files

### 4. `stop_inotify_monitor`

Stops the monitoring service and processes any remaining queued events.

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "message": "File monitor stopped",
  "timestamp": "2025-10-09T16:35:00.000000"
}
```

**Example (Web UI)**:
```
Stop inotify monitor
```

## How It Works

### 1. Discovery Phase
- Reads `/proc/mounts` to find all Hammerspace NFS mounts under `/mnt/se-lab/`
- Excludes the root mount, monitors only specific shares
- Performs initial scan to catalog existing files (won't tag pre-existing files)

### 2. Monitoring Phase
- Polls each mount point every 2 seconds
- Scans top-level directory for new files
- Detects files that weren't in the initial catalog
- Adds detected files to event queue

### 3. Batching Logic
Two modes:
- **Light Traffic** (< 5 files pending): Process immediately
- **Heavy Traffic** (≥ 5 files pending): Batch and process every 15 seconds

### 4. Event Processing
For each file:
1. Verify file still exists
2. Check if file is still being written (compare size after 100ms)
3. Calculate MD5 hash
4. Detect MIME type using python-magic
5. Emit event to log with full metadata
6. Tag file with `user.ingestid=<md5>` and `user.mimeid=<mimetype>`

### 5. Tagging
Uses HSTK CLI to apply tags:
```bash
hs tag set user.ingestid=4fee2aa9ba3d6572912729d15da9d320 /path/to/file
hs tag set user.mimeid=text/plain /path/to/file
```

## Event Log Format

Events are logged to `/home/mike/mcp-1.5/logs/inotify.log` in JSON format:

```json
{"timestamp": "2025-10-09T22:32:16.182795", "event_type": "NEW_FILE", "file_name": "document.pdf", "file_path": "/mnt/se-lab/hub/incoming-pdfs/document.pdf", "md5_hash": "d8e8fca2dc0f896fd7cb4cb0031ba249", "mime_type": "application/pdf", "size_bytes": 2206196, "ingest_time": "2025-10-09T22:32:16.182795"}
```

**Event Types**:
- `NEW_FILE` - File detected by polling (created after monitor started)
- `RETROACTIVE_TAG` - File found during periodic untagged file scan

**Event Fields**:
- `timestamp` - When the event was recorded
- `event_type` - NEW_FILE or RETROACTIVE_TAG
- `file_name` - Filename without path
- `file_path` - Full absolute path to file
- `md5_hash` - MD5 hash (also stored as `user.ingestid` tag)
- `mime_type` - MIME type (also stored as `user.mimeid` tag)
- `size_bytes` - File size in bytes
- `ingest_time` - When file was ingested

## Web UI Monitoring Dashboard

Access the real-time monitoring dashboard at **`http://localhost:5000/monitor`**

### Features:
- 📊 **Live Statistics**: Monitor status, file counts, watched paths, CPU usage
- 📁 **Event Stream**: Real-time display of file ingest events
- 🔔 **Toast Notifications**: Get notified when new files arrive
- 🔍 **Advanced Filtering**: Filter by event type, file pattern, or timestamp
- 📈 **Visual Indicators**: Color-coded event types (green for NEW_FILE, orange for RETROACTIVE_TAG)

### Accessing the Monitor:
1. Navigate to `http://localhost:5000`
2. Click the **"📊 Monitor"** button in the top toolbar
3. The dashboard opens in a new tab

### Dashboard Sections:
- **Stats Panel**: Real-time service statistics
- **Filters**: Query events by type, pattern, limit
- **Events List**: Scrollable list of recent events with full metadata
- **Live Indicator**: Shows connection status to event stream

## API Endpoints

### GET `/api/monitor/status`

Get current monitor service status.

**Response**:
```json
{
  "running": true,
  "watch_paths": [...],
  "tagged_files_count": 107,
  "cpu_usage": {...}
}
```

**Example**:
```bash
curl http://localhost:5000/api/monitor/status | jq
```

### GET `/api/monitor/events`

Query file ingest events with filters.

**Query Parameters**:
- `limit` (default: 100) - Maximum events to return
- `event_type` - Filter by NEW_FILE or RETROACTIVE_TAG
- `file_pattern` - Substring match on filename
- `since_timestamp` - ISO timestamp for time filtering

**Response**:
```json
{
  "success": true,
  "events": [...],
  "count": 50,
  "filters": {...}
}
```

**Examples**:
```bash
# Get last 10 events
curl "http://localhost:5000/api/monitor/events?limit=10"

# Get only new file events
curl "http://localhost:5000/api/monitor/events?event_type=NEW_FILE"

# Get PDF files only
curl "http://localhost:5000/api/monitor/events?file_pattern=.pdf"

# Get events since specific time
curl "http://localhost:5000/api/monitor/events?since_timestamp=2025-10-09T20:00:00"
```

### GET `/api/monitor/events/stream`

Stream file ingest events in real-time using Server-Sent Events (SSE).

**Response**: `text/event-stream`

**Example**:
```bash
curl -N http://localhost:5000/api/monitor/events/stream
```

**JavaScript Example**:
```javascript
const eventSource = new EventSource('/api/monitor/events/stream');
eventSource.onmessage = function(e) {
  const event = JSON.parse(e.data);
  console.log('New file:', event.file_name, event.md5_hash);
};
```

## Monitored Shares

By default, monitors all NFS mounts under `/mnt/se-lab/` except `/root`:

- `/mnt/se-lab/modelstore`
- `/mnt/se-lab/upload`
- `/mnt/se-lab/Milvuss3`
- `/mnt/se-lab/audio`
- `/mnt/se-lab/hub`
- `/mnt/se-lab/tier0`

## Use Cases

### Automated Ingestion Pipeline

1. **Start Monitor**:
   ```
   Start inotify monitor to auto-tag new files
   ```

2. **Copy Files to Hammerspace**:
   ```bash
   cp /source/data/*.bin /mnt/se-lab/upload/
   ```

3. **Automatic Tagging**: Files are detected and tagged automatically

4. **Query Tagged Files**:
   ```
   Check alignment of files tagged with ingestid
   ```

5. **Stop Monitor** (when done):
   ```
   Stop inotify monitor
   ```

### Continuous Monitoring

Leave the monitor running to continuously tag all new files as they arrive:

```
Start inotify monitor to auto-tag new files
```

Files will be tagged with:
- `user.ingestid=<md5hash>` - Unique identifier for deduplication
- `user.mimeid=<mimetype>` - MIME type for classification

## Deduplication Protection

The monitor ensures each file is tagged **exactly once** using in-memory tracking:

### How It Works:
1. **`tagged_files` Set**: Tracks all processed file paths in memory
2. **Fast Lookup**: O(1) check before processing any file
3. **Prevents Reprocessing**: Once tagged, file is never reprocessed
4. **Efficient Scanning**: Subsequent scans skip already-processed files instantly

### Verification:
```bash
# Check for duplicate processing
./check_duplicates.sh

# Should show: "✅ NO DUPLICATES FOUND!"
```

### Why This Matters:
- **Before Fix**: Files were tagged 20-50 times repeatedly
- **After Fix**: Each file tagged exactly once
- **Performance**: Dramatically reduced I/O and CPU usage
- **Clean Logs**: Only genuine new file events are logged

See `DEDUPLICATION_FIX_FINAL.md` for technical details.

## Performance

- **Polling Interval**: 2 seconds
- **Batch Interval**: 15 seconds (or immediate for < 5 files)
- **Untagged Scan**: Every 5 seconds (retroactive tagging of existing files)
- **File Processing**: ~500ms per file (MD5 + MIME + 2 tag operations)
- **Overhead**: Minimal - scans up to 3 directory levels deep
- **CPU Usage**: < 1% average, < 10% peak during batch processing
- **Deduplication**: O(1) in-memory lookup - no repeated subprocess calls

## Limitations

### Current Implementation
- ✅ Monitors top-level directory of each share
- ❌ Does NOT recursively monitor subdirectories (prevents performance issues)
- ✅ NFS-compatible (uses polling instead of inotify)
- ✅ Handles large files efficiently (chunked MD5 calculation)

### Why Not Recursive?
Recursive monitoring could scan thousands of files, causing:
- High CPU usage
- Network load on NFS
- Slow poll cycles

**Recommendation**: Place new files in the top-level of shares, or organize by date/batch subdirectories and restart the monitor when needed.

## Troubleshooting

### Monitor Won't Start

**Check dependencies**:
```bash
pip install python-magic inotify_simple
```

**Check mounts**:
```bash
mount | grep hammerspace
```

### Files Not Being Detected

1. **Check monitor is running**:
   ```
   Get inotify monitor status
   ```

2. **Verify file is in top-level directory**:
   ```bash
   ls /mnt/se-lab/upload/
   ```

3. **Check logs**:
   ```bash
   tail -f /home/mike/mcp-1.5/logs/inotify.log
   ```

### Tags Not Applied

1. **Check HSTK CLI is working**:
   ```bash
   /home/mike/hs-mcp-1.0/.venv/bin/hs tag list /path/to/file
   ```

2. **Look for tagging errors in logs**:
   ```bash
   grep "Failed to tag" /home/mike/mcp-1.5/logs/inotify.log
   ```

## Advanced Configuration

### Adjust Batch Interval

Edit `src/inotify_monitor.py`:
```python
self.batch_interval = 15  # Change to desired seconds
```

### Adjust Poll Interval

Edit `src/inotify_monitor.py`:
```python
self.poll_interval = 2  # Change to desired seconds
```

### Customize Tag Names

Edit the `tag_file` method in `src/inotify_monitor.py`:
```python
def tag_file(self, file_path: str, ingest_id: str, mime_id: str) -> bool:
    # Change "user.ingestid" and "user.mimeid" to your preferred tag names
    ingest_tag_cmd = [self.hs_cli, "tag", "set", f"user.ingestid={ingest_id}", file_path]
    mime_tag_cmd = [self.hs_cli, "tag", "set", f"user.mimeid={mime_id}", file_path]
```

## Dependencies

- `python-magic` - MIME type detection
- `inotify_simple` - (Not used in polling mode, but kept for future enhancements)
- HSTK CLI - `/home/mike/hs-mcp-1.0/.venv/bin/hs`

## Examples

### Start Monitoring and Create Test Files

```bash
# Via Web UI
"Start inotify monitor to auto-tag new files"

# Create test files
echo "test1" > /mnt/se-lab/upload/test1.txt
echo "test2" > /mnt/se-lab/upload/test2.txt
echo "test3" > /mnt/se-lab/upload/test3.txt

# Wait 5 seconds, then check status
"Get inotify monitor status"

# Should show 3 files processed

# Verify tags
hs tag list /mnt/se-lab/upload/test1.txt
# Should show user.ingestid and user.mimeid tags
```

---

**Monitor Service**: `src/inotify_monitor.py`  
**Log File**: `logs/inotify.log`  
**Status**: ✅ PRODUCTION READY

