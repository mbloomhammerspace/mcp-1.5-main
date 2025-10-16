# Hammerspace MCP Web UI

A beautiful web-based interface for interacting with Hammerspace MCP services using natural language, powered by Anthropic's Claude AI.

## 🌟 Features

- **Natural Language Interface**: Use plain English to control your Hammerspace storage
- **Claude AI Integration**: Powered by Anthropic's Claude 3.5 Sonnet for intelligent tool selection
- **Real-time MCP Tool Execution**: Direct integration with all 19 MCP tools
- **Beautiful Modern UI**: Clean, responsive design with smooth animations
- **Conversation History**: Maintains context across multiple requests

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/mike/mcp-1.5/web_ui
pip install -r requirements.txt
```

### 2. Configure Anthropic API Key

Add your Anthropic API key to the `.env` file in the project root:

```bash
cd /home/mike/mcp-1.5
nano .env
```

Add this line (replace with your actual key):
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Get your API key from: https://console.anthropic.com/

### 3. Start the Web UI

```bash
cd /home/mike/mcp-1.5/web_ui
python app.py
```

### 4. Open in Browser

Navigate to: **http://localhost:5000**

## 💬 Example Commands

Try these natural language commands (using share-relative paths):

- "Tag all files in /modelstore/nvidia-test-thurs as modelsetid=mynvidiademo"
- "Promote all modelsetid=mynvidiademo tagged files to tier0"
- "Check alignment status of files tagged with modelsetid=mynvidiademo"
- "Remove the Place-on-tier0 objective from /modelstore/nvidia-test-thurs"
- "List all objectives for /modelstore/gtc-demo-models"
- "Apply placeonvolumes objective to /modelstore/incoming-models"
- "Refresh Hammerspace mounts"
- "Find new files in /modelstore/ from the last 60 minutes, tag them as modelsetid=hs-GTC-0001, and place on tier1"

**Note**: Paths like `/modelstore/dir` are automatically converted to `/mnt/se-lab/modelstore/dir`

## 🛠️ How It Works

1. **User Input**: You type a natural language command
2. **Claude AI**: Analyzes your request and selects the appropriate MCP tool(s)
3. **MCP Server**: Executes the tool via the stdio MCP protocol
4. **Hammerspace**: Performs the actual storage operation
5. **Response**: Claude formats and presents the results in natural language

## 🏗️ Architecture

```
┌─────────────┐
│  Web UI     │  Flask + HTML/CSS/JS
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Claude AI  │  Anthropic API
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ MCP Client  │  Python MCP SDK
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ MCP Server  │  aiq_hstk_mcp_server.py
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Hammerspace │  HSTK CLI (hs command)
└─────────────┘
```

## 📋 Available MCP Tools

The Web UI has access to all MCP tools (using real HSTK CLI operations):

### Core Tools
1. **`tag_directory_recursive`** - Tag all files recursively (uses `hs tag set -r`)
2. **`check_tagged_files_alignment`** - Find files by tag and check alignment
3. **`apply_objective_to_path`** - Apply tier objectives (uses `hs objective add`)
4. **`remove_objective_from_path`** - Remove objectives (uses `hs objective delete`)
5. **`list_objectives_for_path`** - List objectives (uses `hs objective list`)
6. **`ingest_new_files`** - Find new files by time, tag, and tier
7. **`refresh_mounts`** - Refresh NFS mounts to fix stale file handles

**All operations use real Hammerspace CLI commands - no mock or simulated data.**

## 🔧 Configuration

### Environment Variables

Create/edit `/home/mike/mcp-1.5/.env`:

```bash
NVIDIA_API_KEY=nvapi-...
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Server Settings

Edit `web_ui/app.py` to change:

- **Port**: Default is `5000`
- **Host**: Default is `0.0.0.0` (all interfaces)
- **Model**: Default is `claude-3-5-sonnet-20241022`

## 🎯 Use Cases

### Demo Scenario 1: File Promotion
**Command**: "Promote all GTC tagged objects to tier0"

**What happens**:
1. Claude identifies this needs the `apply_objective_to_path` tool
2. Determines the objective is "Place-on-tier0"
3. Finds the GTC directory path
4. Executes the MCP tool
5. Returns success confirmation

### Demo Scenario 2: Alignment Check
**Command**: "Check if my GTC files are aligned"

**What happens**:
1. Claude uses `check_tagged_files_alignment` tool
2. Checks files with GTC tag
3. Reports alignment status (ALIGNED/PARTIALLY ALIGNED/MISALIGNED)
4. Exits early if any misalignment found

### Demo Scenario 3: New File Ingestion
**Command**: "Ingest new files from the model store"

**What happens**:
1. Claude uses `ingest_new_files` tool
2. Finds files modified in last 60 minutes
3. Tags them with specified tag
4. Applies placeonvolumes objective
5. Reports number of files processed

## 🔍 Troubleshooting

### Web UI won't start
- Check that port 5000 is not in use: `netstat -tlnp | grep 5000`
- Verify dependencies are installed: `pip list | grep -E 'flask|anthropic|mcp'`
- Check .env file has ANTHROPIC_API_KEY

### Claude returns errors
- Verify your Anthropic API key is valid
- Check API quota/limits at https://console.anthropic.com/
- Review the console logs for detailed error messages

### MCP tools fail
- Ensure MCP server is accessible
- Check that Hammerspace mounts are available
- Verify HSTK CLI is configured: `/home/mike/hs-mcp-1.0/.venv/bin/hs --version`

### Browser console errors
- Check browser console (F12) for JavaScript errors
- Ensure you're accessing via HTTP not HTTPS
- Try clearing browser cache

## 📊 Logging

The web UI logs to console. To save logs:

```bash
python app.py > web_ui.log 2>&1
```

## 🚀 Production Deployment

For production use:

1. Use a production WSGI server:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. Set up HTTPS with nginx reverse proxy

3. Use environment-specific .env files

4. Enable rate limiting and authentication

## 📝 License

Part of the MCP 1.5 project.

