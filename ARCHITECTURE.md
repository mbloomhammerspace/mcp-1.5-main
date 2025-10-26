# MCP 1.5 Architecture Documentation

This document provides a comprehensive overview of the MCP 1.5 system architecture, including all components, data flows, and integration points.

## System Overview

MCP 1.5 is a production-ready Model Context Protocol (MCP) server system for Hammerspace storage management with natural language interface, automatic file ingestion, and comprehensive monitoring capabilities.

## Core Components

### 1. MCP Servers

#### Hammerspace MCP Server (`src/aiq_hstk_mcp_server.py`)
- **Purpose**: Provides MCP interface for Hammerspace storage operations
- **Transport**: stdio-based communication
- **Features**:
  - Real HSTK CLI command execution (no mock data)
  - Automatic retry on stale file handle errors
  - Enhanced Unicode handling and error recovery
  - Improved tag operations with fallback methods
- **Dependencies**: Hammerspace HSTK CLI, NVIDIA API key (optional)

#### Milvus MCP Server (`mcp-server-milvus/`)
- **Purpose**: Provides MCP interface for Milvus vector database operations
- **Transport**: HTTP/SSE on port 9902
- **Features**:
  - Collection management
  - Vector embedding storage and retrieval
  - Semantic search capabilities
- **Dependencies**: Milvus database instance

#### Kubernetes MCP Server (Planned)
- **Purpose**: Provides MCP interface for Kubernetes operations
- **Transport**: HTTP/SSE on port 9903
- **Status**: Not yet implemented
- **Dependencies**: Kubernetes cluster access

### 2. File Monitoring System

#### File Monitor Daemon (`src/file_monitor_daemon.py`)
- **Purpose**: Standalone daemon for continuous file monitoring
- **Features**:
  - Polling-based detection on NFS 4.2 mounts
  - Multi-format file support (BMP, DOCX, HTML, JPEG, JSON, MD, PDF, PNG, PPTX, SH, TIFF, TXT, MP3)
  - Automatic tagging with MD5 hash and MIME type
  - Tag-based tier management with automatic tier0 promotion/demotion
  - Recursive folder tagging for 40x performance improvement
- **Dependencies**: NFS mounts, Hammerspace CLI

#### File Monitor Core (`src/file_monitor.py`)
- **Purpose**: Core logic for file detection, ingestion, and tier management
- **Features**:
  - Intelligent file type detection
  - Folder-based batch processing
  - Kubernetes job deployment
  - Milvus collection management
  - Event logging and streaming
- **Dependencies**: Kubernetes cluster, Milvus database

### 3. Web Interface

#### Web UI Server (`web_ui/app.py`)
- **Purpose**: Flask-based natural language interface
- **Port**: 5000
- **Features**:
  - Claude AI integration for natural language processing
  - Real-time debug log streaming
  - File ingest monitor dashboard
  - Event filtering and monitoring
  - Multi-service status monitoring
- **Dependencies**: Anthropic API key, MCP servers

#### Web UI Templates
- **Monitor Dashboard** (`web_ui/templates/monitor.html`): Real-time file monitoring
- **Events Console** (`web_ui/templates/events.html`): Event filtering and display
- **Debug Console** (`web_ui/templates/debug.html`): Log streaming and debugging

### 4. Service Management

#### Unified Startup Script (`start_all_services.sh`)
- **Purpose**: Manages all MCP services with enhanced persistence
- **Features**:
  - Screen session persistence
  - Auto-restart capability
  - Systemd integration
  - Port conflict resolution
  - Comprehensive logging
  - Health monitoring
- **Dependencies**: Screen, Python 3, systemd (optional)

## Data Flow Architecture

### File Ingestion Pipeline

```
New File/Folder Detection
         ↓
    File Monitor Daemon
         ↓
    Automatic Tagging
    (ingestid, mimeid, embedding)
         ↓
    Tier0 Promotion
    (for embedding files)
         ↓
    Kubernetes Job Creation
         ↓
    File Processing
    (multi-format support)
         ↓
    Milvus Collection
    (vector embeddings)
         ↓
    Tier0 Demotion
    (after embedding)
         ↓
    Event Logging
         ↓
    Web UI Dashboard
```

### Natural Language Interface Flow

```
User Input (Natural Language)
         ↓
    Claude AI Processing
         ↓
    MCP Tool Selection
         ↓
    Hammerspace MCP Server
         ↓
    HSTK CLI Execution
         ↓
    Hammerspace Storage
         ↓
    Response Generation
         ↓
    Web UI Display
```

### Service Communication Flow

```
Web UI Server
    ↕ (HTTP/SSE)
MCP Servers
    ↕ (stdio/HTTP)
External Services
    ↕ (CLI/API)
Hammerspace Storage
Kubernetes Cluster
Milvus Database
```

## Integration Points

### Hammerspace Integration
- **HSTK CLI**: Direct command execution for all operations
- **NFS Mounts**: File system monitoring and operations
- **Tag Management**: Custom tag application and retrieval
- **Objective Management**: Tier promotion/demotion operations

### Kubernetes Integration
- **Job Deployment**: Automatic PDF/file processing jobs
- **ConfigMaps**: File lists and configuration
- **PVC Integration**: Persistent storage for processing
- **Path Mapping**: Container path translation

### Milvus Integration
- **Collection Management**: Dynamic collection creation
- **Vector Storage**: Embedding storage and retrieval
- **Semantic Search**: Vector similarity search
- **Metadata Management**: File metadata storage

### External API Integration
- **Anthropic Claude**: Natural language processing
- **NVIDIA API**: Optional AI features
- **Hammerspace API**: Storage operations

## Service Dependencies

### Core Dependencies
- **Python 3.8+**: Runtime environment
- **Screen**: Session persistence
- **Hammerspace HSTK CLI**: Storage operations
- **Anthropic API Key**: Natural language processing

### Optional Dependencies
- **Milvus Database**: Vector database operations
- **Kubernetes Cluster**: File processing
- **NVIDIA API Key**: AI features

### System Dependencies
- **Linux System**: Ubuntu 20.04+ recommended
- **NFS 4.2**: File system monitoring
- **Systemd**: Optional auto-start capability

## Security Considerations

### API Security
- **API Key Management**: Secure storage of API keys
- **Access Control**: Restricted service access
- **Network Security**: Port-based access control

### Data Security
- **File Encryption**: Hammerspace native encryption
- **Access Logging**: Comprehensive audit trails
- **Secure Communication**: HTTPS for web interface

### System Security
- **User Permissions**: Restricted service execution
- **Process Isolation**: Screen session isolation
- **Log Security**: Secure log file handling

## Performance Characteristics

### File Processing Performance
- **Polling Interval**: 5 seconds (fast), 30 seconds (retroactive)
- **Batch Processing**: 15-second event batching
- **Folder Tagging**: 40x performance improvement with recursive operations
- **Multi-format Support**: 13 supported file types

### Service Performance
- **Auto-restart**: 5-second restart delay
- **Health Monitoring**: Real-time status checking
- **Log Management**: Automatic log rotation
- **Memory Management**: Efficient resource utilization

### Scalability
- **Horizontal Scaling**: Multiple file monitor instances
- **Vertical Scaling**: Resource optimization
- **Load Balancing**: Service distribution
- **Caching**: In-memory file tracking

## Monitoring and Observability

### Service Monitoring
- **Health Checks**: Port and process monitoring
- **Status Dashboard**: Real-time service status
- **Log Aggregation**: Centralized logging
- **Error Tracking**: Comprehensive error handling

### File Monitoring
- **Event Streaming**: Real-time file events
- **Progress Tracking**: Processing status
- **Performance Metrics**: Processing statistics
- **Alert System**: Notification system

### System Monitoring
- **Resource Usage**: CPU, memory, disk
- **Network Monitoring**: Port and connection status
- **Dependency Health**: External service status
- **Performance Metrics**: System performance

## Deployment Architecture

### Development Environment
- **Local Services**: All services on single machine
- **Screen Sessions**: Development persistence
- **Debug Logging**: Verbose logging enabled
- **Hot Reloading**: Development-friendly restarts

### Production Environment
- **Systemd Integration**: Service management
- **Auto-start**: Boot-time service startup
- **Resource Limits**: Production resource constraints
- **Security Hardening**: Production security measures

### Container Deployment (Future)
- **Docker Containers**: Service containerization
- **Kubernetes Deployment**: Orchestrated deployment
- **Service Mesh**: Advanced networking
- **CI/CD Integration**: Automated deployment

## Troubleshooting Architecture

### Error Handling
- **Graceful Degradation**: Service failure handling
- **Automatic Recovery**: Self-healing capabilities
- **Error Logging**: Comprehensive error tracking
- **Fallback Mechanisms**: Alternative operation paths

### Debug Capabilities
- **Debug Logging**: Verbose operation logging
- **Service Attach**: Direct service access
- **Log Streaming**: Real-time log viewing
- **Status Monitoring**: Service health tracking

### Recovery Procedures
- **Service Restart**: Automatic restart capability
- **Mount Refresh**: NFS mount recovery
- **Data Recovery**: File processing recovery
- **System Recovery**: Full system recovery

## Future Architecture Considerations

### Planned Enhancements
- **Kubernetes MCP Server**: Full Kubernetes integration
- **Advanced Monitoring**: Prometheus/Grafana integration
- **Microservices**: Service decomposition
- **API Gateway**: Centralized API management

### Scalability Improvements
- **Distributed Processing**: Multi-node processing
- **Load Balancing**: Service load distribution
- **Caching Layer**: Performance optimization
- **Database Scaling**: Milvus clustering

### Security Enhancements
- **Authentication**: User authentication system
- **Authorization**: Role-based access control
- **Encryption**: End-to-end encryption
- **Audit Logging**: Comprehensive audit trails

---

**MCP 1.5 Architecture** - Production-ready Hammerspace storage management with natural language interface and automatic file ingestion.

