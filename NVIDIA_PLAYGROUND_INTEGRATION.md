# NVIDIA Playground Integration Guide

## Overview
This guide explains how to use the MCP server with NVIDIA Playground for natural language-based storage management.

## Prerequisites
- NVIDIA Playground access
- NVIDIA API Key: `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`
- MCP server running on the jump host
- Hammerspace storage system accessible

## MCP Server Configuration

### Environment Variables (.env file)
```bash
# NVIDIA API Configuration
NVIDIA_API_KEY=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

# Hammerspace Configuration
HAMMERSPACE_BASE_URL=https://10.200.10.120:8443/mgmt/v1.2/rest/
HAMMERSPACE_USERNAME=admin
HAMMERSPACE_PASSWORD=H@mmerspace123!
HAMMERSPACE_VERIFY_SSL=false
HAMMERSPACE_TIMEOUT=30

# Logging Configuration
LOG_LEVEL=INFO
```

### Start the MCP Server
```bash
cd /home/mike/mcp-1.5
source venv/bin/activate
python src/aiq_hstk_mcp_server.py
```

The server will start in stdio mode and communicate via standard input/output with NVIDIA Playground.

## Available Tools

### 1. Tag Management

#### `tag_directory_recursive`
Tag all files in a directory recursively.

**Natural Language Example:**
> "Tag all files in /mnt/se-lab/modelstore/model-v2/ as modelsetid=hs-GTC-0002"

**Parameters:**
- `path`: Directory path (e.g., `/mnt/se-lab/modelstore/model-v2/`)
- `tag_name`: Tag name (e.g., `user.modelsetid`)
- `tag_value`: Tag value (e.g., `hs-GTC-0002`)

**Response:**
```json
{
  "success": true,
  "message": "Successfully tagged all files in /mnt/se-lab/modelstore/model-v2/ with user.modelsetid=hs-GTC-0002",
  "path": "/mnt/se-lab/modelstore/model-v2/",
  "tag_name": "user.modelsetid",
  "tag_value": "hs-GTC-0002"
}
```

### 2. Objective Management

#### `apply_objective_to_path`
Apply a Hammerspace objective to move data to specific tiers.

**Natural Language Examples:**

**For Tier 1 (default working tier):**
> "Apply placeonvolumes objective to /mnt/se-lab/modelstore/model-v2/ so files are on tier1"

**For Tier 0 (high-performance tier):**
> "Apply place-on-tier0 objective to /mnt/se-lab/modelstore/critical-models/"

**Parameters:**
- `objective_name`: Objective to apply
  - `placeonvolumes` - Move to Tier 1 (default working tier)
  - `place-on-tier0` - Move to Tier 0 (high-performance tier)
- `path`: Directory path

**Response:**
```json
{
  "success": true,
  "message": "Successfully applied objective 'placeonvolumes' to /mnt/se-lab/modelstore/model-v2/",
  "objective_name": "placeonvolumes",
  "path": "/mnt/se-lab/modelstore/model-v2/"
}
```

#### `remove_objective_from_path`
Remove an objective from a path.

**Natural Language Example:**
> "Remove the place-on-tier0 objective from /mnt/se-lab/modelstore/test-models/"

**Parameters:**
- `objective_name`: Objective to remove
- `path`: Directory path

#### `list_objectives_for_path`
List all objectives applied to a path.

**Natural Language Example:**
> "What objectives are applied to /mnt/se-lab/modelstore/gtc-demo-models/?"

**Parameters:**
- `path`: Directory path

**Response:**
```json
{
  "success": true,
  "objectives": "SLOS_TABLE{\n\t|OBJECTIVE = SLO('placeonvolumes'), \n\t|COUNT = EXPRESSION(TRUE);\n\t...\n}",
  "path": "/mnt/se-lab/modelstore/gtc-demo-models/"
}
```

### 3. Alignment Checking

#### `check_tagged_files_alignment`
Check if files with a specific tag are aligned to their intended tier.

**Natural Language Example:**
> "Are the files tagged with user.project GTC aligned?"

**Parameters:**
- `tag_name`: Tag name to check
- `tag_value`: Tag value (optional)
- `share_path`: Path to check (default: `/mnt/se-lab/modelstore/gtc-demo-models/`)
- `max_files_to_check`: Maximum files to check (default: 50)

**Response:**
```json
{
  "success": true,
  "alignment_status": "ALIGNED",
  "message": "All 23 checked files are aligned",
  "files_checked": 23,
  "tag_name": "user.project"
}
```

### 4. File Discovery

#### `list_files_by_tag`
List all files that have a specific tag.

**Natural Language Example:**
> "List all files tagged with user.modelsetid=hs-GTC-0002"

**Parameters:**
- `tag_name`: Tag name to search for
- `tag_value`: Tag value (optional)
- `share_uuid`: Share UUID (optional - searches all shares if not provided)

## Common Workflows

### Workflow 1: Tag and Move to Tier 1 (Default Working Tier)

**Natural Language Request:**
> "Tag all files in /mnt/se-lab/modelstore/new-models/ as modelsetid=hs-GTC-0003 and put them on tier1 using placeonvolumes"

**Steps the MCP server will execute:**
1. `tag_directory_recursive`:
   - path: `/mnt/se-lab/modelstore/new-models/`
   - tag_name: `user.modelsetid`
   - tag_value: `hs-GTC-0003`

2. `apply_objective_to_path`:
   - objective_name: `placeonvolumes`
   - path: `/mnt/se-lab/modelstore/new-models/`

3. `check_tagged_files_alignment`:
   - tag_name: `user.modelsetid`
   - tag_value: `hs-GTC-0003`
   - share_path: `/mnt/se-lab/modelstore/new-models/`

### Workflow 2: Move Critical Models to Tier 0

**Natural Language Request:**
> "Tag all files in /mnt/se-lab/modelstore/production/ as priority=critical and move them to tier0"

**Steps:**
1. `tag_directory_recursive`:
   - path: `/mnt/se-lab/modelstore/production/`
   - tag_name: `user.priority`
   - tag_value: `critical`

2. `apply_objective_to_path`:
   - objective_name: `place-on-tier0`
   - path: `/mnt/se-lab/modelstore/production/`

### Workflow 3: Check Status and Alignment

**Natural Language Request:**
> "What objectives are applied to /mnt/se-lab/modelstore/gtc-demo-models/ and are those files aligned?"

**Steps:**
1. `list_objectives_for_path`:
   - path: `/mnt/se-lab/modelstore/gtc-demo-models/`

2. `check_tagged_files_alignment`:
   - tag_name: `user.project`
   - tag_value: `gtc-model-demo-0001`
   - share_path: `/mnt/se-lab/modelstore/gtc-demo-models/`

## NVIDIA Playground Integration

### Connecting to the MCP Server

1. **Access NVIDIA Playground**:
   - Go to [NVIDIA Playground](https://playground.nvidia.com)
   - Sign in with your NVIDIA account

2. **Configure MCP Connection**:
   - Navigate to Settings → Integrations → MCP
   - Add new MCP server configuration:

```json
{
  "mcpServers": {
    "hammerspace-mcp": {
      "command": "ssh",
      "args": [
        "jumphost",
        "cd /home/mike/mcp-1.5 && source venv/bin/activate && python src/aiq_hstk_mcp_server.py"
      ],
      "env": {
        "NVIDIA_API_KEY": "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"
      }
    }
  }
}
```

3. **Alternative: Local Network Connection**:
   If NVIDIA Playground supports HTTP-based MCP servers, you can expose the server via HTTP (future enhancement).

### Natural Language Examples

Once connected, you can use natural language in NVIDIA Playground:

#### Example 1: Basic Tagging and Tier Placement
```
You: Tag all files in /modelstore/modeldir as modelsetid=hs-GTC-0002 
     and apply placeonvolumes so they are on tier1
```

The MCP server will:
- Tag all files recursively
- Apply the `placeonvolumes` objective
- Return success confirmation

#### Example 2: Check Status
```
You: What's the status of files tagged with modelsetid=hs-GTC-0002?
```

The MCP server will:
- List files with that tag
- Check alignment status
- Report results

#### Example 3: Move to High-Performance Tier
```
You: I need all files in /modelstore/critical-models/ on tier0 for performance
```

The MCP server will:
- Apply `place-on-tier0` objective
- Monitor alignment
- Confirm when complete

#### Example 4: Remove from Tier
```
You: Take all GTC files off tier0 and put them on tier1
```

The MCP server will:
- Remove `place-on-tier0` objective
- Apply `placeonvolumes` objective
- Verify alignment

## Tier Strategy

### Default Working Tier: Tier 1
- **Objective**: `placeonvolumes`
- **Use Case**: Default storage for model files and datasets
- **Characteristics**: Balanced performance and capacity

### High-Performance Tier: Tier 0
- **Objective**: `place-on-tier0`
- **Use Case**: Critical models requiring fastest access
- **Characteristics**: Highest performance, limited capacity

## Troubleshooting

### Server Not Responding
```bash
# Check if server is running
ps aux | grep aiq_hstk_mcp_server

# Restart server
pkill -f aiq_hstk_mcp_server.py
cd /home/mike/mcp-1.5 && source venv/bin/activate && python src/aiq_hstk_mcp_server.py
```

### Check Server Logs
```bash
tail -f /home/mike/mcp-1.5/logs/aiq_hstk_mcp_server.log
```

### Verify Tools Are Available
```bash
cd /home/mike/mcp-1.5
source venv/bin/activate
python test_new_tools.py
```

## Security Notes

- The NVIDIA API key is stored in the `.env` file
- Hammerspace credentials are also in `.env`
- Ensure proper file permissions: `chmod 600 .env`
- The MCP server runs with the permissions of the user running it

## Support

For issues or questions:
1. Check server logs: `/home/mike/mcp-1.5/logs/aiq_hstk_mcp_server.log`
2. Verify Hammerspace connectivity
3. Ensure NVIDIA API key is valid
4. Test tools directly using `test_new_tools.py`

