#!/usr/bin/env python3
"""
Simple MCP client to test MCP server functionality
"""
import asyncio
import json
import sys
import subprocess
from typing import Dict, Any

class MCPClient:
    def __init__(self, server_command):
        self.server_command = server_command
        self.process = None
    
    async def start_server(self):
        """Start the MCP server process"""
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            print("✅ MCP Server started")
            return True
        except Exception as e:
            print(f"❌ Failed to start MCP server: {e}")
            return False
    
    async def send_request(self, method: str, params: Dict[str, Any] = None):
        """Send a JSON-RPC request to the MCP server"""
        if not self.process:
            return {"error": "Server not started"}
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        try:
            # Send request
            request_str = json.dumps(request) + "\n"
            self.process.stdin.write(request_str.encode())
            await self.process.stdin.drain()
            
            # Read response
            response_line = await self.process.stdout.readline()
            if response_line:
                response = json.loads(response_line.decode().strip())
                return response
            else:
                return {"error": "No response from server"}
                
        except Exception as e:
            return {"error": f"Request failed: {e}"}
    
    async def list_tools(self):
        """List available tools"""
        return await self.send_request("tools/list")
    
    async def call_tool(self, name: str, arguments: Dict[str, Any] = None):
        """Call a specific tool"""
        return await self.send_request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
    
    async def close(self):
        """Close the server process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()

async def test_destage_from_tier0():
    """Test destaging files from Tier 0 using MCP server"""
    print("🧪 Testing MCP Server Destaging from Tier 0")
    print("=" * 50)
    
    # Try the fastmcp_server
    server_cmd = ["python3", "src/fastmcp_server.py", "--host", "0.0.0.0", "--port", "9901"]
    
    client = MCPClient(server_cmd)
    
    try:
        # Start server
        if not await client.start_server():
            print("❌ Could not start MCP server")
            return
        
        # Wait a moment for server to initialize
        await asyncio.sleep(3)
        
        # List available tools
        print("\n🔧 Listing available tools...")
        tools_response = await client.list_tools()
        print(f"Tools response: {json.dumps(tools_response, indent=2)}")
        
        # Try to call a tool (if any are available)
        if "result" in tools_response and "tools" in tools_response["result"]:
            tools = tools_response["result"]["tools"]
            if tools:
                # Look for destaging-related tools
                destage_tools = [t for t in tools if "destage" in t["name"].lower() or "tier" in t["name"].lower() or "objective" in t["name"].lower()]
                
                if destage_tools:
                    tool = destage_tools[0]
                    print(f"\n🛠️ Calling destaging tool: {tool['name']}")
                    print(f"Tool description: {tool['description']}")
                    
                    # Try to call the tool with appropriate parameters
                    tool_response = await client.call_tool(tool["name"], {
                        "path": "/mnt/se-lab/modelstore/gtc-demo-models/",
                        "tag_name": "user.project",
                        "tag_value": "gtc-model-demo-0001"
                    })
                    print(f"Tool response: {json.dumps(tool_response, indent=2)}")
                else:
                    # Try the first available tool
                    tool_name = tools[0]["name"]
                    print(f"\n🛠️ Calling tool: {tool_name}")
                    tool_response = await client.call_tool(tool_name, {})
                    print(f"Tool response: {json.dumps(tool_response, indent=2)}")
            else:
                print("❌ No tools available")
        else:
            print("❌ Could not get tools list")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_destage_from_tier0())
