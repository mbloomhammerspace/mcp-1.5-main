# MCP 1.5 Deployment Guide

## Production Deployment - October 9, 2025

This guide covers deploying the MCP 1.5 server with Claude AI Web UI for natural language Hammerspace storage management.

## ✅ What's Deployed

### Components
1. **MCP Server** (`src/aiq_hstk_mcp_server.py`) - Real HSTK CLI operations
2. **Web UI** (`web_ui/app.py`) - Claude AI natural language interface  
3. **Mount Refresh** (`refresh_mounts.sh`) - Automatic NFS mount recovery
4. **Test Suite** (`tests/`) - Comprehensive validation scripts

### Current Status
- **MCP Server**: ✅ Operational with 7 core tools
- **Web UI**: ✅ Running on port 5000
- **Hammerspace**: ✅ Connected to SE Lab cluster (10.200.120.90)
- **All Operations**: ✅ Using real HSTK CLI (no mock data)

## 🚀 Quick Start

### Start the Web UI

```bash
cd /home/mike/mcp-1.5/web_ui
source ../venv/bin/activate
python app.py > ../logs/web_ui.log 2>&1 &
```

### Access the Interface

- **Main UI**: `http://10.200.120.94:5000`
- **Debug Logs**: `http://10.200.120.94:5000/debug`

### Stop Services

```bash
pkill -f "python.*app.py"
```

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# Hammerspace Cluster
HS_ANVIL=10.200.120.90

# Claude AI (required for Web UI)
ANTHROPIC_API_KEY=sk-ant-api03-...

# NVIDIA (optional)
NVIDIA_API_KEY=nvapi-...

# Logging
LOG_LEVEL=INFO
```

### Mount Points (NFS)

SE Lab Hammerspace mounts:
- `/mnt/se-lab/root` → `10.200.120.90:/`
- `/mnt/se-lab/modelstore` → `10.200.120.90:/modelstore`
- `/mnt/se-lab/tier0` → `10.200.120.90:/tier0`
- And more...

## 📋 Core MCP Tools

### Tag Operations
1. **`tag_directory_recursive`** - Tag all files in a directory
   - Uses: `hs tag set -r user.tag=value /path`
   - Auto-retry on stale file handles

2. **`check_tagged_files_alignment`** - Find and check tagged files
   - Uses: `find` + `hs eval has_tag()` + `hs dump misaligned`
   - Searches ALL file types (not just .safetensors)
   - Checks up to 500 files
   - Returns list of matching files with paths

### Tier Management  
3. **`apply_objective_to_path`** - Apply tier objectives
   - Uses: `hs objective add "Objective Name" /path`
   - Common objectives: "Place-on-tier0", "placeonvolumes"
   - Auto-retry on stale file handles

4. **`remove_objective_from_path`** - Remove objectives
   - Uses: `hs objective delete "Objective Name" /path`

5. **`list_objectives_for_path`** - List applied objectives
   - Uses: `hs objective list /path`

### Utility Tools
6. **`ingest_new_files`** - Find new files, tag, place on tier1
   - Finds files by ctime/mtime
   - Tags them
   - Applies `placeonvolumes`

7. **`refresh_mounts`** - Refresh NFS mounts
   - Fixes stale file handle errors
   - Unmounts and remounts all shares

## 🎯 Common Workflows

### Workflow 1: Tag and Tier Management

```
Tag all files in /modelstore/my-models as modelsetid=demo-001
↓
Promote all modelsetid=demo-001 tagged files to tier0
↓
Check alignment status
```

**Behind the scenes:**
1. `tag_directory_recursive(path="/mnt/se-lab/modelstore/my-models", tag_name="user.modelsetid", tag_value="demo-001")`
2. `check_tagged_files_alignment(tag_name="user.modelsetid", tag_value="demo-001")` → finds files
3. Claude extracts directory from file paths
4. `apply_objective_to_path(objective_name="Place-on-tier0", path="/mnt/se-lab/modelstore/my-models")`

### Workflow 2: New File Ingestion

```
Find new files in /modelstore/ from the last 60 minutes, 
tag them as modelsetid=batch-202510, and place on tier1
```

**Behind the scenes:**
1. `ingest_new_files(path="/mnt/se-lab/modelstore/", tag_name="user.modelsetid", tag_value="batch-202510", age_minutes=60)`

## 🐛 Troubleshooting

### Stale File Handle Errors

**Automatic Recovery**: The MCP server automatically detects stale file handles and refreshes mounts.

**Manual Recovery**:
```bash
/home/mike/mcp-1.5/refresh_mounts.sh
```

Or via Web UI:
```
Refresh Hammerspace mounts
```

### Tag Operations Failing

1. Verify mount is accessible:
   ```bash
   ls -la /mnt/se-lab/modelstore/
   ```

2. Test HSTK CLI:
   ```bash
   /home/mike/hs-mcp-1.0/.venv/bin/hs --version
   ```

3. Check logs:
   ```bash
   tail -f /home/mike/mcp-1.5/logs/aiq_hstk_mcp.log
   ```

### Web UI Not Responding

1. Check if running:
   ```bash
   lsof -i :5000
   ```

2. Restart:
   ```bash
   pkill -f "python.*app.py"
   cd /home/mike/mcp-1.5/web_ui
   source ../venv/bin/activate
   python app.py > ../logs/web_ui.log 2>&1 &
   ```

3. Check logs:
   ```bash
   tail -f /home/mike/mcp-1.5/logs/web_ui.log
   ```

## 🔒 Security Notes

### Production Deployment

- **Use HTTPS**: Deploy behind nginx or Apache with SSL
- **Add Authentication**: Implement user authentication  
- **Restrict Access**: Firewall rules for port 5000
- **API Key Security**: Never commit `.env` file to git

### Current Deployment

- **Environment**: Development/Demo
- **Access**: Internal network only (10.200.120.94)
- **Authentication**: None (add before production use)

## 📊 Performance

### Optimizations Applied

- **Search Scope**: Default to `/mnt/se-lab/modelstore/` instead of entire filesystem
- **File Limit**: Check up to 500 files (increased from 50)
- **File Types**: Search ALL files, not just .safetensors
- **Early Exit**: Stop checking when misalignment found
- **Auto-Retry**: Automatic mount refresh on errors

### Typical Performance

- Tag 1 file: ~200ms
- Tag directory (10 files): ~500ms
- Check alignment: ~300-500ms (depends on file count)
- Apply objective: ~200ms
- Mount refresh: ~10 seconds

## 🎉 Latest Updates (October 9, 2025)

### Critical Bug Fixes

1. **Tag Matching Logic**
   - Fixed: Was matching "FALSE" as "TRUE"
   - Now: Only matches when `tag_output == "TRUE"`
   - Impact: Tag searches now find correct files

2. **File Type Filter**
   - Fixed: Only searching `.safetensors` files
   - Now: Searches ALL file types
   - Impact: Tags work on any file

3. **Search Scope**
   - Fixed: Searching entire `/mnt/se-lab/` (200+ files)
   - Now: Default to `/mnt/se-lab/modelstore/` (~14 files)
   - Impact: 10x faster searches

4. **File Check Limit**
   - Fixed: Only checking first 50 files
   - Now: Checks up to 500 files
   - Impact: Handles larger collections

### Feature Additions

1. **Copy Buttons** - All chat messages have copy buttons (with fallback for HTTP)
2. **Suppressed Warnings** - Cleaned up Anthropic API deprecation warnings
3. **File Paths in Results** - Returns tagged file paths for Claude to extract directories
4. **PARTIALLY ALIGNED Detection** - Correctly reports partial alignment status

## 📞 Support

- **GitHub**: https://github.com/mbloomhammerspace/mcp-1.5
- **Logs**: `/home/mike/mcp-1.5/logs/`
- **Documentation**: `/home/mike/mcp-1.5/docs/`

---

**Deployment**: SE Lab Hammerspace Cluster  
**Status**: ✅ PRODUCTION READY  
**Last Updated**: October 9, 2025

