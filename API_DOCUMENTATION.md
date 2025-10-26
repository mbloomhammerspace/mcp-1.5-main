# MCP 1.5 API Documentation

This document provides comprehensive API documentation for all MCP servers and web interface endpoints in the MCP 1.5 system.

## Table of Contents

1. [Hammerspace MCP Server](#hammerspace-mcp-server)
2. [Milvus MCP Server](#milvus-mcp-server)
3. [Kubernetes MCP Server](#kubernetes-mcp-server)
4. [Web UI API Endpoints](#web-ui-api-endpoints)
5. [File Monitor API](#file-monitor-api)
6. [Event System API](#event-system-api)

## Hammerspace MCP Server

**Transport**: stdio-based communication  
**Server**: `src/aiq_hstk_mcp_server.py`  
**Dependencies**: Hammerspace HSTK CLI, NVIDIA API key (optional)

### Core Tools

#### `tag_directory_recursive`
Recursively tag all files in a directory with a custom tag.

**Parameters**:
```json
{
  "path": "/mnt/anvil/hub/my-folder",
  "tag_name": "user.modelsetid",
  "tag_value": "my-demo"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully tagged 15 files in /mnt/anvil/hub/my-folder",
  "files_tagged": 15
}
```

#### `check_tagged_files_alignment`
Find and check alignment status of files with specific tags.

**Parameters**:
```json
{
  "tag_name": "user.modelsetid",
  "tag_value": "my-demo",
  "share_path": "/mnt/anvil/hub/"
}
```

**Response**:
```json
{
  "success": true,
  "files_found": 15,
  "alignment_status": {
    "fully_aligned": 12,
    "partially_aligned": 2,
    "not_aligned": 1
  },
  "details": [
    {
      "file": "/mnt/anvil/hub/file1.pdf",
      "status": "FULLY_ALIGNED",
      "objectives": ["Place-on-tier0"]
    }
  ]
}
```

#### `apply_objective_to_path`
Apply Hammerspace objectives to a specific path.

**Parameters**:
```json
{
  "objective_name": "Place-on-tier0",
  "path": "/mnt/anvil/hub/my-folder"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully applied Place-on-tier0 to /mnt/anvil/hub/my-folder",
  "objective": "Place-on-tier0",
  "path": "/mnt/anvil/hub/my-folder"
}
```

#### `remove_objective_from_path`
Remove objectives from a specific path.

**Parameters**:
```json
{
  "objective_name": "Place-on-tier0",
  "path": "/mnt/anvil/hub/my-folder"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully removed Place-on-tier0 from /mnt/anvil/hub/my-folder",
  "objective": "Place-on-tier0",
  "path": "/mnt/anvil/hub/my-folder"
}
```

#### `list_objectives_for_path`
List all objectives applied to a specific path.

**Parameters**:
```json
{
  "path": "/mnt/anvil/hub/my-folder"
}
```

**Response**:
```json
{
  "success": true,
  "objectives": [
    {
      "name": "Place-on-tier0",
      "status": "ACTIVE",
      "applied_date": "2025-10-23T14:30:00Z"
    }
  ]
}
```

#### `ingest_new_files`
Find new files, tag them, and place on Tier 1.

**Parameters**:
```json
{
  "path": "/mnt/anvil/hub/",
  "tag_name": "user.modelsetid",
  "tag_value": "new-batch",
  "age_minutes": 60
}
```

**Response**:
```json
{
  "success": true,
  "files_processed": 8,
  "files_tagged": 8,
  "files_placed": 8,
  "details": [
    {
      "file": "/mnt/anvil/hub/file1.pdf",
      "tagged": true,
      "placed": true,
      "tier": "Tier1"
    }
  ]
}
```

#### `refresh_mounts`
Refresh NFS mounts to resolve stale file handles.

**Parameters**:
```json
{
  "mount_type": "all"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully refreshed all NFS mounts",
  "mounts_refreshed": 3
}
```

### File Monitoring Tools

#### `start_inotify_monitor`
Start automated file monitoring service.

**Parameters**:
```json
{}
```

**Response**:
```json
{
  "success": true,
  "message": "File monitoring service started",
  "monitor_id": "monitor_12345",
  "watched_paths": ["/mnt/anvil/hub/"],
  "polling_interval": 5
}
```

#### `get_file_monitor_status`
Get current status of the file monitoring service.

**Parameters**:
```json
{}
```

**Response**:
```json
{
  "success": true,
  "monitor_running": true,
  "watched_paths": ["/mnt/anvil/hub/"],
  "pending_events": 3,
  "files_tagged": 127,
  "cpu_usage": "2.3%",
  "memory_usage": "45MB",
  "last_activity": "2025-10-23T14:30:00Z"
}
```

#### `get_file_ingest_events`
Query file ingestion events with filtering.

**Parameters**:
```json
{
  "limit": 100,
  "event_type": "NEW_FILE",
  "file_pattern": ".pdf",
  "since_timestamp": "2025-10-23T14:00:00Z"
}
```

**Response**:
```json
{
  "success": true,
  "events": [
    {
      "timestamp": "2025-10-23T14:30:00Z",
      "event_type": "NEW_FILE",
      "file_name": "document.pdf",
      "file_path": "/mnt/anvil/hub/document.pdf",
      "md5_hash": "abc123def456",
      "mime_type": "application/pdf",
      "size_bytes": 1024000,
      "ingest_time": "2025-10-23T14:30:00Z"
    }
  ],
  "total_events": 1,
  "has_more": false
}
```

#### `stop_inotify_monitor`
Stop the file monitoring service.

**Parameters**:
```json
{}
```

**Response**:
```json
{
  "success": true,
  "message": "File monitoring service stopped",
  "monitor_id": "monitor_12345"
}
```

## Milvus MCP Server

**Transport**: HTTP/SSE on port 9902  
**Server**: `mcp-server-milvus/`  
**Dependencies**: Milvus database instance

### Collection Management

#### `create_collection`
Create a new Milvus collection.

**Parameters**:
```json
{
  "collection_name": "my_collection",
  "description": "Collection for my documents",
  "dimension": 768
}
```

**Response**:
```json
{
  "success": true,
  "collection_name": "my_collection",
  "message": "Collection created successfully"
}
```

#### `list_collections`
List all available collections.

**Parameters**:
```json
{}
```

**Response**:
```json
{
  "success": true,
  "collections": [
    {
      "name": "my_collection",
      "description": "Collection for my documents",
      "document_count": 150,
      "created_at": "2025-10-23T14:30:00Z"
    }
  ]
}
```

#### `delete_collection`
Delete a collection and all its data.

**Parameters**:
```json
{
  "collection_name": "my_collection"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Collection my_collection deleted successfully"
}
```

### Vector Operations

#### `insert_vectors`
Insert vector embeddings into a collection.

**Parameters**:
```json
{
  "collection_name": "my_collection",
  "vectors": [
    {
      "id": "doc_1",
      "vector": [0.1, 0.2, 0.3, ...],
      "metadata": {
        "filename": "document.pdf",
        "file_path": "/mnt/anvil/hub/document.pdf"
      }
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "inserted_count": 1,
  "message": "Vectors inserted successfully"
}
```

#### `search_vectors`
Search for similar vectors in a collection.

**Parameters**:
```json
{
  "collection_name": "my_collection",
  "query_vector": [0.1, 0.2, 0.3, ...],
  "top_k": 10,
  "similarity_threshold": 0.8
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "id": "doc_1",
      "similarity": 0.95,
      "metadata": {
        "filename": "document.pdf",
        "file_path": "/mnt/anvil/hub/document.pdf"
      }
    }
  ],
  "total_results": 1
}
```

## Kubernetes MCP Server

**Transport**: HTTP/SSE on port 9903  
**Status**: Not yet implemented  
**Dependencies**: Kubernetes cluster access

### Planned Tools

#### `create_job`
Create a Kubernetes job for file processing.

**Parameters**:
```json
{
  "job_name": "pdf-ingest-job",
  "image": "pdf-processor:latest",
  "files": ["/mnt/anvil/hub/file1.pdf", "/mnt/anvil/hub/file2.pdf"],
  "collection_name": "my_collection"
}
```

#### `get_job_status`
Get the status of a Kubernetes job.

**Parameters**:
```json
{
  "job_name": "pdf-ingest-job"
}
```

#### `delete_job`
Delete a Kubernetes job.

**Parameters**:
```json
{
  "job_name": "pdf-ingest-job"
}
```

## Web UI API Endpoints

**Base URL**: `http://localhost:5000`  
**Server**: `web_ui/app.py`  
**Dependencies**: Anthropic API key, MCP servers

### Chat Interface

#### `POST /api/chat`
Natural language chat interface with Claude AI.

**Request**:
```json
{
  "message": "Tag all files in /mnt/anvil/hub/my-folder as modelsetid=my-demo"
}
```

**Response**:
```json
{
  "response": "I'll tag all files in that folder with the modelsetid=my-demo tag.",
  "action_taken": "tag_directory_recursive",
  "parameters": {
    "path": "/mnt/anvil/hub/my-folder",
    "tag_name": "user.modelsetid",
    "tag_value": "my-demo"
  },
  "result": {
    "success": true,
    "files_tagged": 15
  }
}
```

### Monitoring Endpoints

#### `GET /api/monitor/status`
Get comprehensive service status.

**Response**:
```json
{
  "services": {
    "file_monitor": {
      "status": "running",
      "uptime": "2h 30m",
      "files_processed": 127,
      "cpu_usage": "2.3%",
      "memory_usage": "45MB"
    },
    "web_ui": {
      "status": "running",
      "uptime": "2h 30m",
      "port": 5000
    },
    "hammerspace_mcp": {
      "status": "running",
      "uptime": "2h 30m"
    },
    "milvus_mcp": {
      "status": "running",
      "uptime": "2h 30m",
      "port": 9902
    }
  },
  "system": {
    "timestamp": "2025-10-23T14:30:00Z",
    "uptime": "2h 30m"
  }
}
```

#### `GET /api/monitor/events`
Query ingestion events with filtering.

**Query Parameters**:
- `limit`: Maximum number of events (default: 100)
- `event_type`: Filter by event type (NEW_FILE, FOLDER_INGEST_SUCCESS, etc.)
- `file_pattern`: Filter by file pattern (e.g., ".pdf", "test-")
- `since`: Filter events since timestamp

**Response**:
```json
{
  "events": [
    {
      "timestamp": "2025-10-23T14:30:00Z",
      "event_type": "NEW_FILE",
      "file_name": "document.pdf",
      "file_path": "/mnt/anvil/hub/document.pdf",
      "md5_hash": "abc123def456",
      "mime_type": "application/pdf",
      "size_bytes": 1024000,
      "ingest_time": "2025-10-23T14:30:00Z"
    }
  ],
  "total_events": 1,
  "has_more": false
}
```

#### `GET /api/monitor/events/stream`
Server-Sent Events stream for real-time event monitoring.

**Response**: Continuous stream of events in SSE format:
```
data: {"timestamp": "2025-10-23T14:30:00Z", "event_type": "NEW_FILE", "file_name": "document.pdf", ...}

data: {"timestamp": "2025-10-23T14:30:05Z", "event_type": "FOLDER_INGEST_SUCCESS", "folder_name": "my-folder", ...}
```

### Debug Endpoints

#### `GET /api/logs/stream`
Stream debug logs in real-time.

**Response**: Continuous stream of log entries in SSE format:
```
data: {"timestamp": "2025-10-23T14:30:00Z", "level": "INFO", "message": "File monitor started", "service": "file_monitor"}

data: {"timestamp": "2025-10-23T14:30:05Z", "level": "INFO", "message": "New file detected: document.pdf", "service": "file_monitor"}
```

#### `GET /api/tools`
List all available MCP tools.

**Response**:
```json
{
  "tools": [
    {
      "name": "tag_directory_recursive",
      "description": "Recursively tag all files in a directory",
      "parameters": {
        "path": "string",
        "tag_name": "string",
        "tag_value": "string"
      }
    },
    {
      "name": "apply_objective_to_path",
      "description": "Apply Hammerspace objectives to a path",
      "parameters": {
        "objective_name": "string",
        "path": "string"
      }
    }
  ]
}
```

## File Monitor API

**Internal API**: Used by file monitor daemon  
**Dependencies**: Hammerspace CLI, Kubernetes cluster, Milvus database

### Event Types

#### `NEW_FILE`
Triggered when a new file is detected.

**Event Data**:
```json
{
  "timestamp": "2025-10-23T14:30:00Z",
  "event_type": "NEW_FILE",
  "file_name": "document.pdf",
  "file_path": "/mnt/anvil/hub/document.pdf",
  "md5_hash": "abc123def456",
  "mime_type": "application/pdf",
  "size_bytes": 1024000,
  "ingest_time": "2025-10-23T14:30:00Z"
}
```

#### `FOLDER_INGEST_SUCCESS`
Triggered when a folder is successfully processed.

**Event Data**:
```json
{
  "timestamp": "2025-10-23T14:30:00Z",
  "event_type": "FOLDER_INGEST_SUCCESS",
  "folder_name": "my-folder",
  "folder_path": "/mnt/anvil/hub/my-folder",
  "file_count": 15,
  "status": "SUCCESS",
  "job_type": "folder_ingest",
  "collection_name": "my_folder_collection",
  "ingest_time": "2025-10-23T14:30:00Z"
}
```

#### `TIER0_PROMOTION_BY_TAG`
Triggered when files are promoted to tier0 based on tags.

**Event Data**:
```json
{
  "timestamp": "2025-10-23T14:30:00Z",
  "event_type": "TIER0_PROMOTION_BY_TAG",
  "tag_name": "embedding",
  "files_affected": 15,
  "status": "SUCCESS",
  "operation": "via kubernetes mcp",
  "ingest_time": "2025-10-23T14:30:00Z"
}
```

#### `TIER0_DEMOTION_BY_TAG`
Triggered when files are demoted from tier0 after embedding.

**Event Data**:
```json
{
  "timestamp": "2025-10-23T14:30:00Z",
  "event_type": "TIER0_DEMOTION_BY_TAG",
  "tag_name": "embedding",
  "files_affected": 15,
  "status": "SUCCESS",
  "operation": "via milvus mcp",
  "ingest_time": "2025-10-23T14:30:00Z"
}
```

## Error Handling

### Common Error Responses

#### Authentication Error
```json
{
  "error": "authentication_failed",
  "message": "Invalid API key",
  "code": 401
}
```

#### Validation Error
```json
{
  "error": "validation_error",
  "message": "Invalid parameter: path is required",
  "code": 400,
  "details": {
    "parameter": "path",
    "issue": "required_field_missing"
  }
}
```

#### Service Error
```json
{
  "error": "service_error",
  "message": "Hammerspace CLI not available",
  "code": 503,
  "details": {
    "service": "hammerspace_mcp",
    "issue": "cli_not_found"
  }
}
```

### Error Codes

- **400**: Bad Request - Invalid parameters
- **401**: Unauthorized - Authentication failed
- **403**: Forbidden - Insufficient permissions
- **404**: Not Found - Resource not found
- **500**: Internal Server Error - Server error
- **503**: Service Unavailable - External service unavailable

## Rate Limiting

### Web UI Endpoints
- **Chat API**: 10 requests per minute per IP
- **Event Streaming**: 1 connection per IP
- **Log Streaming**: 1 connection per IP

### MCP Server Endpoints
- **Hammerspace MCP**: No rate limiting (stdio-based)
- **Milvus MCP**: 100 requests per minute per connection
- **Kubernetes MCP**: 50 requests per minute per connection

## Authentication

### API Keys
- **Anthropic API Key**: Required for Web UI chat functionality
- **NVIDIA API Key**: Optional for AI features
- **Hammerspace API**: Not required (uses CLI)

### Access Control
- **Web UI**: No authentication required (development)
- **MCP Servers**: stdio-based communication (no HTTP auth)
- **File Monitor**: Internal service (no external access)

## Monitoring and Health Checks

### Health Check Endpoints
- **Web UI**: `GET /health` - Returns service status
- **Milvus MCP**: `GET /health` - Returns database connection status
- **Kubernetes MCP**: `GET /health` - Returns cluster connection status

### Metrics
- **Request Count**: Number of API requests
- **Response Time**: Average response time
- **Error Rate**: Percentage of failed requests
- **Service Uptime**: Service availability

---

**MCP 1.5 API Documentation** - Comprehensive API reference for all MCP servers and web interface endpoints.

