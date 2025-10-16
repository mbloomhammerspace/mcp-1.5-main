# MCP 1.5 Server Integration Guide

This guide explains how to register and use the MCP 1.5 Server with different AI applications and development environments.

## 📋 Table of Contents

- [Cursor IDE Integration](#cursor-ide-integration)
- [Windsurf IDE Integration](#windsurf-ide-integration)
- [NVIDIA Playground Integration](#nvidia-playground-integration)
- [Claude Desktop Integration](#claude-desktop-integration)
- [Custom Application Integration](#custom-application-integration)
- [Troubleshooting](#troubleshooting)

## 🎯 Cursor IDE Integration

### Prerequisites
- Cursor IDE installed
- MCP 1.5 Server running
- Python 3.8+ environment

### Configuration Steps

1. **Open Cursor Settings**:
   - Press `Cmd/Ctrl + ,` to open settings
   - Search for "MCP" or "Model Context Protocol"

2. **Add MCP Server Configuration**:
   ```json
   {
     "mcpServers": {
       "hammerspace": {
         "command": "python",
         "args": [
           "/home/mike/mcp-1.5/src/aiq_hstk_mcp_server.py"
         ],
         "env": {
           "PYTHONPATH": "/home/mike/mcp-1.5",
           "HS_ANVIL": "10.200.120.90"
         }
       }
     }
   }
   ```

3. **With NVIDIA API Key (Optional)**:
   ```json
   {
     "mcpServers": {
       "hammerspace": {
         "command": "python",
         "args": [
           "/home/mike/mcp-1.5/src/aiq_hstk_mcp_server.py"
         ],
         "env": {
           "PYTHONPATH": "/home/mike/mcp-1.5",
           "HS_ANVIL": "10.200.120.90",
           "NVIDIA_API_KEY": "your_nvidia_api_key_here"
         }
       }
     }
   }
   ```

4. **Restart Cursor**:
   - Completely close and restart Cursor
   - The MCP server should now be available

### Testing the Integration

Ask Cursor questions like:
- "Tag all files in /modelstore/my-models as modelsetid=test123"
- "Check alignment of files tagged with modelsetid=test123"
- "Promote files in /modelstore/my-models to tier0"
- "List objectives for /modelstore/my-models"
- "Refresh Hammerspace mounts"

## 🌊 Windsurf IDE Integration

### Prerequisites
- Windsurf IDE installed
- MCP 1.5 Server running
- Python 3.8+ environment

### Configuration Steps

1. **Open Windsurf Settings**:
   - Go to Settings → Extensions → MCP
   - Or use the command palette: `Ctrl+Shift+P` → "MCP: Configure"

2. **Add MCP Server Configuration**:
   ```json
   {
     "mcpServers": {
       "mcp-1.5": {
         "command": "python",
         "args": [
           "/home/mike/mcp-1.5/src/aiq_hstk_mcp_server.py"
         ],
         "env": {
           "PYTHONPATH": "/home/mike/mcp-1.5",
           "NVIDIA_API_KEY": "your_nvidia_api_key_here"
         }
       }
     }
   }
   ```

3. **Network Configuration (if using remote server)**:
   ```json
   {
     "mcpServers": {
       "mcp-1.5": {
         "command": "curl",
         "args": [
           "-X", "POST",
           "http://your-server:9901/mcp",
           "-H", "Content-Type: application/json",
           "-d", "{}"
         ],
         "env": {}
       }
     }
   }
   ```

4. **Restart Windsurf**:
   - Close and restart Windsurf
   - Check the MCP status in the status bar

### Testing the Integration

Use Windsurf's AI features to:
- Query storage volumes and file systems
- Perform data management operations
- Monitor system status and jobs

## 🎮 NVIDIA Playground Integration

### Prerequisites
- NVIDIA Playground access
- MCP 1.5 Server running with NVIDIA AI Q integration
- Valid NVIDIA API key

### Configuration Steps

1. **Access NVIDIA Playground**:
   - Go to [NVIDIA Playground](https://playground.nvidia.com)
   - Sign in with your NVIDIA account

2. **Configure MCP Connection**:
   - Navigate to Settings → Integrations → MCP
   - Add new MCP server configuration

3. **Server Configuration**:
   ```json
   {
     "name": "mcp-1.5",
     "type": "mcp",
     "endpoint": "http://your-server:9901/mcp",
     "authentication": {
       "type": "api_key",
       "key": "your_nvidia_api_key_here"
     },
     "capabilities": [
       "volume_management",
       "file_operations",
       "tag_search",
       "tier_management",
       "objective_application"
     ]
   }
   ```

4. **Test Connection**:
   - Use the "Test Connection" button
   - Verify all capabilities are recognized

### Using with NVIDIA Playground

1. **Start a New Session**:
   - Create a new playground session
   - Select "MCP Integration" mode

2. **Available Commands**:
   - `@mcp-1.5 list_volumes` - List storage volumes
   - `@mcp-1.5 search_files_by_tag` - Search by tags
   - `@mcp-1.5 place_on_tier` - Move to tier
   - `@mcp-1.5 get_system_status` - System health

3. **AI-Powered Workflows**:
   - Use natural language to describe data management tasks
   - Let NVIDIA's AI orchestrate complex operations
   - Monitor results through the playground interface

## 🤖 Claude Desktop Integration

### Prerequisites
- Claude Desktop installed
- MCP 1.5 Server running
- Python 3.8+ environment

### Configuration Steps

1. **Locate Claude Desktop Config**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add MCP Server Configuration**:
   ```json
   {
     "mcpServers": {
       "mcp-1.5": {
         "command": "python",
         "args": [
           "/home/mike/mcp-1.5/src/aiq_hstk_mcp_server.py"
         ],
         "env": {
           "PYTHONPATH": "/home/mike/mcp-1.5",
           "NVIDIA_API_KEY": "your_nvidia_api_key_here"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**:
   - Close and restart Claude Desktop
   - The MCP server should be available in conversations

### Testing the Integration

Start a conversation with Claude and ask:
- "Can you show me the volumes in my storage system?"
- "Help me find all files tagged with 'user.priority=high'"
- "Move all model files to the hot storage tier"

## 🔧 Custom Application Integration

### Python Client Example

```python
import asyncio
from mcp import ClientSession, StdioClientParameters

async def main():
    # Connect to MCP server
    async with ClientSession(
        StdioClientParameters(
            command="python",
            args=["/home/mike/mcp-1.5/src/aiq_hstk_mcp_server.py"],
            env={"PYTHONPATH": "/home/mike/mcp-1.5"}
        )
    ) as session:
        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {[tool.name for tool in tools.tools]}")
        
        # Call a tool
        result = await session.call_tool("list_volumes", {})
        print(f"Volumes: {result.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### HTTP Client Example

```python
import httpx
import asyncio

async def call_mcp_tool(tool_name: str, arguments: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:9901/mcp",
            json={
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
        )
        return response.json()

# Example usage
async def main():
    volumes = await call_mcp_tool("list_volumes", {})
    print(f"Volumes: {volumes}")

asyncio.run(main())
```

### JavaScript/Node.js Client Example

```javascript
const { spawn } = require('child_process');
const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');

async function connectToMCPServer() {
    const transport = new StdioClientTransport({
        command: 'python',
        args: ['/home/mike/mcp-1.5/src/aiq_hstk_mcp_server.py'],
        env: { PYTHONPATH: '/home/mike/mcp-1.5' }
    });
    
    const client = new Client({
        name: 'mcp-1.5-client',
        version: '1.0.0'
    }, {
        capabilities: {}
    });
    
    await client.connect(transport);
    
    // List available tools
    const tools = await client.listTools();
    console.log('Available tools:', tools.tools.map(t => t.name));
    
    // Call a tool
    const result = await client.callTool('list_volumes', {});
    console.log('Volumes:', result.content);
    
    await client.close();
}

connectToMCPServer().catch(console.error);
```

## 🔍 Troubleshooting

### Common Issues

#### 1. MCP Server Not Found
**Problem**: Application can't find the MCP server
**Solution**:
- Verify the server is running: `sudo systemctl status mcp-1.5`
- Check the path in configuration is correct
- Ensure Python environment is properly set up

#### 2. Permission Denied
**Problem**: Permission errors when starting the server
**Solution**:
```bash
sudo chown -R $USER:$USER /home/mike/mcp-1.5
chmod +x /home/mike/mcp-1.5/src/aiq_hstk_mcp_server.py
```

#### 3. Environment Variables Not Set
**Problem**: NVIDIA_API_KEY or other env vars not recognized
**Solution**:
- Check `.env` file exists and is properly formatted
- Verify environment variables in the MCP configuration
- Restart the application after changing environment

#### 4. Port Already in Use
**Problem**: Port 9901 is already in use
**Solution**:
```bash
sudo netstat -tlnp | grep 9901
sudo systemctl stop mcp-1.5
# Or change the port in configuration
```

#### 5. Connection Timeout
**Problem**: Applications timeout when connecting
**Solution**:
- Check firewall settings
- Verify server is listening on correct interface
- Test with curl: `curl http://localhost:9901/health`

### Debugging Steps

1. **Check Server Logs**:
   ```bash
   journalctl -u mcp-1.5 -f
   tail -f /home/mike/mcp-1.5/logs/aiq_mcp_server.log
   ```

2. **Test Server Manually**:
   ```bash
   cd /home/mike/mcp-1.5
   source venv/bin/activate
   python src/aiq_hstk_mcp_server.py
   ```

3. **Verify Dependencies**:
   ```bash
   cd /home/mike/mcp-1.5
   source venv/bin/activate
   pip list | grep -E "(mcp|aiqtoolkit|fastapi)"
   ```

4. **Test MCP Connection**:
   ```bash
   curl -X POST http://localhost:9901/mcp \
     -H "Content-Type: application/json" \
     -d '{"method": "tools/list", "params": {}}'
   ```

### Getting Help

- **Check Documentation**: Review the guides in `/home/mike/mcp-1.5/docs/`
- **View Logs**: Monitor server logs for error messages
- **Test Tools**: Use the test harness: `python scripts/test_extended_features.py`
- **Community Support**: Create an issue in the GitHub repository

## 📚 Additional Resources

- [MCP 1.5 Server Documentation](README.md)
- [Volume Canvas Features](VOLUME_CANVAS_FEATURES.md)
- [Tag Search Guide](TAG_SEARCH_GUIDE.md)
- [Tier Management Guide](TIER_MANAGEMENT_GUIDE.md)
- [Test Validation Summary](../TEST_VALIDATION_SUMMARY.md)

---

**MCP 1.5 Server Integration Guide** - Connecting AI applications to your storage management system.
