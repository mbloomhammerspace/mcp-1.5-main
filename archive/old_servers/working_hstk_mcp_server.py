#!/usr/bin/env python3
"""
Working HSTK MCP Server - Real Hammerspace API + HSTK
This server uses the working HSTK components for all operations.
No mock data - only real Hammerspace API calls through HSTK.
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
    from hammerspace_client import HammerspaceClient, create_hammerspace_client
    from models import Share, File, Objective, DataMovementJob
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
        logging.FileHandler('logs/working_hstk_mcp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('working_hstk_mcp')

class WorkingHSTKMCPServer:
    """Working HSTK-based MCP Server for Volume Canvas functionality."""
    
    def __init__(self):
        """Initialize the HSTK MCP server."""
        self.client = None
        
        # Initialize HSTK if available
        if HSTK_AVAILABLE and HSTK_AVAILABLE:
            try:
                # Create HSTK client using the working create_hammerspace_client function
                self.client = create_hammerspace_client()
                logger.info("✅ HSTK client initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize HSTK client: {e}")
                HSTK_AVAILABLE = False
        else:
            logger.error("❌ HSTK components not available")
        
        # Create MCP server
        self.server = Server("working-hstk-volume-canvas-mcp")
        
        # Register all functions
        self._register_functions()
    
    def _register_functions(self):
        """Register all HSTK-based functions with MCP server."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available HSTK tools."""
            return [
                types.Tool(
                    name="list_shares",
                    description="List all shares using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="list_files",
                    description="List files in a share using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "share_uuid": {
                                "type": "string",
                                "description": "Share UUID to list files from"
                            },
                            "path": {
                                "type": "string",
                                "description": "Path within the share",
                                "default": "/"
                            }
                        },
                        "required": ["share_uuid"]
                    }
                ),
                types.Tool(
                    name="get_file_tags",
                    description="Get tags for a file using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "share_uuid": {
                                "type": "string",
                                "description": "Share UUID"
                            },
                            "path": {
                                "type": "string",
                                "description": "File path to get tags for"
                            }
                        },
                        "required": ["share_uuid", "path"]
                    }
                ),
                types.Tool(
                    name="set_file_tag",
                    description="Set a tag on a file using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "share_uuid": {
                                "type": "string",
                                "description": "Share UUID"
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
                        "required": ["share_uuid", "path", "tag_name", "tag_value"]
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
                    name="list_jobs",
                    description="List all data movement jobs using HSTK",
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
                if not HSTK_AVAILABLE or not self.client:
                    return [types.TextContent(
                        type="text", 
                        text=json.dumps({
                            "error": "HSTK client not available",
                            "tool": name,
                            "timestamp": datetime.now().isoformat()
                        }, indent=2)
                    )]
                
                if name == "list_shares":
                    shares = await self.client.get_shares()
                    result = {
                        "success": True,
                        "shares": [share.to_dict() if hasattr(share, 'to_dict') else str(share) for share in shares] if shares else [],
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                elif name == "list_files":
                    share_uuid = arguments.get("share_uuid")
                    path = arguments.get("path", "/")
                    files = await self.client.search_files(path, share_uuid=share_uuid)
                    result = {
                        "success": True,
                        "files": [file.to_dict() if hasattr(file, 'to_dict') else str(file) for file in files] if files else [],
                        "share_uuid": share_uuid,
                        "path": path,
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                elif name == "get_file_tags":
                    share_uuid = arguments.get("share_uuid")
                    path = arguments.get("path")
                    tags = await self.client.get_tags(share_uuid, path)
                    result = {
                        "success": True,
                        "tags": tags if tags else [],
                        "share_uuid": share_uuid,
                        "path": path,
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                elif name == "set_file_tag":
                    share_uuid = arguments.get("share_uuid")
                    path = arguments.get("path")
                    tag_name = arguments.get("tag_name")
                    tag_value = arguments.get("tag_value")
                    
                    success = await self.client.set_tag(share_uuid, path, tag_name, tag_value)
                    result = {
                        "success": success,
                        "share_uuid": share_uuid,
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
                    
                    objective = await self.client.create_objective(objective_type, path, tier_name)
                    result = {
                        "success": True,
                        "objective": objective.to_dict() if hasattr(objective, 'to_dict') else str(objective),
                        "timestamp": datetime.now().isoformat(),
                        "source": "hstk"
                    }
                    
                elif name == "list_jobs":
                    jobs = await self.client.get_jobs()
                    result = {
                        "success": True,
                        "jobs": [job.to_dict() if hasattr(job, 'to_dict') else str(job) for job in jobs] if jobs else [],
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
        
        logger.info("🚀 Starting Working HSTK MCP Server")
        logger.info("📡 Server will communicate via stdio")
        
        if HSTK_AVAILABLE and self.client:
            logger.info("✅ HSTK client loaded")
            logger.info(f"🔗 Hammerspace API: {self.client.base_url}")
        else:
            logger.error("❌ HSTK client not available")
        
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
                    server_name="working-hstk-volume-canvas-mcp",
                    server_version="1.0.0",
                    capabilities=capabilities
                )
            )

async def main():
    """Main entry point."""
    server = WorkingHSTKMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
