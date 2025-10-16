#!/usr/bin/env python3
"""
HSTK (Hammerspace Toolkit) MCP Server - Real API Only
This server uses the actual HSTK components for all Hammerspace operations.
No mock data, no raw API calls - only HSTK toolkit.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# MCP imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# HSTK imports
try:
    from hammerspace_client import HammerspaceClient, AuthenticationError, APIError
    from operations.storage import StorageOperations
    from operations.movement import MovementOperations
    from operations.catalog import CatalogOperations
    from operations.visibility import VisibilityOperations
    from models import Volume, Share, File, Objective, DataMovementJob
    from config import get_config, HammerspaceConfig
    HSTK_AVAILABLE = True
    print("✅ HSTK components loaded successfully")
except ImportError as e:
    HSTK_AVAILABLE = False
    print(f"❌ HSTK components not available: {e}")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/hstk_mcp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('hstk_mcp')

class HSTKMCPServer:
    """HSTK-based MCP Server for Volume Canvas functionality."""
    
    def __init__(self):
        """Initialize the HSTK MCP server."""
        self.client = None
        self.storage_ops = None
        self.movement_ops = None
        self.catalog_ops = None
        self.visibility_ops = None
        
        # Initialize HSTK if available
        if HSTK_AVAILABLE:
            try:
                # Configure HSTK
                config = HammerspaceConfig(
                    base_url=os.getenv("HAMMERSPACE_BASE_URL", "https://10.200.10.120:8443/mgmt/v1.2/rest"),
                    username=os.getenv("HAMMERSPACE_USERNAME", "admin"),
                    password=os.getenv("HAMMERSPACE_PASSWORD", "H@mmerspace123!"),
                    verify_ssl=os.getenv("HAMMERSPACE_VERIFY_SSL", "false").lower() == "true",
                    timeout=int(os.getenv("HAMMERSPACE_TIMEOUT", "30"))
                )
                
                # Initialize HSTK client
                self.client = HammerspaceClient(config)
                
                # Initialize HSTK operations
                self.storage_ops = StorageOperations(self.client)
                self.movement_ops = MovementOperations(self.client)
                self.catalog_ops = CatalogOperations(self.client)
                self.visibility_ops = VisibilityOperations(self.client)
                
                logger.info("✅ HSTK initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize HSTK: {e}")
                HSTK_AVAILABLE = False
        else:
            logger.error("❌ HSTK components not available")
        
        # Create MCP server
        self.server = Server("hstk-volume-canvas-mcp")
        
        # Register all functions
        self._register_functions()
    
    def _register_functions(self):
        """Register all HSTK-based functions with MCP server."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available HSTK tools."""
            return [
                types.Tool(
                    name="list_volumes",
                    description="List all storage volumes using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="list_shares",
                    description="List all shares using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "volume_id": {
                                "type": "string",
                                "description": "Optional volume ID to filter shares"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="list_files",
                    description="List files in a share using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "share_id": {
                                "type": "string",
                                "description": "Share ID to list files from"
                            },
                            "path": {
                                "type": "string",
                                "description": "Path within the share",
                                "default": "/"
                            }
                        },
                        "required": ["share_id"]
                    }
                ),
                types.Tool(
                    name="get_file_tags",
                    description="Get tags for a file using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "share_id": {
                                "type": "string",
                                "description": "Share ID"
                            },
                            "path": {
                                "type": "string",
                                "description": "File path to get tags for"
                            }
                        },
                        "required": ["share_id", "path"]
                    }
                ),
                types.Tool(
                    name="set_file_tag",
                    description="Set a tag on a file using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "share_id": {
                                "type": "string",
                                "description": "Share ID"
                            },
                            "path": {
                                "type": "string",
                                "description": "File path to set tag on"
                            },
                            "tag_name": {
                                "type": "string",
                                "description": "Name of the tag"
                            },
                            "tag_value": {
                                "type": "string",
                                "description": "Value of the tag"
                            }
                        },
                        "required": ["share_id", "path", "tag_name", "tag_value"]
                    }
                ),
                types.Tool(
                    name="create_objective",
                    description="Create an objective using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "objective_type": {
                                "type": "string",
                                "description": "Type of objective (PLACE_ON_TIER, EXCLUDE_FROM_TIER)"
                            },
                            "path": {
                                "type": "string",
                                "description": "Path to apply objective to"
                            },
                            "tier_name": {
                                "type": "string",
                                "description": "Tier name for the objective"
                            }
                        },
                        "required": ["objective_type", "path", "tier_name"]
                    }
                ),
                types.Tool(
                    name="list_objectives",
                    description="List all objectives using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="list_jobs",
                    description="List all data movement jobs using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_system_status",
                    description="Get system status using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls using HSTK."""
            try:
                if not HSTK_AVAILABLE:
                    return [types.TextContent(
                        type="text", 
                        text=json.dumps({
                            "error": "HSTK not available",
                            "tool": name,
                            "timestamp": datetime.now().isoformat()
                        }, indent=2)
                    )]
                
                if name == "list_volumes":
                    volumes = await self.storage_ops.list_volumes()
                    result = {
                        "success": True,
                        "volumes": [vol.to_dict() for vol in volumes] if volumes else [],
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                elif name == "list_shares":
                    volume_id = arguments.get("volume_id")
                    shares = await self.storage_ops.list_shares(volume_id)
                    result = {
                        "success": True,
                        "shares": [share.to_dict() for share in shares] if shares else [],
                        "volume_id": volume_id,
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                elif name == "list_files":
                    share_id = arguments.get("share_id")
                    path = arguments.get("path", "/")
                    files = await self.catalog_ops.list_files(share_id, path)
                    result = {
                        "success": True,
                        "files": [file.to_dict() for file in files] if files else [],
                        "share_id": share_id,
                        "path": path,
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                elif name == "get_file_tags":
                    share_id = arguments.get("share_id")
                    path = arguments.get("path")
                    tags = await self.visibility_ops.get_tags(share_id, path)
                    result = {
                        "success": True,
                        "tags": tags if tags else [],
                        "share_id": share_id,
                        "path": path,
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                elif name == "set_file_tag":
                    share_id = arguments.get("share_id")
                    path = arguments.get("path")
                    tag_name = arguments.get("tag_name")
                    tag_value = arguments.get("tag_value")
                    
                    success = await self.visibility_ops.set_tag(share_id, path, tag_name, tag_value)
                    result = {
                        "success": success,
                        "share_id": share_id,
                        "path": path,
                        "tag_name": tag_name,
                        "tag_value": tag_value,
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                elif name == "create_objective":
                    objective_type = arguments.get("objective_type")
                    path = arguments.get("path")
                    tier_name = arguments.get("tier_name")
                    
                    objective = await self.movement_ops.create_objective(objective_type, path, tier_name)
                    result = {
                        "success": True,
                        "objective": objective.to_dict() if objective else None,
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                elif name == "list_objectives":
                    objectives = await self.movement_ops.list_objectives()
                    result = {
                        "success": True,
                        "objectives": [obj.to_dict() for obj in objectives] if objectives else [],
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                elif name == "list_jobs":
                    jobs = await self.movement_ops.list_jobs()
                    result = {
                        "success": True,
                        "jobs": [job.to_dict() for job in jobs] if jobs else [],
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                elif name == "get_system_status":
                    status = await self.storage_ops.get_system_status()
                    result = {
                        "success": True,
                        "status": status if status else {},
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                else:
                    result = {
                        "error": f"Unknown tool: {name}",
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}")
                error_result = {
                    "error": str(e),
                    "tool": name,
                    "timestamp": datetime.now().isoformat(),
                    "source": "hstk"
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    async def run(self):
        """Run the HSTK MCP server."""
        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)
        
        # Check for NVIDIA API key
        nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        if not nvidia_api_key:
            logger.warning("NVIDIA_API_KEY environment variable not set")
        else:
            logger.info(f"🔑 NVIDIA API Key found: {'*' * (len(nvidia_api_key) - 8) + nvidia_api_key[-8:]}")
        
        logger.info("🚀 Starting HSTK MCP Server")
        logger.info("📡 Server will communicate via stdio")
        
        if HSTK_AVAILABLE:
            logger.info("✅ HSTK components loaded")
            logger.info(f"🔗 Hammerspace API: {self.client.config.base_url}")
        else:
            logger.error("❌ HSTK components not available")
        
        # Run the server using stdio transport
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            # Create capabilities manually
            capabilities = {
                "tools": {},
                "resources": {},
                "prompts": {}
            }
            
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="hstk-volume-canvas-mcp",
                    server_version="1.0.0",
                    capabilities=capabilities
                )
            )

async def main():
    """Main entry point."""
    server = HSTKMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
