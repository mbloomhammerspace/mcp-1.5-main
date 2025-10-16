# MCP 1.7 Project Structure

## Core Files (Production)

### Main MCP Server
```
src/aiq_hstk_mcp_server.py    # THE MCP server with NVIDIA AIQ + HSTK integration
```

### HSTK Components
```
src/hammerspace_client.py      # Hammerspace API client
src/models.py                  # Data models (Share, File, Objective, etc.)
src/config.py                  # Configuration manager
src/logging_config.py          # Logging configuration
src/volume_movement_manager.py # Volume movement operations
src/__init__.py                # Package marker
```

### HSTK Operations
```
src/operations/
  ├── __init__.py              # Package marker
  ├── catalog.py               # Catalog operations
  ├── movement.py              # Data movement operations
  ├── storage.py               # Storage management operations
  └── visibility.py            # Data visibility operations
```

### Configuration
```
.env                           # Environment variables (NVIDIA API key, credentials)
requirements.txt               # Python dependencies
```

### Server Management
```
install.sh                     # Installation script
start_server.sh                # Start the MCP server
stop_server.sh                 # Stop the MCP server
```

### Documentation
```
README.md                                           # Main readme
IMPLEMENTATION_COMPLETE.md                          # Technical summary
NVIDIA_PLAYGROUND_INTEGRATION.md                    # NVIDIA Playground guide
docs/
  ├── GUIDES_INDEX.md                               # Guide index
  ├── INTEGRATION_GUIDE.md                          # Integration guide
  ├── TAG_SEARCH_GUIDE.md                          # Tag search guide
  ├── TAG_TO_OBJECTIVES_GUIDE.md                   # Tag to objectives workflow
  ├── TIER_MANAGEMENT_GUIDE.md                     # Tier management guide
  ├── VOLUME_CANVAS_FEATURES.md                    # Feature documentation
  └── REST API documentation - Development - Confluence.pdf
```

### Reference Materials
```
Hammerspace Objectives Guide v1.2 (1).pdf          # Hammerspace objectives reference
```

### Infrastructure
```
mount_script.sh                # NFS mount script
fstab_entries.txt              # All NFS mount entries
fstab_essential.txt            # Essential NFS mounts only
```

### Runtime
```
logs/                          # Server logs
pids/                          # Process IDs
venv/                          # Python virtual environment
```

## Archived Files

### `archive/`
Contains obsolete files from development iterations:
- `old_servers/` - 10 obsolete MCP server implementations
- `old_scripts/` - 7 demo and test scripts
- `old_docs/` - 8 progress summary documents
- `old_configs/` - 4 old YAML configuration files
- `old_tests/` - Test files and reports
- `README.md` - Archive documentation

### `tmp/`
Temporary files that can be safely deleted:
- `.fs_command_gateway *` - Hammerspace CLI temporary files

## MCP Server Tools (18 Total)

### Tag Management
1. `tag_directory_recursive` - Recursively tag files
2. `set_file_tag` - Set tag on individual file
3. `get_file_tags` - Get file tags
4. `list_files_by_tag` - Find files by tag

### Objective Management
5. `apply_objective_to_path` - Apply tier objectives
6. `remove_objective_from_path` - Remove objectives
7. `list_objectives_for_path` - List applied objectives
8. `apply_hs_objective` - Direct hs CLI objective apply
9. `remove_hs_objective` - Direct hs CLI objective remove
10. `create_objective` - HSTK API objective creation

### File Ingestion
11. `ingest_new_files` - Find new files, tag them, place on Tier 1

### Alignment Checking
12. `check_tagged_files_alignment` - Check if tagged files are aligned
13. `check_file_alignment` - Check single file alignment

### Share & File Management
14. `list_shares` - List all shares
15. `list_files` - List files in share

### Jobs & Analysis
16. `list_jobs` - List data movement jobs
17. `aiq_analyze_storage` - AI-powered storage analysis
18. `aiq_optimize_tiering` - AI-powered tier optimization

## Dependencies

See `requirements.txt` for full list. Key dependencies:
- `mcp>=1.12.4` - Model Context Protocol
- `aiqtoolkit>=1.1.0` - NVIDIA AIQ Toolkit
- `aiohttp>=3.9.0` - Async HTTP client
- `python-dotenv>=1.0.0` - Environment variables
- Full HSTK requirements

## Quick Start

1. Install:
   ```bash
   ./install.sh
   ```

2. Configure `.env` with your credentials

3. Start server:
   ```bash
   ./start_server.sh
   ```

4. Use with NVIDIA Playground or any MCP client

## Git History
- Commit `22807a6`: "initial mcp 1.7 effort" - Clean, lean implementation

