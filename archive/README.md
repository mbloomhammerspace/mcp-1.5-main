# Archive Directory

This directory contains obsolete files from the MCP 1.5 → 1.7 development effort.

## Directory Structure

### `old_servers/`
**Why archived**: Multiple MCP server iterations that were replaced by `src/aiq_hstk_mcp_server.py`

Contains 10 obsolete server implementations:
- `aiq_mcp_server.py` - Early AIQ Toolkit integration attempt
- `fastmcp_server.py` - FastMCP framework experiment
- `hstk_mcp_server.py` - HSTK-only implementation
- `http_mcp_server.py` - HTTP transport experiment
- `real_hammerspace_mcp_server.py` - Attempted "real" API (still had mock data)
- `simple_hstk_mcp_server.py` - Simplified HSTK version
- `volume_canvas_mcp_server.py` - Volume Canvas specific server
- `working_hstk_mcp_server.py` - Another working iteration
- `docs_api_server.py` - Documentation API server
- `mcp_docs_service.py` - Documentation service

**Replacement**: `src/aiq_hstk_mcp_server.py` (the final, working version)

### `old_scripts/`
**Why archived**: Demo and test scripts replaced by MCP tools

Contains 7 obsolete scripts:
- `start_aiq_mcp_server.py` - Old startup script (now use direct python command)
- `start_nat_mcp_server.py` - NAT-specific startup
- `start_simple_mcp_server.py` - Simple server startup
- `complete_ingestion_workflow.py` - Old ingestion workflow (replaced by `ingest_new_files` MCP tool)
- `tag_to_objectives_demo.py` - Demo workflow
- `test_extended_features.py` - Feature testing
- `test_harness.py` - Test harness

**Replacement**: MCP tools handle everything now

### `old_docs/`
**Why archived**: Development progress documentation superseded by final docs

Contains 8 summary documents:
- `AIQ_HSTK_INTEGRATION_SUMMARY.md` - Integration progress notes
- `AIQ_SUCCESS_SUMMARY.md` - Success milestone doc
- `EXTENDED_FEATURES_SUMMARY.md` - Feature list
- `TAG_GUIDES_SUMMARY.md` - Tag guide summary
- `TEST_EXECUTION_REPORT.md` - Test results
- `TEST_RUNNER_README.md` - Test runner docs
- `TEST_VALIDATION_SUMMARY.md` - Validation summary
- `PROJECT_SUMMARY.md` - Project overview

**Replacement**: 
- `IMPLEMENTATION_COMPLETE.md` - Complete technical summary
- `NVIDIA_PLAYGROUND_INTEGRATION.md` - Integration guide
- `docs/` directory - Detailed guides

### `old_configs/`
**Why archived**: Config files for different framework attempts

Contains 4 YAML config files:
- `minimal_nat_config.yml` - Minimal NAT config
- `simple_volume_canvas_nat_config.yml` - Simple config
- `volume_canvas_nat_config.yml` - Full Volume Canvas config
- `aiq_volume_canvas_config.yml` - AIQ config

**Replacement**: `.env` file for all configuration

### `old_tests/`
**Why archived**: Tests for obsolete server versions

Contains:
- `test_extended_features.py` - Extended feature tests
- `test_volume_canvas_mcp_server.py` - Server-specific tests
- `test_mcp_client.py` - Old MCP client test
- `run_tests.sh` - Test runner script
- `reports/` - Old test reports

**Replacement**: Direct MCP server testing via NVIDIA Playground

## Current Active Files (Not Archived)

### Core Server
- `src/aiq_hstk_mcp_server.py` - **THE** MCP server (only one needed)

### Supporting Components
- `src/hammerspace_client.py` - HSTK client
- `src/models.py` - Data models
- `src/config.py` - Configuration manager
- `src/logging_config.py` - Logging setup
- `src/operations/` - HSTK operations (visibility, movement, storage, catalog)
- `src/volume_movement_manager.py` - Volume management

### Documentation
- `IMPLEMENTATION_COMPLETE.md` - Complete technical summary
- `NVIDIA_PLAYGROUND_INTEGRATION.md` - Integration guide
- `README.md` - Main readme
- `docs/` - Detailed guides (all kept)

### Configuration
- `.env` - Environment configuration (NVIDIA API key, Hammerspace credentials)
- `requirements.txt` - Python dependencies
- `install.sh` - Installation script
- `start_server.sh` / `stop_server.sh` - Server management

### Utilities
- `mount_script.sh` - NFS mount script
- `fstab_entries.txt` - All NFS mounts
- `fstab_essential.txt` - Essential mounts only

## Archive Date
October 8, 2025

## Notes
These files are preserved for historical reference and can be safely deleted if disk space is needed. The current implementation in `src/aiq_hstk_mcp_server.py` supersedes all archived servers.

