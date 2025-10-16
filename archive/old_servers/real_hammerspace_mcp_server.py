#!/usr/bin/env python3
"""
Real Hammerspace MCP Server - No Mock Data
This server provides MCP endpoints for Volume Canvas functionality using ONLY real Hammerspace API.
No mock data, no synthetic responses - only real API calls.
"""

import asyncio
import json
import logging
import os
import sys
import requests
import urllib3
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

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
HAMMERSPACE_CONFIG = {
    "base_url": os.getenv("HAMMERSPACE_BASE_URL", "https://10.200.10.120:8443/mgmt/v1.2/rest"),
    "username": os.getenv("HAMMERSPACE_USERNAME", "admin"),
    "password": os.getenv("HAMMERSPACE_PASSWORD", "H@mmerspace123!"),
    "verify_ssl": os.getenv("HAMMERSPACE_VERIFY_SSL", "false").lower() == "true",
    "timeout": int(os.getenv("HAMMERSPACE_TIMEOUT", "30"))
}

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/real_hammerspace_mcp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('real_hammerspace_mcp')

class RealHammerspaceClient:
    """Real Hammerspace API client - no mock data."""
    
    def __init__(self, base_url, username, password, verify_ssl=False, timeout=30):
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password)
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.verify = verify_ssl
        
    def _make_request(self, method, endpoint, **kwargs):
        """Make a request to the Hammerspace API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(
                method, url, 
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise Exception(f"Hammerspace API error: {e}")
    
    def get_volumes(self):
        """Get all volumes from Hammerspace."""
        try:
            return self._make_request('GET', '/volumes')
        except Exception as e:
            logger.error(f"Failed to get volumes: {e}")
            raise
    
    def get_shares(self, volume_uuid=None):
        """Get all shares from Hammerspace."""
        try:
            if volume_uuid:
                return self._make_request('GET', f'/volumes/{volume_uuid}/shares')
            else:
                return self._make_request('GET', '/shares')
        except Exception as e:
            logger.error(f"Failed to get shares: {e}")
            raise
    
    def get_files(self, share_uuid, path="/"):
        """Get files from a share."""
        try:
            return self._make_request('GET', f'/shares/{share_uuid}/files', params={'path': path})
        except Exception as e:
            logger.error(f"Failed to get files: {e}")
            raise
    
    def get_tags(self, share_uuid, path="/"):
        """Get tags for a path."""
        try:
            return self._make_request('GET', f'/shares/{share_uuid}/tags', params={'path': path})
        except Exception as e:
            logger.error(f"Failed to get tags: {e}")
            raise
    
    def set_tag(self, share_uuid, path, tag_name, tag_value):
        """Set a tag on a path."""
        try:
            data = {
                'path': path,
                'tag_name': tag_name,
                'tag_value': tag_value
            }
            return self._make_request('POST', f'/shares/{share_uuid}/tags', json=data)
        except Exception as e:
            logger.error(f"Failed to set tag: {e}")
            raise
    
    def create_objective(self, objective_data):
        """Create an objective."""
        try:
            return self._make_request('POST', '/objectives', json=objective_data)
        except Exception as e:
            logger.error(f"Failed to create objective: {e}")
            raise
    
    def get_jobs(self):
        """Get all jobs."""
        try:
            return self._make_request('GET', '/jobs')
        except Exception as e:
            logger.error(f"Failed to get jobs: {e}")
            raise
    
    def get_system_status(self):
        """Get system status."""
        try:
            return self._make_request('GET', '/system/status')
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            raise

# Create the MCP server
server = Server("real-hammerspace-mcp")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="list_volumes",
            description="List all storage volumes from Hammerspace API",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="list_shares",
            description="List all shares from Hammerspace API",
            inputSchema={
                "type": "object",
                "properties": {
                    "volume_uuid": {
                        "type": "string",
                        "description": "Optional volume UUID to filter shares"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="list_files",
            description="List files in a share from Hammerspace API",
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
            name="get_tags",
            description="Get tags for a path from Hammerspace API",
            inputSchema={
                "type": "object",
                "properties": {
                    "share_uuid": {
                        "type": "string",
                        "description": "Share UUID"
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to get tags for",
                        "default": "/"
                    }
                },
                "required": ["share_uuid"]
            }
        ),
        types.Tool(
            name="set_tag",
            description="Set a tag on a path using Hammerspace API",
            inputSchema={
                "type": "object",
                "properties": {
                    "share_uuid": {
                        "type": "string",
                        "description": "Share UUID"
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to set tag on"
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
            description="Create an objective using Hammerspace API",
            inputSchema={
                "type": "object",
                "properties": {
                    "objective_type": {
                        "type": "string",
                        "description": "Type of objective (place_on_tier, exclude_from_tier)"
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
            description="List all jobs from Hammerspace API",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_system_status",
            description="Get system status from Hammerspace API",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls with real Hammerspace API."""
    try:
        # Initialize the real Hammerspace client
        client = RealHammerspaceClient(**HAMMERSPACE_CONFIG)
        
        if name == "list_volumes":
            volumes = client.get_volumes()
            result = {
                "success": True,
                "volumes": volumes,
                "timestamp": datetime.now().isoformat(),
                "source": "real_hammerspace_api"
            }
            
        elif name == "list_shares":
            volume_uuid = arguments.get("volume_uuid")
            shares = client.get_shares(volume_uuid)
            result = {
                "success": True,
                "shares": shares,
                "volume_uuid": volume_uuid,
                "timestamp": datetime.now().isoformat(),
                "source": "real_hammerspace_api"
            }
            
        elif name == "list_files":
            share_uuid = arguments.get("share_uuid")
            path = arguments.get("path", "/")
            files = client.get_files(share_uuid, path)
            result = {
                "success": True,
                "files": files,
                "share_uuid": share_uuid,
                "path": path,
                "timestamp": datetime.now().isoformat(),
                "source": "real_hammerspace_api"
            }
            
        elif name == "get_tags":
            share_uuid = arguments.get("share_uuid")
            path = arguments.get("path", "/")
            tags = client.get_tags(share_uuid, path)
            result = {
                "success": True,
                "tags": tags,
                "share_uuid": share_uuid,
                "path": path,
                "timestamp": datetime.now().isoformat(),
                "source": "real_hammerspace_api"
            }
            
        elif name == "set_tag":
            share_uuid = arguments.get("share_uuid")
            path = arguments.get("path")
            tag_name = arguments.get("tag_name")
            tag_value = arguments.get("tag_value")
            response = client.set_tag(share_uuid, path, tag_name, tag_value)
            result = {
                "success": True,
                "response": response,
                "share_uuid": share_uuid,
                "path": path,
                "tag_name": tag_name,
                "tag_value": tag_value,
                "timestamp": datetime.now().isoformat(),
                "source": "real_hammerspace_api"
            }
            
        elif name == "create_objective":
            objective_type = arguments.get("objective_type")
            path = arguments.get("path")
            tier_name = arguments.get("tier_name")
            
            objective_data = {
                "objective_type": objective_type,
                "path": path,
                "tier_name": tier_name,
                "status": "active"
            }
            
            response = client.create_objective(objective_data)
            result = {
                "success": True,
                "objective": response,
                "timestamp": datetime.now().isoformat(),
                "source": "real_hammerspace_api"
            }
            
        elif name == "list_jobs":
            jobs = client.get_jobs()
            result = {
                "success": True,
                "jobs": jobs,
                "timestamp": datetime.now().isoformat(),
                "source": "real_hammerspace_api"
            }
            
        elif name == "get_system_status":
            status = client.get_system_status()
            result = {
                "success": True,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "source": "real_hammerspace_api"
            }
            
        else:
            result = {
                "error": f"Unknown tool: {name}",
                "timestamp": datetime.now().isoformat(),
                "source": "real_hammerspace_api"
            }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}")
        error_result = {
            "error": str(e),
            "tool": name,
            "timestamp": datetime.now().isoformat(),
            "source": "real_hammerspace_api"
        }
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]

async def main():
    """Main entry point."""
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Check for NVIDIA API key
    nvidia_api_key = os.getenv("NVIDIA_API_KEY")
    if not nvidia_api_key:
        logger.warning("NVIDIA_API_KEY environment variable not set - server will run without NVIDIA integration")
    else:
        logger.info(f"🔑 NVIDIA API Key found: {'*' * (len(nvidia_api_key) - 8) + nvidia_api_key[-8:]}")
    
    logger.info("🚀 Starting Real Hammerspace MCP Server (No Mock Data)")
    logger.info("📡 Server will communicate via stdio")
    logger.info(f"🔗 Hammerspace API: {HAMMERSPACE_CONFIG['base_url']}")
    logger.info(f"👤 Username: {HAMMERSPACE_CONFIG['username']}")
    
    # Test Hammerspace connection
    try:
        client = RealHammerspaceClient(**HAMMERSPACE_CONFIG)
        volumes = client.get_volumes()
        logger.info(f"✅ Hammerspace connection successful - found {len(volumes)} volumes")
    except Exception as e:
        logger.error(f"❌ Hammerspace connection failed: {e}")
        logger.error("Server will start but API calls will fail")
    
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        # Create capabilities manually
        capabilities = {
            "tools": {},
            "resources": {},
            "prompts": {}
        }
        
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="real-hammerspace-mcp",
                server_version="1.0.0",
                capabilities=capabilities
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
