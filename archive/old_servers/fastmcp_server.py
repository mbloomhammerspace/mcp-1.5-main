#!/usr/bin/env python3
"""
FastMCP Server for Federated Storage Service with TCP/IP Support.
This server provides comprehensive storage management capabilities for Cursor and other MCP clients.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional
from pathlib import Path
from urllib.parse import urljoin

# FastMCP imports
from fastmcp import FastMCP, Context

# Local imports
try:
    from .hammerspace_client import HammerspaceClient, AuthenticationError, APIError
    from .config import HammerspaceConfig
    HAMMERSPACE_AVAILABLE = True
except ImportError:
    HAMMERSPACE_AVAILABLE = False
    print("Warning: Hammerspace client not available")

# Configuration
HAMMERSPACE_CONFIG = {
    "base_url": "https://10.200.10.120:8443/mgmt/v1.2/rest/",
    "username": "admin",
    "password": "H@mmerspace123!",
    "verify_ssl": False,
    "timeout": 30
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fastmcp_server.log')
    ]
)
logger = logging.getLogger('fastmcp_server')


class FederatedStorageFastMCPServer:
    """FastMCP Server implementation for Federated Storage Service with TCP/IP support."""
    
    def __init__(self, server_name: str = "federated-storage-mcp"):
        """Initialize the FastMCP server."""
        self.server_name = server_name
        self.mcp = FastMCP(server_name)
        self._setup_tools()
        self._setup_resources()
        self._setup_prompts()
        logger.info(f"FastMCP Server '{server_name}' initialized")
    
    def _setup_tools(self):
        """Setup MCP tools for storage operations."""
        
        @self.mcp.tool
        async def list_shares(ctx: Context) -> str:
            """List all shares across all volumes."""
            logger.info("FastMCP: Executing list_shares tool")
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                config = HammerspaceConfig(
                    base_url=HAMMERSPACE_CONFIG["base_url"],
                    username=HAMMERSPACE_CONFIG["username"],
                    password=HAMMERSPACE_CONFIG["password"],
                    verify_ssl=HAMMERSPACE_CONFIG["verify_ssl"],
                    timeout=HAMMERSPACE_CONFIG["timeout"]
                )
                
                async with HammerspaceClient(config) as client:
                    shares = await client.get_shares()
                    result = f"Found {len(shares)} shares:\n"
                    for share in shares:
                        result += f"- {share.name} (path: {share.path})\n"
                    return result
                    
            except Exception as e:
                logger.error(f"Error listing shares: {str(e)}")
                return f"Error listing shares: {str(e)}"
        
        @self.mcp.tool
        async def list_nodes(ctx: Context) -> str:
            """List all storage nodes and their details."""
            logger.info("FastMCP: Executing list_nodes tool")
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                config = HammerspaceConfig(
                    base_url=HAMMERSPACE_CONFIG["base_url"],
                    username=HAMMERSPACE_CONFIG["username"],
                    password=HAMMERSPACE_CONFIG["password"],
                    verify_ssl=HAMMERSPACE_CONFIG["verify_ssl"],
                    timeout=HAMMERSPACE_CONFIG["timeout"]
                )
                
                async with HammerspaceClient(config) as client:
                    nodes = await client.get_nodes()
                    result = f"Found {len(nodes)} storage nodes:\n"
                    for node in nodes:
                        result += f"- {node.name} (type: {node.node_type}, endpoint: {node.endpoint})\n"
                    return result
                    
            except Exception as e:
                logger.error(f"Error listing nodes: {str(e)}")
                return f"Error listing nodes: {str(e)}"
        
        @self.mcp.tool
        async def list_volumes(ctx: Context) -> str:
            """List all storage volumes."""
            logger.info("FastMCP: Executing list_volumes tool")
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                config = HammerspaceConfig(
                    base_url=HAMMERSPACE_CONFIG["base_url"],
                    username=HAMMERSPACE_CONFIG["username"],
                    password=HAMMERSPACE_CONFIG["password"],
                    verify_ssl=HAMMERSPACE_CONFIG["verify_ssl"],
                    timeout=HAMMERSPACE_CONFIG["timeout"]
                )
                
                async with HammerspaceClient(config) as client:
                    volumes = await client.get_storage_volumes()
                    result = f"Found {len(volumes)} storage volumes:\n"
                    for volume in volumes:
                        result += f"- {volume.name} (type: {volume.volume_type}, state: {volume.state})\n"
                    return result
                    
            except Exception as e:
                logger.error(f"Error listing volumes: {str(e)}")
                return f"Error listing volumes: {str(e)}"
        
        @self.mcp.tool
        async def search_files(ctx: Context, query: str = "*", limit: int = 100) -> str:
            """Search files by name, path, or metadata."""
            logger.info(f"FastMCP: Executing search_files tool with query: {query}")
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                config = HammerspaceConfig(
                    base_url=HAMMERSPACE_CONFIG["base_url"],
                    username=HAMMERSPACE_CONFIG["username"],
                    password=HAMMERSPACE_CONFIG["password"],
                    verify_ssl=HAMMERSPACE_CONFIG["verify_ssl"],
                    timeout=HAMMERSPACE_CONFIG["timeout"]
                )
                
                async with HammerspaceClient(config) as client:
                    files = await client.search_files(query, limit)
                    result = f"Found {len(files)} files matching '{query}':\n"
                    for file in files[:10]:  # Show first 10 results
                        result += f"- {file.path} (size: {file.size} bytes)\n"
                    if len(files) > 10:
                        result += f"... and {len(files) - 10} more files\n"
                    return result
                    
            except Exception as e:
                logger.error(f"Error searching files: {str(e)}")
                return f"Error searching files: {str(e)}"
        
        @self.mcp.tool
        async def get_file_count(ctx: Context, query: str = "*") -> str:
            """Get file count for a specific query."""
            logger.info(f"FastMCP: Executing get_file_count tool with query: {query}")
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                config = HammerspaceConfig(
                    base_url=HAMMERSPACE_CONFIG["base_url"],
                    username=HAMMERSPACE_CONFIG["username"],
                    password=HAMMERSPACE_CONFIG["password"],
                    verify_ssl=HAMMERSPACE_CONFIG["verify_ssl"],
                    timeout=HAMMERSPACE_CONFIG["timeout"]
                )
                
                async with HammerspaceClient(config) as client:
                    count = await client.get_file_count(query)
                    return f"File count for '{query}': {count} files"
                    
            except Exception as e:
                logger.error(f"Error getting file count: {str(e)}")
                return f"Error getting file count: {str(e)}"
        
        @self.mcp.tool
        async def create_share(ctx: Context, name: str, path: str) -> str:
            """Create a new share."""
            logger.info(f"FastMCP: Executing create_share tool for {name}")
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                import requests
                import base64
                
                base_url = HAMMERSPACE_CONFIG["base_url"]
                if not base_url.endswith("/"):
                    base_url += "/"
                url = base_url + "shares"
                
                credentials = f"{HAMMERSPACE_CONFIG['username']}:{HAMMERSPACE_CONFIG['password']}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                headers = {
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                payload = {
                    "name": name,
                    "path": path
                }
                
                resp = requests.post(url, headers=headers, json=payload, verify=False)
                if resp.status_code == 202:
                    task_location = resp.headers.get("Location", "")
                    return f"Share '{name}' created successfully. Task location: {task_location}"
                else:
                    return f"Error creating share: HTTP {resp.status_code} - {resp.text}"
                    
            except Exception as e:
                logger.error(f"Error creating share: {str(e)}")
                return f"Error creating share: {str(e)}"
        
        @self.mcp.tool
        async def list_objectives(ctx: Context) -> str:
            """List all available objectives/policies."""
            logger.info("FastMCP: Executing list_objectives tool")
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                import requests
                import base64
                
                base_url = HAMMERSPACE_CONFIG["base_url"]
                if not base_url.endswith("/"):
                    base_url += "/"
                url = base_url + "objectives"
                
                credentials = f"{HAMMERSPACE_CONFIG['username']}:{HAMMERSPACE_CONFIG['password']}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                headers = {
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                resp = requests.get(url, headers=headers, verify=False)
                if resp.status_code == 200:
                    objectives = resp.json()
                    result = f"Found {len(objectives)} objectives:\n"
                    for obj in objectives:
                        name = obj.get('name', 'Unknown')
                        obj_type = obj.get('_type', 'Unknown')
                        result += f"- {name} ({obj_type})\n"
                    return result
                else:
                    return f"Error getting objectives: HTTP {resp.status_code}"
                    
            except Exception as e:
                logger.error(f"Error listing objectives: {str(e)}")
                return f"Error listing objectives: {str(e)}"
        
        @self.mcp.tool
        async def assimilate_data(ctx: Context, volume_identifier: str, share_identifier: str, 
                                source_path: str, destination_path: str) -> str:
            """Assimilate data from a volume into a share."""
            logger.info(f"FastMCP: Executing assimilate_data tool")
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                import requests
                import base64
                
                base_url = HAMMERSPACE_CONFIG["base_url"]
                if not base_url.endswith("/"):
                    base_url += "/"
                url = base_url + f"storage-volumes/{volume_identifier}/assimilation?sourcePath={source_path}&share={share_identifier}&path={destination_path}"
                
                credentials = f"{HAMMERSPACE_CONFIG['username']}:{HAMMERSPACE_CONFIG['password']}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                headers = {
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                resp = requests.post(url, headers=headers, verify=False)
                if resp.status_code == 202:
                    task_location = resp.headers.get("Location", "")
                    return f"Volume assimilation started successfully. Task location: {task_location}"
                else:
                    return f"Error starting volume assimilation: HTTP {resp.status_code} - {resp.text}"
                    
            except Exception as e:
                logger.error(f"Error assimilating data: {str(e)}")
                return f"Error assimilating data: {str(e)}"
        
        @self.mcp.tool
        async def get_task_status(ctx: Context, task_uuid: str) -> str:
            """Get status of a specific task."""
            logger.info(f"FastMCP: Executing get_task_status tool for {task_uuid}")
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                config = HammerspaceConfig(
                    base_url=HAMMERSPACE_CONFIG["base_url"],
                    username=HAMMERSPACE_CONFIG["username"],
                    password=HAMMERSPACE_CONFIG["password"],
                    verify_ssl=HAMMERSPACE_CONFIG["verify_ssl"],
                    timeout=HAMMERSPACE_CONFIG["timeout"]
                )
                
                async with HammerspaceClient(config) as client:
                    task = await client.get_task(task_uuid)
                    result = f"Task: {task.name}\n"
                    result += f"Status: {task.status}\n"
                    result += f"Progress: {task.progress}%\n"
                    result += f"Exit Value: {task.exit_value}\n"
                    return result
                    
            except Exception as e:
                logger.error(f"Error getting task status: {str(e)}")
                return f"Error getting task status: {str(e)}"
        
        @self.mcp.tool
        async def get_system_status(ctx: Context) -> str:
            """Get overall system status and summary."""
            logger.info("FastMCP: Executing get_system_status tool")
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                config = HammerspaceConfig(
                    base_url=HAMMERSPACE_CONFIG["base_url"],
                    username=HAMMERSPACE_CONFIG["username"],
                    password=HAMMERSPACE_CONFIG["password"],
                    verify_ssl=HAMMERSPACE_CONFIG["verify_ssl"],
                    timeout=HAMMERSPACE_CONFIG["timeout"]
                )
                
                async with HammerspaceClient(config) as client:
                    shares = await client.get_shares()
                    nodes = await client.get_nodes()
                    volumes = await client.get_storage_volumes()
                    
                    system_status = {
                        "status": "success",
                        "message": "System status retrieved successfully",
                        "data": {
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "service_healthy": True,
                            "components": {
                                "hammerspace": {
                                    "healthy": True,
                                    "status": "connected",
                                    "url": HAMMERSPACE_CONFIG["base_url"]
                                }
                            },
                            "summary": {
                                "total_nodes": len(nodes),
                                "total_volumes": len(volumes),
                                "total_shares": len(shares)
                            }
                        }
                    }
                    
                    return f"System Status: {json.dumps(system_status, indent=2)}"
                    
            except Exception as e:
                logger.error(f"Error getting system status: {str(e)}")
                return f"Error getting system status: {str(e)}"
    
    def _setup_resources(self):
        """Setup MCP resources for storage discovery."""
        
        @self.mcp.resource("mcp://federated-storage/storage_nodes")
        async def storage_nodes(ctx: Context) -> str:
            """Get all storage nodes as a resource."""
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                config = HammerspaceConfig(
                    base_url=HAMMERSPACE_CONFIG["base_url"],
                    username=HAMMERSPACE_CONFIG["username"],
                    password=HAMMERSPACE_CONFIG["password"],
                    verify_ssl=HAMMERSPACE_CONFIG["verify_ssl"],
                    timeout=HAMMERSPACE_CONFIG["timeout"]
                )
                
                async with HammerspaceClient(config) as client:
                    nodes = await client.get_nodes()
                    return json.dumps([node.__dict__ for node in nodes], indent=2)
                    
            except Exception as e:
                return f"Error getting storage nodes: {str(e)}"
        
        @self.mcp.resource("mcp://federated-storage/storage_volumes")
        async def storage_volumes(ctx: Context) -> str:
            """Get all storage volumes as a resource."""
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                config = HammerspaceConfig(
                    base_url=HAMMERSPACE_CONFIG["base_url"],
                    username=HAMMERSPACE_CONFIG["username"],
                    password=HAMMERSPACE_CONFIG["password"],
                    verify_ssl=HAMMERSPACE_CONFIG["verify_ssl"],
                    timeout=HAMMERSPACE_CONFIG["timeout"]
                )
                
                async with HammerspaceClient(config) as client:
                    volumes = await client.get_storage_volumes()
                    return json.dumps([volume.__dict__ for volume in volumes], indent=2)
                    
            except Exception as e:
                return f"Error getting storage volumes: {str(e)}"
        
        @self.mcp.resource("mcp://federated-storage/shares")
        async def shares(ctx: Context) -> str:
            """Get all shares as a resource."""
            if not HAMMERSPACE_AVAILABLE:
                return "Hammerspace client not available"
            
            try:
                config = HammerspaceConfig(
                    base_url=HAMMERSPACE_CONFIG["base_url"],
                    username=HAMMERSPACE_CONFIG["username"],
                    password=HAMMERSPACE_CONFIG["password"],
                    verify_ssl=HAMMERSPACE_CONFIG["verify_ssl"],
                    timeout=HAMMERSPACE_CONFIG["timeout"]
                )
                
                async with HammerspaceClient(config) as client:
                    shares = await client.get_shares()
                    return json.dumps([share.__dict__ for share in shares], indent=2)
                    
            except Exception as e:
                return f"Error getting shares: {str(e)}"
    
    def _setup_prompts(self):
        """Setup MCP prompts for common operations."""
        
        @self.mcp.prompt
        async def storage_overview_prompt(ctx: Context) -> str:
            """Generate a prompt for getting storage system overview."""
            return """Please provide an overview of the federated storage system including:
1. Number of storage nodes and their types
2. Number of storage volumes and their states
3. Number of shares and their paths
4. Total file count across the system
5. Any active tasks or operations

Use the available tools to gather this information systematically."""
        
        @self.mcp.prompt
        async def data_movement_prompt(ctx: Context, source: str, destination: str) -> str:
            """Generate a prompt for data movement operations."""
            return f"""Please help with moving data from {source} to {destination}:

1. First, verify the source and destination exist
2. Check available storage capacity
3. Create any necessary shares or volumes
4. Set up appropriate objectives for data placement
5. Initiate the data movement operation
6. Monitor the task progress

Use the available tools to perform these steps safely."""
    
    def run(self, transport: str = "http", host: str = "127.0.0.1", port: int = 8000, path: str = "/mcp"):
        """Run the FastMCP server with specified transport."""
        logger.info(f"Starting FastMCP server on {transport}://{host}:{port}{path}")
        
        if transport == "http":
            # Create a simple HTTP server using FastMCP's built-in HTTP support
            try:
                # FastMCP 2.10.6 HTTP transport
                self.mcp.run(transport="http", host=host, port=port, path=path)
            except Exception as e:
                logger.error(f"HTTP transport failed: {e}")
                # Fallback to stdio
                logger.info("Falling back to stdio transport")
                self.mcp.run(transport="stdio")
        elif transport == "sse":
            self.mcp.run(transport="sse", host=host, port=port)
        else:
            # Default to stdio for local development
            self.mcp.run(transport="stdio")


def main():
    """Main entry point for FastMCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Federated Storage FastMCP Server")
    parser.add_argument("--transport", choices=["stdio", "http", "sse"], default="stdio",
                       help="Transport protocol (default: stdio)")
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP/SSE transport")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP/SSE transport")
    parser.add_argument("--path", default="/mcp", help="Path for HTTP transport")
    
    args = parser.parse_args()
    
    logger.info("Starting Federated Storage FastMCP Server")
    server = FederatedStorageFastMCPServer()
    server.run(transport=args.transport, host=args.host, port=args.port, path=args.path)


if __name__ == "__main__":
    main() 