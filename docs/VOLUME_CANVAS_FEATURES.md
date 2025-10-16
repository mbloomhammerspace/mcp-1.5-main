# Volume Canvas Features Documentation

This document provides a comprehensive overview of all features available in the Volume Canvas GUI and their corresponding MCP server endpoints in the NVIDIA AI Q Toolkit implementation.

## Overview

The Volume Canvas is a web-based interface for managing volume movement operations in the Hammerspace federated storage system. It provides a visual canvas for exploring volumes, shares, and files, and applying objectives to move data between different storage tiers.

## Feature Categories

### 1. Volume Management
### 2. File Management
### 3. Data Movement Operations
### 4. Objective Management
### 5. Job Monitoring
### 6. Tag Management
### 7. System Analysis
### 8. Debug and Diagnostic Tools

---

## 1. Volume Management

### Volume Explorer
**GUI Component**: Left panel with volume categorization and filtering
**MCP Endpoint**: `list_volumes`

**Features**:
- Browse and categorize volumes (LSS, Tier0, Tier1, Third-party)
- Filter by volume type
- Display volume status, size, and usage information
- Click to select volumes for operations

**MCP Function**:
```python
@aiq.function
async def list_volumes(filter: str = "all", storage_system: str = "production") -> Dict[str, Any]:
    """List all storage volumes with categorization."""
```

**Parameters**:
- `filter`: Volume type filter ("all", "lss", "tier0", "tier1", "third_party", "production", "se-lab")
- `storage_system`: Target storage system ("production", "se-lab")

**Response**:
```json
{
  "volumes": [
    {
      "uuid": "volume-uuid",
      "name": "volume-name",
      "type": "lss",
      "state": "UP",
      "size_bytes": 1000000000,
      "used_bytes": 500000000,
      "created": "2024-01-01T00:00:00Z",
      "modified": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Share Management
**GUI Component**: Center panel showing shares for selected volume
**MCP Endpoint**: `list_shares`

**Features**:
- List all shares for a given volume
- Display share information (name, path, file count)
- Navigate to share contents

**MCP Function**:
```python
@aiq.function
async def list_shares(volume_uuid: str, storage_system: str = "production") -> Dict[str, Any]:
    """List all shares for a given volume."""
```

---

## 2. File Management

### File Browser
**GUI Component**: Center panel with file navigation and breadcrumb navigation
**MCP Endpoint**: `list_files`

**Features**:
- Navigate through shares and files
- Breadcrumb navigation for easy path tracking
- Click to select files for operations
- Display file properties (size, dates, location)

**MCP Function**:
```python
@aiq.function
async def list_files(path: str, limit: int = 100, storage_system: str = "production") -> Dict[str, Any]:
    """List files in a specific path."""
```

### File Search
**GUI Component**: Tag search dialog with regex support
**MCP Endpoint**: `search_files`

**Features**:
- Search files using regex patterns
- Search by tags and/or paths
- Case-sensitive/insensitive options
- Real-time search results

**MCP Function**:
```python
@aiq.function
async def search_files(
    query: str, 
    search_by_tags: bool = True, 
    search_by_path: bool = True, 
    case_sensitive: bool = False,
    storage_system: str = "production"
) -> Dict[str, Any]:
    """Search for files using various criteria."""
```

---

## 3. Data Movement Operations

### Operation Canvas
**GUI Component**: Right panel for configuring operations
**MCP Endpoints**: `copy_files`, `clone_files`, `move_files`

**Features**:
- Drag-and-drop interface for selecting source and target
- Visual operation configuration
- Real-time operation monitoring
- Progress tracking

### Copy Operation
**MCP Function**:
```python
@aiq.function
async def copy_files(
    source_type: str, 
    target_type: str, 
    path: str, 
    recursive: bool = True,
    storage_system: str = "production"
) -> Dict[str, Any]:
    """Copy files from source to target volume."""
```

### Clone Operation
**MCP Function**:
```python
@aiq.function
async def clone_files(
    source_type: str, 
    target_type: str, 
    path: str,
    storage_system: str = "production"
) -> Dict[str, Any]:
    """Clone files from source to target volume."""
```

### Move Operation
**MCP Function**:
```python
@aiq.function
async def move_files(
    source_type: str, 
    target_type: str, 
    path: str,
    storage_system: str = "production"
) -> Dict[str, Any]:
    """Move files from source to target volume."""
```

---

## 4. Objective Management

### Objective Selection
**GUI Component**: Objective selector in operation canvas
**MCP Endpoints**: `place_on_tier`, `exclude_from_tier`

**Features**:
- Choose between Copy, Clone, and Move operations
- Create storage objectives
- Manage tier placement rules

### Place on Tier Objective
**MCP Function**:
```python
@aiq.function
async def place_on_tier(
    volume_type: str, 
    path: str, 
    tier_name: str,
    storage_system: str = "production"
) -> Dict[str, Any]:
    """Create a place-on-tier objective."""
```

### Exclude from Tier Objective
**MCP Function**:
```python
@aiq.function
async def exclude_from_tier(
    volume_type: str, 
    path: str, 
    tier_name: str,
    storage_system: str = "production"
) -> Dict[str, Any]:
    """Create an exclude-from-tier objective."""
```

---

## 5. Job Monitoring

### Job Monitor
**GUI Component**: Job monitoring section in operation canvas
**MCP Endpoints**: `list_jobs`, `get_job_status`

**Features**:
- Real-time job progress monitoring
- Job status tracking
- Error reporting
- Job history

### List Jobs
**MCP Function**:
```python
@aiq.function
async def list_jobs(
    storage_system: str = "production",
    status_filter: str = "all"
) -> Dict[str, Any]:
    """List all active data movement jobs."""
```

### Get Job Status
**MCP Function**:
```python
@aiq.function
async def get_job_status(job_uuid: str, storage_system: str = "production") -> Dict[str, Any]:
    """Get detailed status of a specific job."""
```

---

## 6. Tag Management

### File Tagging
**GUI Component**: Tagging section in operation canvas
**MCP Endpoints**: `get_tags`, `set_tag`, `clear_all_tags`

**Features**:
- View current tags on files/folders/shares
- Add new tags
- Remove existing tags
- Clear all tags

### Get Tags
**MCP Function**:
```python
@aiq.function
async def get_tags(path: str, storage_system: str = "production") -> Dict[str, Any]:
    """Get tags for a specific file, folder, or share."""
```

### Set Tag
**MCP Function**:
```python
@aiq.function
async def set_tag(
    path: str, 
    tag_name: str, 
    tag_value: str,
    storage_system: str = "production"
) -> Dict[str, Any]:
    """Set a tag on a file, folder, or share."""
```

### Clear All Tags
**MCP Function**:
```python
@aiq.function
async def clear_all_tags(path: str, storage_system: str = "production") -> Dict[str, Any]:
    """Clear all tags from a file, folder, or share."""
```

---

## 7. System Analysis

### System Status
**GUI Component**: System status indicators and health checks
**MCP Endpoint**: `get_system_status`

**Features**:
- Overall system health monitoring
- Storage system detection
- Resource utilization tracking

**MCP Function**:
```python
@aiq.function
async def get_system_status(storage_system: str = "production") -> Dict[str, Any]:
    """Get overall system status and health."""
```

### Volume Constraint Analysis
**GUI Component**: Volume constraint analyzer in debug console
**MCP Endpoint**: `analyze_volume_constraints`

**Features**:
- Analyze volume capacity constraints
- Check durability and performance limits
- Identify potential issues

**MCP Function**:
```python
@aiq.function
async def analyze_volume_constraints(
    volume_type: str, 
    storage_system: str = "production"
) -> Dict[str, Any]:
    """Analyze volume constraints and capacity."""
```

---

## 8. Debug and Diagnostic Tools

### Objective Debug Console
**GUI Component**: Full-height debug console panel
**MCP Endpoint**: `get_objective_debug_info`

**Features**:
- Debug summary with objective statistics
- Failed objectives analysis
- LLM-powered suggestions
- Error log analysis

**MCP Function**:
```python
@aiq.function
async def get_objective_debug_info(
    objective_name: str = "",
    storage_system: str = "production"
) -> Dict[str, Any]:
    """Get debug information for objectives."""
```

### Data Integrity Verification
**GUI Component**: Data verification tools
**MCP Endpoint**: `verify_data_integrity`

**Features**:
- Verify data integrity after operations
- Check data consistency
- Validate file integrity

**MCP Function**:
```python
@aiq.function
async def verify_data_integrity(
    volume_type: str, 
    path: str,
    storage_system: str = "production"
) -> Dict[str, Any]:
    """Verify data integrity on a volume."""
```

---

## Workflow Integration

### Volume Migration Workflow
**Description**: Complete workflow for migrating data between volumes
**Steps**:
1. `list_volumes` - Get available volumes
2. `list_files` - Browse source files
3. `copy_files` - Execute copy operation
4. `verify_data_integrity` - Verify copied data
5. `get_job_status` - Monitor job progress

### Objective Management Workflow
**Description**: Workflow for managing storage objectives
**Steps**:
1. `place_on_tier` - Create placement objectives
2. `exclude_from_tier` - Create exclusion objectives
3. `get_objective_debug_info` - Monitor objective status

### System Analysis Workflow
**Description**: Complete system analysis workflow
**Steps**:
1. `get_system_status` - Get overall system health
2. `analyze_volume_constraints` - Analyze volume limitations
3. `list_jobs` - Check active operations
4. `get_objective_debug_info` - Review objective status

---

## Storage System Support

### Production System
- **Mount Point**: `/mnt/hammerspace`
- **System Type**: Production (diweins)
- **Default Configuration**: Primary system

### SE Lab System
- **Mount Point**: `/mnt/se-lab/tier0`
- **System Type**: SE Lab (mb.local)
- **Default Configuration**: Development/testing system

---

## Error Handling

All MCP functions include comprehensive error handling:

- **Authentication Errors**: Invalid credentials or permissions
- **API Errors**: Hammerspace API communication issues
- **Validation Errors**: Invalid parameters or data
- **System Errors**: Storage system unavailability
- **Network Errors**: Connection timeouts or failures

Error responses follow a consistent format:
```json
{
  "error": "Error description",
  "success": false,
  "data": null
}
```

---

## Performance Considerations

### Caching
- Volume and share information is cached for performance
- File listings are limited to prevent memory issues
- Search results are paginated for large datasets

### Rate Limiting
- API calls are rate-limited to prevent system overload
- Concurrent operations are queued and managed
- Timeout handling for long-running operations

### Resource Management
- Memory usage is monitored and controlled
- Database connections are pooled and managed
- Log files are rotated to prevent disk space issues

---

## Security Features

### Authentication
- Secure credential storage using environment variables
- SSL/TLS support for API communications
- Token-based authentication for MCP clients

### Authorization
- Role-based access control for different operations
- Permission validation for file and volume operations
- Audit logging for all operations

### Data Protection
- Encrypted data transmission
- Secure credential management
- Input validation and sanitization

---

## Monitoring and Logging

### Logging Levels
- **DEBUG**: Detailed operation information
- **INFO**: General operation status
- **WARNING**: Non-critical issues
- **ERROR**: Operation failures
- **CRITICAL**: System-level failures

### Log Files
- `logs/hs_1_5_nvidia.log` - Main application log
- `logs/aiq_mcp_server.log` - MCP server log
- `logs/llm_sessions.log` - LLM interaction log

### Metrics
- Operation success/failure rates
- Response times and performance metrics
- Resource utilization statistics
- Error frequency and patterns

---

## Future Enhancements

### Planned Features
- **Real-time WebSocket Updates**: Live job progress updates
- **Batch Operations**: Select multiple files for operations
- **Operation History**: Track and replay previous operations
- **Advanced Filtering**: Filter files by size, date, type
- **Visual Job Dependencies**: Show operation dependencies
- **Integration with Main Project**: Merge into existing web UI

### API Improvements
- **GraphQL Support**: More flexible query capabilities
- **Webhook Integration**: Real-time event notifications
- **Advanced Search**: Full-text search capabilities
- **Custom Workflows**: User-defined operation sequences

### Performance Optimizations
- **Parallel Processing**: Concurrent operation execution
- **Smart Caching**: Intelligent data caching strategies
- **Load Balancing**: Distributed operation processing
- **Resource Optimization**: Dynamic resource allocation
