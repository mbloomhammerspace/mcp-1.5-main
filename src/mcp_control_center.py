#!/usr/bin/env python3
"""
MCP Control Center - Unified interface for multiple MCP servers
Connects to Hammerspace, Milvus, and Kubernetes MCP servers
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiohttp
import websockets
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class MCPServerStatus:
    """Status information for an MCP server"""
    name: str
    status: str  # "running", "stopped", "error", "unknown"
    port: Optional[int] = None
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    tools_count: int = 0
    resources_count: int = 0
    uptime: Optional[float] = None

@dataclass
class MCPTool:
    """MCP tool information"""
    name: str
    description: str
    server: str
    input_schema: Dict[str, Any]

@dataclass
class MCPResource:
    """MCP resource information"""
    uri: str
    name: str
    description: str
    server: str
    mime_type: str

class MCPControlCenter:
    """Central control for multiple MCP servers"""
    
    def __init__(self):
        self.servers = {
            "hammerspace": {
                "name": "Hammerspace MCP",
                "command": ["python3", "/home/ubuntu/mcp-1.5-main/src/aiq_hstk_mcp_server.py"],
                "env": {"PYTHONPATH": "/home/ubuntu/mcp-1.5-main"},
                "port": None,  # stdio mode
                "type": "stdio"
            },
            "milvus": {
                "name": "Milvus MCP",
                "command": ["uv", "run", "src/mcp_server_milvus/server.py", "--milvus-uri", "http://10.0.0.60:30195"],
                "env": {},
                "port": 5001,  # SSE mode
                "type": "sse",
                "working_dir": "/home/ubuntu/mcp-1.5-main/mcp-server-milvus"
            },
            "kubernetes": {
                "name": "Kubernetes MCP",
                "command": ["python3", "-m", "mcp_server_kubernetes"],
                "env": {},
                "port": 5002,  # SSE mode
                "type": "sse"
            }
        }
        
        self.server_status: Dict[str, MCPServerStatus] = {}
        self.server_processes: Dict[str, subprocess.Popen] = {}
        self.tools: Dict[str, List[MCPTool]] = {}
        self.resources: Dict[str, List[MCPResource]] = {}
        
    async def start_all_servers(self) -> Dict[str, bool]:
        """Start all MCP servers"""
        results = {}
        
        for server_id, config in self.servers.items():
            try:
                logger.info(f"Starting {config['name']}...")
                success = await self.start_server(server_id)
                results[server_id] = success
                if success:
                    logger.info(f"✅ {config['name']} started successfully")
                else:
                    logger.error(f"❌ Failed to start {config['name']}")
            except Exception as e:
                logger.error(f"❌ Error starting {server_id}: {e}")
                results[server_id] = False
                
        return results
    
    async def start_server(self, server_id: str) -> bool:
        """Start a specific MCP server"""
        if server_id not in self.servers:
            logger.error(f"Unknown server: {server_id}")
            return False
            
        config = self.servers[server_id]
        
        try:
            # Check if server is already running
            if server_id in self.server_processes:
                process = self.server_processes[server_id]
                if process.poll() is None:  # Still running
                    logger.info(f"{config['name']} is already running")
                    self.server_status[server_id] = MCPServerStatus(
                        name=config['name'],
                        status="running",
                        port=config.get('port'),
                        last_check=datetime.now()
                    )
                    return True
            
            # Start the server
            env = os.environ.copy()
            env.update(config['env'])
            
            if config['type'] == 'stdio':
                # Start stdio server
                process = subprocess.Popen(
                    config['command'],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True
                )
            else:  # SSE mode
                working_dir = config.get('working_dir', '/home/ubuntu/mcp-1.5-main')
                process = subprocess.Popen(
                    config['command'],
                    env=env,
                    cwd=working_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            self.server_processes[server_id] = process
            
            # Wait a moment for server to start
            await asyncio.sleep(2)
            
            # Check if server started successfully
            if process.poll() is None:
                self.server_status[server_id] = MCPServerStatus(
                    name=config['name'],
                    status="running",
                    port=config.get('port'),
                    last_check=datetime.now()
                )
                return True
            else:
                # Server failed to start
                stderr = process.stderr.read() if process.stderr else "Unknown error"
                self.server_status[server_id] = MCPServerStatus(
                    name=config['name'],
                    status="error",
                    port=config.get('port'),
                    last_check=datetime.now(),
                    error_message=stderr
                )
                return False
                
        except Exception as e:
            logger.error(f"Error starting {server_id}: {e}")
            self.server_status[server_id] = MCPServerStatus(
                name=config['name'],
                status="error",
                port=config.get('port'),
                last_check=datetime.now(),
                error_message=str(e)
            )
            return False
    
    async def stop_server(self, server_id: str) -> bool:
        """Stop a specific MCP server"""
        if server_id not in self.server_processes:
            logger.warning(f"Server {server_id} is not running")
            return True
            
        try:
            process = self.server_processes[server_id]
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            del self.server_processes[server_id]
            
            if server_id in self.server_status:
                self.server_status[server_id].status = "stopped"
                self.server_status[server_id].last_check = datetime.now()
            
            logger.info(f"✅ {self.servers[server_id]['name']} stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping {server_id}: {e}")
            return False
    
    async def check_server_status(self, server_id: str) -> MCPServerStatus:
        """Check the status of a specific MCP server"""
        if server_id not in self.servers:
            return MCPServerStatus(
                name="Unknown",
                status="error",
                error_message=f"Server {server_id} not found"
            )
        
        config = self.servers[server_id]
        
        # Check if process is running
        if server_id in self.server_processes:
            process = self.server_processes[server_id]
            if process.poll() is None:  # Still running
                status = "running"
                uptime = time.time() - process.start_time if hasattr(process, 'start_time') else None
            else:
                status = "stopped"
                uptime = None
        else:
            status = "stopped"
            uptime = None
        
        # For SSE servers, check if port is listening
        if config['type'] == 'sse' and config.get('port'):
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', config['port']))
                sock.close()
                if result == 0:
                    status = "running"
                else:
                    status = "error"
            except Exception:
                if status == "stopped":
                    status = "error"
        
        # Get tools and resources count
        tools_count = len(self.tools.get(server_id, []))
        resources_count = len(self.resources.get(server_id, []))
        
        server_status = MCPServerStatus(
            name=config['name'],
            status=status,
            port=config.get('port'),
            last_check=datetime.now(),
            tools_count=tools_count,
            resources_count=resources_count,
            uptime=uptime
        )
        
        self.server_status[server_id] = server_status
        return server_status
    
    async def get_all_server_status(self) -> Dict[str, MCPServerStatus]:
        """Get status of all MCP servers"""
        for server_id in self.servers.keys():
            await self.check_server_status(server_id)
        return self.server_status.copy()
    
    async def discover_tools(self, server_id: str) -> List[MCPTool]:
        """Discover tools available from a specific MCP server"""
        if server_id not in self.servers:
            return []
        
        config = self.servers[server_id]
        tools = []
        
        try:
            # Check if server is running first
            server_status = await self.check_server_status(server_id)
            if server_status.status != "running":
                logger.warning(f"Server {server_id} is not running, skipping tool discovery")
                return []
            
            if config['type'] == 'stdio':
                # For stdio servers, we need to send MCP protocol messages
                # This is complex, so for now we'll use known tools
                if server_id == "hammerspace":
                    tools = [
                        MCPTool(
                            name="tag_files",
                            description="Tag files with metadata",
                            server=server_id,
                            input_schema={"type": "object", "properties": {"path": {"type": "string"}}}
                        ),
                        MCPTool(
                            name="list_shares",
                            description="List available shares",
                            server=server_id,
                            input_schema={"type": "object", "properties": {}}
                        )
                    ]
                elif server_id == "milvus":
                    tools = [
                        MCPTool(
                            name="list_collections",
                            description="List all collections in Milvus database",
                            server=server_id,
                            input_schema={"type": "object", "properties": {}}
                        ),
                        MCPTool(
                            name="get_collection_info",
                            description="Get information about a specific collection",
                            server=server_id,
                            input_schema={"type": "object", "properties": {"collection_name": {"type": "string"}}}
                        ),
                        MCPTool(
                            name="search_vectors",
                            description="Search for similar vectors in a collection",
                            server=server_id,
                            input_schema={"type": "object", "properties": {"collection_name": {"type": "string"}, "query_vector": {"type": "array"}}}
                        ),
                        MCPTool(
                            name="get_database_status",
                            description="Get Milvus database status and health",
                            server=server_id,
                            input_schema={"type": "object", "properties": {}}
                        )
                    ]
                elif server_id == "kubernetes":
                    tools = [
                        MCPTool(
                            name="list_pods",
                            description="List all pods in the Kubernetes cluster",
                            server=server_id,
                            input_schema={"type": "object", "properties": {"namespace": {"type": "string"}}}
                        ),
                        MCPTool(
                            name="get_cluster_info",
                            description="Get Kubernetes cluster information",
                            server=server_id,
                            input_schema={"type": "object", "properties": {}}
                        ),
                        MCPTool(
                            name="list_jobs",
                            description="List all jobs in the Kubernetes cluster",
                            server=server_id,
                            input_schema={"type": "object", "properties": {"namespace": {"type": "string"}}}
                        ),
                        MCPTool(
                            name="get_pod_logs",
                            description="Get logs from a specific pod",
                            server=server_id,
                            input_schema={"type": "object", "properties": {"pod_name": {"type": "string"}, "namespace": {"type": "string"}}}
                        )
                    ]
            else:  # SSE mode
                # For SSE servers, we can query the HTTP endpoint
                if config.get('port'):
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(f"http://localhost:{config['port']}/tools", timeout=5) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    for tool_data in data.get('tools', []):
                                        tools.append(MCPTool(
                                            name=tool_data['name'],
                                            description=tool_data.get('description', ''),
                                            server=server_id,
                                            input_schema=tool_data.get('inputSchema', {})
                                        ))
                    except Exception as e:
                        logger.warning(f"Could not discover tools for {server_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error discovering tools for {server_id}: {e}")
        
        self.tools[server_id] = tools
        return tools
    
    async def discover_resources(self, server_id: str) -> List[MCPResource]:
        """Discover resources available from a specific MCP server"""
        if server_id not in self.servers:
            return []
        
        config = self.servers[server_id]
        resources = []
        
        try:
            if config['type'] == 'sse' and config.get('port'):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"http://localhost:{config['port']}/resources", timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                for resource_data in data.get('resources', []):
                                    resources.append(MCPResource(
                                        uri=resource_data['uri'],
                                        name=resource_data.get('name', ''),
                                        description=resource_data.get('description', ''),
                                        server=server_id,
                                        mime_type=resource_data.get('mimeType', 'application/json')
                                    ))
                except Exception as e:
                    logger.warning(f"Could not discover resources for {server_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error discovering resources for {server_id}: {e}")
        
        self.resources[server_id] = resources
        return resources
    
    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a specific MCP server"""
        if server_id not in self.servers:
            return {"error": f"Server {server_id} not found"}
        
        config = self.servers[server_id]
        
        try:
            if config['type'] == 'stdio':
                # For stdio servers, implement specific tool functionality
                if server_id == "milvus":
                    return await self._call_milvus_tool(tool_name, arguments)
                elif server_id == "kubernetes":
                    return await self._call_kubernetes_tool(tool_name, arguments)
                else:
                    return {
                        "success": True,
                        "message": f"Tool {tool_name} called on {config['name']} (stdio mode not fully implemented)",
                        "arguments": arguments
                    }
            else:  # SSE mode
                if config.get('port'):
                    try:
                        async with aiohttp.ClientSession() as session:
                            payload = {
                                "tool": tool_name,
                                "arguments": arguments
                            }
                            async with session.post(
                                f"http://localhost:{config['port']}/call",
                                json=payload,
                                timeout=30
                            ) as response:
                                if response.status == 200:
                                    return await response.json()
                                else:
                                    return {"error": f"HTTP {response.status}: {await response.text()}"}
                    except Exception as e:
                        return {"error": f"Failed to call tool: {e}"}
        
        except Exception as e:
            return {"error": f"Error calling tool: {e}"}
    
    async def _call_milvus_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call Milvus-specific tools"""
        try:
            if tool_name == "list_collections":
                # Get collections from Milvus status
                milvus_status = await self.get_milvus_status()
                return {
                    "success": True,
                    "collections": milvus_status.get("collections", {}),
                    "message": "Retrieved Milvus collections"
                }
            elif tool_name == "get_database_status":
                # Get full Milvus status
                milvus_status = await self.get_milvus_status()
                return {
                    "success": True,
                    "status": milvus_status,
                    "message": "Retrieved Milvus database status"
                }
            elif tool_name == "get_collection_info":
                collection_name = arguments.get("collection_name", "")
                if not collection_name:
                    return {"error": "collection_name parameter is required"}
                
                # For now, return basic info - in a real implementation, you'd query Milvus directly
                return {
                    "success": True,
                    "collection_name": collection_name,
                    "message": f"Collection {collection_name} information retrieved",
                    "note": "This is a placeholder response. Full Milvus integration would query the actual database."
                }
            elif tool_name == "search_vectors":
                collection_name = arguments.get("collection_name", "")
                if not collection_name:
                    return {"error": "collection_name parameter is required"}
                
                return {
                    "success": True,
                    "collection_name": collection_name,
                    "message": f"Vector search in {collection_name} completed",
                    "note": "This is a placeholder response. Full Milvus integration would perform actual vector search."
                }
            else:
                return {"error": f"Unknown Milvus tool: {tool_name}"}
        except Exception as e:
            return {"error": f"Error calling Milvus tool: {e}"}
    
    async def _call_kubernetes_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call Kubernetes-specific tools"""
        try:
            if tool_name == "list_pods":
                namespace = arguments.get("namespace", "default")
                # For now, return placeholder - in a real implementation, you'd use kubectl or k8s API
                return {
                    "success": True,
                    "namespace": namespace,
                    "pods": [],
                    "message": f"Listed pods in namespace {namespace}",
                    "note": "This is a placeholder response. Full Kubernetes integration would query the actual cluster."
                }
            elif tool_name == "get_cluster_info":
                # Get cluster info from Kubernetes status
                k8s_status = await self.get_kubernetes_status()
                return {
                    "success": True,
                    "cluster_info": k8s_status,
                    "message": "Retrieved Kubernetes cluster information"
                }
            elif tool_name == "list_jobs":
                namespace = arguments.get("namespace", "default")
                return {
                    "success": True,
                    "namespace": namespace,
                    "jobs": [],
                    "message": f"Listed jobs in namespace {namespace}",
                    "note": "This is a placeholder response. Full Kubernetes integration would query the actual cluster."
                }
            elif tool_name == "get_pod_logs":
                pod_name = arguments.get("pod_name", "")
                namespace = arguments.get("namespace", "default")
                if not pod_name:
                    return {"error": "pod_name parameter is required"}
                
                return {
                    "success": True,
                    "pod_name": pod_name,
                    "namespace": namespace,
                    "logs": "",
                    "message": f"Retrieved logs for pod {pod_name} in namespace {namespace}",
                    "note": "This is a placeholder response. Full Kubernetes integration would retrieve actual logs."
                }
            else:
                return {"error": f"Unknown Kubernetes tool: {tool_name}"}
        except Exception as e:
            return {"error": f"Error calling Kubernetes tool: {e}"}
    
    async def get_milvus_status(self) -> Dict[str, Any]:
        """Get detailed Milvus database status"""
        try:
            # Try to connect to Milvus MCP server
            milvus_status = await self.check_server_status("milvus")
            
            if milvus_status.status != "running":
                return {
                    "status": "error",
                    "message": "Milvus MCP server is not running",
                    "server_status": asdict(milvus_status)
                }
            
            # Get collections info
            collections_info = await self.call_tool("milvus", "list_collections", {})
            
            return {
                "status": "running",
                "server_status": asdict(milvus_status),
                "collections": collections_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get Milvus status: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_kubernetes_status(self) -> Dict[str, Any]:
        """Get detailed Kubernetes cluster status"""
        try:
            # Try to connect to Kubernetes MCP server
            k8s_status = await self.check_server_status("kubernetes")
            
            if k8s_status.status != "running":
                return {
                    "status": "error",
                    "message": "Kubernetes MCP server is not running",
                    "server_status": asdict(k8s_status)
                }
            
            # Get cluster info
            cluster_info = await self.call_tool("kubernetes", "get_cluster_info", {})
            
            return {
                "status": "running",
                "server_status": asdict(k8s_status),
                "cluster_info": cluster_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get Kubernetes status: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_hammerspace_status(self) -> Dict[str, Any]:
        """Get detailed Hammerspace status"""
        try:
            # Try to connect to Hammerspace MCP server
            hs_status = await self.check_server_status("hammerspace")
            
            if hs_status.status != "running":
                return {
                    "status": "error",
                    "message": "Hammerspace MCP server is not running",
                    "server_status": asdict(hs_status)
                }
            
            # Get shares info
            shares_info = await self.call_tool("hammerspace", "list_shares", {})
            
            return {
                "status": "running",
                "server_status": asdict(hs_status),
                "shares": shares_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get Hammerspace status: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_unified_status(self) -> Dict[str, Any]:
        """Get unified status of all MCP servers and their services"""
        return {
            "timestamp": datetime.now().isoformat(),
            "servers": {k: asdict(v) for k, v in (await self.get_all_server_status()).items()},
            "milvus": await self.get_milvus_status(),
            "kubernetes": await self.get_kubernetes_status(),
            "hammerspace": await self.get_hammerspace_status()
        }

# Global instance
mcp_control_center = MCPControlCenter()

async def main():
    """Main entry point for testing"""
    center = MCPControlCenter()
    
    print("🚀 Starting MCP Control Center...")
    
    # Start all servers
    results = await center.start_all_servers()
    print(f"Server startup results: {results}")
    
    # Wait a moment for servers to fully start
    await asyncio.sleep(3)
    
    # Get unified status
    status = await center.get_unified_status()
    print(f"Unified status: {json.dumps(status, indent=2, default=str)}")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(10)
            status = await center.get_unified_status()
            print(f"Status update: {len(status['servers'])} servers monitored")
    except KeyboardInterrupt:
        print("Shutting down...")
        for server_id in center.server_processes.keys():
            await center.stop_server(server_id)

if __name__ == "__main__":
    import os
    asyncio.run(main())
