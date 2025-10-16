#!/usr/bin/env python3
"""
AIQ Toolkit MCP Server for Federated Storage Service.
This server follows NVIDIA's AIQ Toolkit deployment patterns for MCP services.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional
from pathlib import Path
from urllib.parse import urljoin

# AIQ Toolkit imports
from aiqtoolkit import AIQToolkit, Function, Workflow
from aiqtoolkit.workflows.mcp import MCPServer

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
        logging.FileHandler('logs/aiq_mcp_server.log')
    ]
)
logger = logging.getLogger('aiq_mcp_server')


class FederatedStorageAIQMCPServer:
    """AIQ Toolkit MCP Server implementation for Federated Storage Service."""
    
    def __init__(self, server_name: str = "federated-storage-mcp"):
        """Initialize the AIQ Toolkit MCP server."""
        self.server_name = server_name
        self.aiq = AIQToolkit()
        self.mcp_server = MCPServer(server_name)
        self._setup_functions()
        self._setup_workflow()
        logger.info(f"AIQ Toolkit MCP Server '{server_name}' initialized")
    
    def _setup_functions(self):
        """Setup AIQ Toolkit functions for storage operations."""
        
        @self.aiq.function
        async def list_shares() -> str:
            """List all shares across all volumes."""
            logger.info("AIQ Toolkit: Executing list_shares function")
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
        
        @self.aiq.function
        async def list_nodes() -> str:
            """List all storage nodes and their details."""
            logger.info("AIQ Toolkit: Executing list_nodes function")
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
                    result = f"Found {len(nodes)} nodes:\n"
                    for node in nodes:
                        result += f"- {node.name} (status: {node.status})\n"
                    return result
                    
            except Exception as e:
                logger.error(f"Error listing nodes: {str(e)}")
                return f"Error listing nodes: {str(e)}"
        
        @self.aiq.function
        async def list_volumes() -> str:
            """List all storage volumes and their details."""
            logger.info("AIQ Toolkit: Executing list_volumes function")
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
                    volumes = await client.get_volumes()
                    result = f"Found {len(volumes)} volumes:\n"
                    for volume in volumes:
                        result += f"- {volume.name} (size: {volume.size})\n"
                    return result
                    
            except Exception as e:
                logger.error(f"Error listing volumes: {str(e)}")
                return f"Error listing volumes: {str(e)}"
        
        @self.aiq.function
        async def search_files(query: str = "*", limit: int = 100) -> str:
            """Search for files across all shares."""
            logger.info(f"AIQ Toolkit: Executing search_files function with query: {query}")
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
                    for file in files[:limit]:
                        result += f"- {file.name} (size: {file.size})\n"
                    return result
                    
            except Exception as e:
                logger.error(f"Error searching files: {str(e)}")
                return f"Error searching files: {str(e)}"
        
        @self.aiq.function
        async def get_file_count(query: str = "*") -> str:
            """Get the total count of files matching a query."""
            logger.info(f"AIQ Toolkit: Executing get_file_count function with query: {query}")
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
                    return f"Total files matching '{query}': {count}"
                    
            except Exception as e:
                logger.error(f"Error getting file count: {str(e)}")
                return f"Error getting file count: {str(e)}"
        
        @self.aiq.function
        async def create_share(name: str, path: str) -> str:
            """Create a new storage share."""
            logger.info(f"AIQ Toolkit: Executing create_share function for {name}")
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
                    share = await client.create_share(name, path)
                    return f"Successfully created share '{name}' at {path}"
                    
            except Exception as e:
                logger.error(f"Error creating share: {str(e)}")
                return f"Error creating share: {str(e)}"
        
        @self.aiq.function
        async def get_system_status() -> str:
            """Get overall system status and health."""
            logger.info("AIQ Toolkit: Executing get_system_status function")
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
                    status = await client.get_system_status()
                    return json.dumps(status, indent=2)
                    
            except Exception as e:
                logger.error(f"Error getting system status: {str(e)}")
                return f"Error getting system status: {str(e)}"
    
    def _setup_workflow(self):
        """Setup the AIQ Toolkit workflow."""
        self.workflow = Workflow(
            name="federated-storage-workflow",
            description="Federated Storage Management Workflow using AIQ Toolkit"
        )
        
        # Add functions to workflow
        self.workflow.add_function(self.aiq.functions.list_shares)
        self.workflow.add_function(self.aiq.functions.list_nodes)
        self.workflow.add_function(self.aiq.functions.list_volumes)
        self.workflow.add_function(self.aiq.functions.search_files)
        self.workflow.add_function(self.aiq.functions.get_file_count)
        self.workflow.add_function(self.aiq.functions.create_share)
        self.workflow.add_function(self.aiq.functions.get_system_status)
    
    def run(self, host: str = "127.0.0.1", port: int = 9901, path: str = "/mcp"):
        """Run the AIQ Toolkit MCP server."""
        logger.info(f"Starting AIQ Toolkit MCP server on {host}:{port}{path}")
        
        try:
            # Start the MCP server using AIQ Toolkit's built-in MCP support
            self.mcp_server.start(
                host=host,
                port=port,
                path=path,
                workflow=self.workflow
            )
            
            logger.info(f"AIQ Toolkit MCP server started successfully on {host}:{port}{path}")
            
            # Keep the server running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down AIQ Toolkit MCP server...")
                self.mcp_server.stop()
                
        except Exception as e:
            logger.error(f"Error starting AIQ Toolkit MCP server: {e}")
            raise


def main():
    """Main entry point for the AIQ Toolkit MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AIQ Toolkit MCP Server for Federated Storage")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9901, help="Port to bind to")
    parser.add_argument("--path", default="/mcp", help="MCP path")
    parser.add_argument("--name", default="federated-storage-mcp", help="Server name")
    
    args = parser.parse_args()
    
    # Create and run the server
    server = FederatedStorageAIQMCPServer(args.name)
    server.run(host=args.host, port=args.port, path=args.path)


if __name__ == "__main__":
    main() 