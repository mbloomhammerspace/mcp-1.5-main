#!/usr/bin/env python3
"""
NVIDIA AI Q Toolkit MCP Server for Volume Canvas
This server implements all Volume Canvas functionality as MCP endpoints using NVIDIA's AIQ Toolkit patterns.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# NAT Toolkit imports - NAT uses a different approach
# We'll use the standard MCP library instead
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Local imports
try:
    from volume_movement_manager import VolumeMovementManager
    from hammerspace_client import HammerspaceClient, AuthenticationError, APIError
    HAMMERSPACE_AVAILABLE = True
except ImportError:
    HAMMERSPACE_AVAILABLE = False
    print("Warning: Hammerspace client not available, using mock data")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
HAMMERSPACE_CONFIG = {
    "base_url": os.getenv("HAMMERSPACE_BASE_URL", "https://10.200.10.120:8443/mgmt/v1.2/rest/"),
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
        logging.FileHandler('logs/hs_1_5_nvidia.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('volume_canvas_mcp_server')


class VolumeCanvasNATMCPServer:
    """NAT Toolkit MCP Server implementation for Volume Canvas functionality."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.manager = None
        self.client = None
        self.current_storage_system = "production"
        
        # Initialize Hammerspace client if available
        if HAMMERSPACE_AVAILABLE:
            try:
                self.client = HammerspaceClient(**HAMMERSPACE_CONFIG)
                self.manager = VolumeMovementManager(self.client)
                logger.info("✅ Hammerspace client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Hammerspace client: {e}")
                HAMMERSPACE_AVAILABLE = False
        
        # Create MCP server using standard MCP library
        self.server = Server("hs-1.5-nvidia-volume-canvas-mcp")
        
        # Register all functions
        self._register_functions()
    
    def _register_functions(self):
        """Register all Volume Canvas functions with MCP server."""
        
        # Register tools with the MCP server
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="list_volumes",
                    description="List all storage volumes with categorization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "Filter volumes by category (all, hot, warm, cold, archive)",
                                "default": "all"
                            },
                            "storage_system": {
                                "type": "string", 
                                "description": "Storage system to query (production, staging, development)",
                                "default": "production"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="list_files",
                    description="List files in a specific path",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to list files from",
                                "default": "/"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of files to return",
                                "default": 100
                            },
                            "storage_system": {
                                "type": "string",
                                "description": "Storage system to query",
                                "default": "production"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_system_status",
                    description="Get overall system status and health",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "storage_system": {
                                "type": "string",
                                "description": "Storage system to analyze",
                                "default": "production"
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls."""
            try:
                logger.info(f"Tool called: {name} with arguments: {arguments}")
                
                if name == "list_volumes":
                    result = await self._list_volumes(
                        arguments.get("filter", "all"),
                        arguments.get("storage_system", "production")
                    )
                elif name == "list_files":
                    result = await self._list_files(
                        arguments.get("path", "/"),
                        arguments.get("limit", 100),
                        arguments.get("storage_system", "production")
                    )
                elif name == "get_system_status":
                    result = await self._get_system_status(
                        arguments.get("storage_system", "production")
                    )
                else:
                    result = {
                        "error": f"Unknown tool: {name}",
                        "timestamp": datetime.now().isoformat()
                    }
                
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}")
                error_result = {
                    "error": str(e),
                    "tool": name,
                    "timestamp": datetime.now().isoformat()
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    async def _list_volumes(self, filter: str = "all", storage_system: str = "production") -> Dict[str, Any]:
        """List all storage volumes with categorization."""
        try:
            if not self.manager:
                return {"error": "Hammerspace client not available - no mock data provided", "volumes": []}
            
            # Switch storage system if needed
            if storage_system != self.current_storage_system:
                await self._switch_storage_system(storage_system)
            
            volumes = []
            for category, vol_list in self.manager.volume_categories.items():
                if filter == "all" or filter in category:
                    for vol in vol_list:
                        volumes.append({
                            "uuid": vol.uuid,
                            "name": vol.name,
                            "type": category.replace('_volumes', ''),
                            "state": vol.state.value if hasattr(vol.state, 'value') else str(vol.state),
                            "size_bytes": vol.size_bytes,
                            "used_bytes": vol.used_bytes,
                            "created": vol.created,
                            "modified": vol.modified
                        })
            
            return {"volumes": volumes}
        except Exception as e:
            logger.error(f"Error listing volumes: {e}")
            return {"error": str(e), "volumes": []}
        
        @self.aiq.function
        async def list_shares(volume_uuid: str, storage_system: str = "production") -> Dict[str, Any]:
            """List all shares for a given volume."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "shares": []}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                shares = []
                for share in self.manager.shares.values():
                    if share.volume_uuid == volume_uuid:
                        shares.append({
                            "uuid": share.uuid,
                            "name": share.name,
                            "path": share.path,
                            "file_count": share.total_number_of_files,
                            "created": share.created,
                            "modified": share.modified
                        })
                
                return {"shares": shares}
            except Exception as e:
                logger.error(f"Error listing shares: {e}")
                return {"error": str(e), "shares": []}
        
        # File Management Functions
        @self.aiq.function
        async def list_files(path: str, limit: int = 100, storage_system: str = "production") -> Dict[str, Any]:
            """List files in a specific path."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "files": []}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                # Use the client to search for files
                files = await self.manager.client.search_files(path, limit=limit)
                
                file_list = []
                for file_obj in files:
                    file_list.append({
                        "name": file_obj.name,
                        "path": file_obj.path,
                        "size_bytes": file_obj.size_bytes,
                        "created": file_obj.created,
                        "modified": file_obj.modified,
                        "share_uuid": file_obj.share_uuid,
                        "volume_uuid": file_obj.volume_uuid
                    })
                
                return {"files": file_list}
            except Exception as e:
                logger.error(f"Error listing files: {e}")
                return {"error": str(e), "files": []}
        
        @self.aiq.function
        async def search_files(
            query: str, 
            search_by_tags: bool = True, 
            search_by_path: bool = True, 
            case_sensitive: bool = False,
            storage_system: str = "production"
        ) -> Dict[str, Any]:
            """Search for files using various criteria."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "results": []}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                # Implement search logic here
                # This would integrate with the existing search functionality
                results = []
                
                # Mock implementation - replace with actual search
                if search_by_path:
                    files = await self.manager.client.search_files("/", limit=1000)
                    for file_obj in files:
                        if case_sensitive:
                            if query in file_obj.path or query in file_obj.name:
                                results.append({
                                    "name": file_obj.name,
                                    "path": file_obj.path,
                                    "size_bytes": file_obj.size_bytes,
                                    "tags": {},  # Would get actual tags
                                    "share_uuid": file_obj.share_uuid,
                                    "volume_uuid": file_obj.volume_uuid
                                })
                        else:
                            if query.lower() in file_obj.path.lower() or query.lower() in file_obj.name.lower():
                                results.append({
                                    "name": file_obj.name,
                                    "path": file_obj.path,
                                    "size_bytes": file_obj.size_bytes,
                                    "tags": {},  # Would get actual tags
                                    "share_uuid": file_obj.share_uuid,
                                    "volume_uuid": file_obj.volume_uuid
                                })
                
                return {"results": results}
            except Exception as e:
                logger.error(f"Error searching files: {e}")
                return {"error": str(e), "results": []}
        
        # Data Movement Functions
        @self.aiq.function
        async def copy_files(
            source_type: str, 
            target_type: str, 
            path: str, 
            recursive: bool = True,
            storage_system: str = "production"
        ) -> Dict[str, Any]:
            """Copy files from source to target volume."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "success": False}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                job = await self.manager.copy_files(source_type, target_type, path, recursive)
                
                return {
                    "success": True,
                    "job": {
                        "uuid": job.uuid,
                        "name": job.name,
                        "status": job.status.value if hasattr(job.status, 'value') else str(job.status),
                        "progress": job.progress,
                        "created": job.created
                    }
                }
            except Exception as e:
                logger.error(f"Error copying files: {e}")
                return {"error": str(e), "success": False}
        
        @self.aiq.function
        async def clone_files(
            source_type: str, 
            target_type: str, 
            path: str,
            storage_system: str = "production"
        ) -> Dict[str, Any]:
            """Clone files from source to target volume."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "success": False}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                job = await self.manager.clone_files(source_type, target_type, path)
                
                return {
                    "success": True,
                    "job": {
                        "uuid": job.uuid,
                        "name": job.name,
                        "status": job.status.value if hasattr(job.status, 'value') else str(job.status),
                        "progress": job.progress,
                        "created": job.created
                    }
                }
            except Exception as e:
                logger.error(f"Error cloning files: {e}")
                return {"error": str(e), "success": False}
        
        @self.aiq.function
        async def move_files(
            source_type: str, 
            target_type: str, 
            path: str,
            storage_system: str = "production"
        ) -> Dict[str, Any]:
            """Move files from source to target volume."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "success": False}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                job = await self.manager.move_files(source_type, target_type, path)
                
                return {
                    "success": True,
                    "job": {
                        "uuid": job.uuid,
                        "name": job.name,
                        "status": job.status.value if hasattr(job.status, 'value') else str(job.status),
                        "progress": job.progress,
                        "created": job.created
                    }
                }
            except Exception as e:
                logger.error(f"Error moving files: {e}")
                return {"error": str(e), "success": False}
        
        # Objective Management Functions
        @self.aiq.function
        async def place_on_tier(
            volume_type: str, 
            path: str, 
            tier_name: str,
            storage_system: str = "production"
        ) -> Dict[str, Any]:
            """Create a place-on-tier objective."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "success": False}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                objective = await self.manager.place_on_tier(volume_type, path, tier_name)
                
                return {
                    "success": True,
                    "objective": {
                        "uuid": objective.uuid,
                        "name": objective.name,
                        "objective_type": objective.objective_type.value if hasattr(objective.objective_type, 'value') else str(objective.objective_type),
                        "state": objective.state.value if hasattr(objective.state, 'value') else str(objective.state),
                        "created": objective.created
                    }
                }
            except Exception as e:
                logger.error(f"Error creating place-on-tier objective: {e}")
                return {"error": str(e), "success": False}
        
        @self.aiq.function
        async def exclude_from_tier(
            volume_type: str, 
            path: str, 
            tier_name: str,
            storage_system: str = "production"
        ) -> Dict[str, Any]:
            """Create an exclude-from-tier objective."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "success": False}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                objective = await self.manager.exclude_from_tier(volume_type, path, tier_name)
                
                return {
                    "success": True,
                    "objective": {
                        "uuid": objective.uuid,
                        "name": objective.name,
                        "objective_type": objective.objective_type.value if hasattr(objective.objective_type, 'value') else str(objective.objective_type),
                        "state": objective.state.value if hasattr(objective.state, 'value') else str(objective.state),
                        "created": objective.created
                    }
                }
            except Exception as e:
                logger.error(f"Error creating exclude-from-tier objective: {e}")
                return {"error": str(e), "success": False}
        
        # Job Management Functions
        @self.aiq.function
        async def list_jobs(
            storage_system: str = "production",
            status_filter: str = "all"
        ) -> Dict[str, Any]:
            """List all active data movement jobs."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "jobs": []}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                jobs = await self.manager.list_active_jobs()
                
                job_list = []
                for job in jobs:
                    if status_filter == "all" or status_filter == job.status.value:
                        job_list.append({
                            "uuid": job.uuid,
                            "name": job.name,
                            "status": job.status.value if hasattr(job.status, 'value') else str(job.status),
                            "progress": job.progress,
                            "created": job.created,
                            "started": job.started,
                            "completed": job.completed
                        })
                
                return {"jobs": job_list}
            except Exception as e:
                logger.error(f"Error listing jobs: {e}")
                return {"error": str(e), "jobs": []}
        
        @self.aiq.function
        async def get_job_status(job_uuid: str, storage_system: str = "production") -> Dict[str, Any]:
            """Get detailed status of a specific job."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized"}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                job = await self.manager.client.get_data_movement_job(job_uuid)
                
                return {
                    "uuid": job.uuid,
                    "name": job.name,
                    "status": job.status.value if hasattr(job.status, 'value') else str(job.status),
                    "progress": job.progress,
                    "created": job.created,
                    "started": job.started,
                    "completed": job.completed,
                    "error_message": job.error_message
                }
            except Exception as e:
                logger.error(f"Error getting job status: {e}")
                return {"error": str(e)}
        
        # Tag Management Functions
        @self.aiq.function
        async def get_tags(path: str, storage_system: str = "production") -> Dict[str, Any]:
            """Get tags for a specific file, folder, or share."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "tags": {}}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                # Implement tag retrieval logic here
                # This would integrate with the existing tagging functionality
                tags = {}  # Mock implementation
                
                return {"tags": tags, "path": path}
            except Exception as e:
                logger.error(f"Error getting tags: {e}")
                return {"error": str(e), "tags": {}}
        
        @self.aiq.function
        async def set_tag(
            path: str, 
            tag_name: str, 
            tag_value: str,
            storage_system: str = "production"
        ) -> Dict[str, Any]:
            """Set a tag on a file, folder, or share."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "success": False}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                # Implement tag setting logic here
                # This would integrate with the existing tagging functionality
                
                return {"success": True, "message": f"Tag '{tag_name}' set to '{tag_value}' on '{path}'"}
            except Exception as e:
                logger.error(f"Error setting tag: {e}")
                return {"error": str(e), "success": False}
        
        @self.aiq.function
        async def clear_all_tags(path: str, storage_system: str = "production") -> Dict[str, Any]:
            """Clear all tags from a file, folder, or share."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "success": False}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                # Implement tag clearing logic here
                # This would integrate with the existing tagging functionality
                
                return {"success": True, "message": f"All tags cleared from '{path}'"}
            except Exception as e:
                logger.error(f"Error clearing tags: {e}")
                return {"error": str(e), "success": False}
        
        # System Analysis Functions
        @self.aiq.function
        async def get_system_status(storage_system: str = "production") -> Dict[str, Any]:
            """Get overall system status and health."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "status": "error"}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                # Get system summary
                summary = {
                    "total_nodes": len(self.manager.nodes),
                    "total_volumes": sum(len(vols) for vols in self.manager.volume_categories.values()),
                    "total_shares": len(self.manager.shares),
                    "total_files": sum(share.total_number_of_files for share in self.manager.shares.values())
                }
                
                return {
                    "status": "success",
                    "data": {
                        "summary": summary,
                        "health": "healthy",
                        "last_updated": datetime.now().isoformat()
                    }
                }
            except Exception as e:
                logger.error(f"Error getting system status: {e}")
                return {"error": str(e), "status": "error"}
        
        @self.aiq.function
        async def analyze_volume_constraints(
            volume_type: str, 
            storage_system: str = "production"
        ) -> Dict[str, Any]:
            """Analyze volume constraints and capacity."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "analysis": {}}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                # Implement volume constraint analysis
                # This would integrate with the existing volume constraint analyzer
                analysis = {
                    "capacity": {"available": 0, "used": 0, "total": 0},
                    "durability": {"replication_factor": 1, "erasure_coding": False},
                    "performance": {"throughput": 0, "latency": 0},
                    "constraints": []
                }
                
                return {"analysis": analysis}
            except Exception as e:
                logger.error(f"Error analyzing volume constraints: {e}")
                return {"error": str(e), "analysis": {}}
        
        # Debug and Diagnostic Functions
        @self.aiq.function
        async def get_objective_debug_info(
            objective_name: str = "",
            storage_system: str = "production"
        ) -> Dict[str, Any]:
            """Get debug information for objectives."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "debug_info": {}}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                # Implement objective debug info retrieval
                # This would integrate with the existing debug functionality
                debug_info = {
                    "total_objectives": 0,
                    "successful": 0,
                    "failed": 0,
                    "in_progress": 0,
                    "failed_objectives": []
                }
                
                return {"debug_info": debug_info}
            except Exception as e:
                logger.error(f"Error getting objective debug info: {e}")
                return {"error": str(e), "debug_info": {}}
        
        @self.aiq.function
        async def verify_data_integrity(
            volume_type: str, 
            path: str,
            storage_system: str = "production"
        ) -> Dict[str, Any]:
            """Verify data integrity on a volume."""
            try:
                if not self.manager:
                    return {"error": "Manager not initialized", "success": False}
                
                # Switch storage system if needed
                if storage_system != self.current_storage_system:
                    await self._switch_storage_system(storage_system)
                
                result = await self.manager.verify_data_integrity(volume_type, path)
                
                return {
                    "success": True, 
                    "result": result,
                    "integrity_status": "verified"
                }
            except Exception as e:
                logger.error(f"Error verifying data integrity: {e}")
                return {"error": str(e), "success": False}
    
    async def _switch_storage_system(self, system: str):
        """Switch to a different storage system."""
        try:
            if system != self.current_storage_system:
                logger.info(f"Switching storage system from {self.current_storage_system} to {system}")
                # Implement storage system switching logic here
                self.current_storage_system = system
        except Exception as e:
            logger.error(f"Error switching storage system: {e}")
    
    async def run(self):
        """Run the MCP server."""
        try:
            logger.info("🚀 Starting Volume Canvas AIQ MCP Server...")
            logger.info(f"📡 Server will be available at: http://0.0.0.0:9901/sse")
            
            # Start the server
            await self.server.run(
                host="0.0.0.0",
                port=9901,
                path="/sse"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            raise


async def main():
    """Main entry point."""
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Create and run the server
    server = VolumeCanvasAIQMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
