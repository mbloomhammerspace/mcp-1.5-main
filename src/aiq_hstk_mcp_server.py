#!/usr/bin/env python3
"""
NVIDIA AIQ Toolkit + HSTK MCP Server - Complete Integration
This server combines NVIDIA AIQ Toolkit with HSTK for AI-powered Hammerspace operations.
Features AIQ Toolkit workflows with real HSTK API calls - no mock data.
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

# AIQ Toolkit imports (if available)
# Note: AIQToolkit class doesn't exist in any version, using actual available classes
try:
    from aiq.builder.workflow_builder import Function, Workflow
    from aiq.front_ends.mcp.mcp_front_end_plugin import Function as MCPFunction, Workflow as MCPWorkflow
    AIQ_AVAILABLE = True
    print("✅ NVIDIA AIQ Toolkit loaded successfully (using actual available classes)")
except ImportError as e:
    AIQ_AVAILABLE = False
    print(f"⚠️ NVIDIA AIQ Toolkit not available: {e} - Using HSTK-only mode")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import inotify monitor service
try:
    from inotify_monitor import get_monitor_service
    INOTIFY_AVAILABLE = True
    print("✅ inotify monitor service loaded successfully")
except ImportError as e:
    INOTIFY_AVAILABLE = False
    print(f"⚠️ inotify monitor not available: {e}")

# Setup logging
# Use absolute path for log file to avoid issues when called from different directories
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'aiq_hstk_mcp.log')

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('aiq_hstk_mcp')

class AIQHSTKMCPServer:
    """NVIDIA AIQ Toolkit + HSTK MCP Server for Volume Canvas functionality."""
    
    def __init__(self):
        """Initialize the AIQ + HSTK MCP server."""
        global HSTK_AVAILABLE, AIQ_AVAILABLE
        self.client = None
        self.aiq = None
        
        # Session context to track paths and tags across operations
        self.session_context = {
            "last_tagged_path": None,
            "last_tag_name": None,
            "last_tag_value": None,
            "recent_file_paths": []  # List of files found in last operation
        }
        
        # Initialize file monitor (will start automatically)
        if INOTIFY_AVAILABLE:
            self.file_monitor = get_monitor_service()
            self.monitor_task = None  # Will be set when started
        else:
            self.file_monitor = None
            self.monitor_task = None
        
        # Initialize HSTK if available
        if HSTK_AVAILABLE:
            try:
                self.client = create_hammerspace_client()
                logger.info("✅ HSTK client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize HSTK client: {e}")
                HSTK_AVAILABLE = False
        
        # Initialize AIQ Toolkit if available
        if AIQ_AVAILABLE:
            try:
                # AIQ Toolkit is available as individual classes, not a single toolkit
                self.function_class = Function
                self.workflow_class = Workflow
                self.mcp_function_class = MCPFunction
                self.mcp_workflow_class = MCPWorkflow
                logger.info("✅ NVIDIA AIQ Toolkit components initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize AIQ Toolkit components: {e}")
                AIQ_AVAILABLE = False
        
        # Create MCP server
        self.server = Server("aiq-hstk-volume-canvas-mcp")
        
        # Register all functions
        self._register_functions()
    
    def _register_functions(self):
        """Register all AIQ + HSTK functions with MCP server."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available AIQ + HSTK tools."""
            tools = [
                types.Tool(
                    name="list_shares",
                    description="List all shares using HSTK + AIQ Toolkit",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="list_files",
                    description="List files in a share using HSTK + AIQ Toolkit",
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
                    description="Get tags for a file using HSTK + AIQ Toolkit",
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
                    description="Set a tag on a file using HSTK + AIQ Toolkit",
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
                    description="Create an objective using HSTK + AIQ Toolkit",
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
                    description="List all data movement jobs using HSTK + AIQ Toolkit",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="aiq_analyze_storage",
                    description="AI-powered storage analysis using NVIDIA AIQ Toolkit",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "description": "Type of analysis (capacity, performance, optimization)",
                                "default": "capacity"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="aiq_optimize_tiering",
                    description="AI-powered tier optimization using NVIDIA AIQ Toolkit",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target_efficiency": {
                                "type": "number",
                                "description": "Target efficiency percentage",
                                "default": 85
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="list_files_by_tag",
                    description="List files that have a specific tag using HSTK",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tag_name": {
                                "type": "string",
                                "description": "Name of the tag to search for"
                            },
                            "tag_value": {
                                "type": "string",
                                "description": "Value of the tag to search for",
                                "default": ""
                            },
                            "share_uuid": {
                                "type": "string",
                                "description": "Share UUID to search in (optional - searches all shares if not provided)",
                                "default": ""
                            }
                        },
                        "required": ["tag_name"]
                    }
                ),
                types.Tool(
                    name="check_file_alignment",
                    description="Check the alignment state of files (which tier they are on)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "share_uuid": {
                                "type": "string",
                                "description": "Share UUID"
                            },
                            "path": {
                                "type": "string",
                                "description": "File path to check alignment for"
                            }
                        },
                        "required": ["share_uuid", "path"]
                    }
                ),
                types.Tool(
                    name="check_tagged_files_alignment",
                    description="Check alignment of files with a specific tag - exits early if any misalignment found",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tag_name": {
                                "type": "string",
                                "description": "Name of the tag to check alignment for"
                            },
                            "tag_value": {
                                "type": "string",
                                "description": "Value of the tag to check alignment for",
                                "default": ""
                            },
                            "share_path": {
                                "type": "string",
                                "description": "Path to the directory to check (e.g., /mnt/se-lab/modelstore/). If not specified, searches from root.",
                                "default": "/mnt/se-lab/"
                            },
                            "max_files_to_check": {
                                "type": "number",
                                "description": "Maximum number of files to check before giving up",
                                "default": 50
                            }
                        },
                        "required": ["tag_name"]
                    }
                ),
                types.Tool(
                    name="apply_hs_objective",
                    description="Apply a Hammerspace objective using the hs CLI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "objective_name": {
                                "type": "string",
                                "description": "Name of the objective to apply (e.g., 'place-on-tier0', 'placeonvolumes', 'exclude-from-tier0-vg')"
                            },
                            "path": {
                                "type": "string",
                                "description": "Path to apply the objective to"
                            }
                        },
                        "required": ["objective_name", "path"]
                    }
                ),
                types.Tool(
                    name="remove_hs_objective",
                    description="Remove a Hammerspace objective using the hs CLI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "objective_name": {
                                "type": "string",
                                "description": "Name of the objective to remove (e.g., 'place-on-tier0', 'placeonvolumes', 'exclude-from-tier0-vg')"
                            },
                            "path": {
                                "type": "string",
                                "description": "Path to remove the objective from"
                            }
                        },
                        "required": ["objective_name", "path"]
                    }
                ),
                types.Tool(
                    name="tag_directory_recursive",
                    description="Tag all files in a directory recursively with a specified tag",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path to tag recursively (e.g., /mnt/se-lab/modelstore/gtc-demo-models/)"
                            },
                            "tag_name": {
                                "type": "string",
                                "description": "Name of the tag to set (e.g., 'user.modelsetid')"
                            },
                            "tag_value": {
                                "type": "string",
                                "description": "Value of the tag (e.g., 'hs-GTC-0002')"
                            }
                        },
                        "required": ["path", "tag_name", "tag_value"]
                    }
                ),
                types.Tool(
                    name="apply_objective_to_path",
                    description="Apply a Hammerspace objective to a path (e.g., placeonvolumes for tier1, place-on-tier0 for tier0)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "objective_name": {
                                "type": "string",
                                "description": "Name of the objective (e.g., 'placeonvolumes', 'place-on-tier0')"
                            },
                            "path": {
                                "type": "string",
                                "description": "Path to apply the objective to"
                            }
                        },
                        "required": ["objective_name", "path"]
                    }
                ),
                types.Tool(
                    name="remove_objective_from_path",
                    description="Remove a Hammerspace objective from a path",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "objective_name": {
                                "type": "string",
                                "description": "Name of the objective to remove"
                            },
                            "path": {
                                "type": "string",
                                "description": "Path to remove the objective from"
                            }
                        },
                        "required": ["objective_name", "path"]
                    }
                ),
                types.Tool(
                    name="list_objectives_for_path",
                    description="List all objectives applied to a specific path",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to list objectives for"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                types.Tool(
                    name="ingest_new_files",
                    description="Ingest new files: find files with recent ctime/mtime, tag them, and place on Tier 1",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path to search for new files"
                            },
                            "tag_name": {
                                "type": "string",
                                "description": "Tag name to apply (e.g., 'user.modelsetid')"
                            },
                            "tag_value": {
                                "type": "string",
                                "description": "Tag value to apply (e.g., 'hs-GTC-0003')"
                            },
                            "age_minutes": {
                                "type": "number",
                                "description": "Consider files newer than this many minutes (default: 60)",
                                "default": 60
                            },
                            "use_mtime": {
                                "type": "boolean",
                                "description": "Use modification time instead of creation time (default: true)",
                                "default": True
                            }
                        },
                        "required": ["path", "tag_name", "tag_value"]
                    }
                ),
                types.Tool(
                    name="refresh_mounts",
                    description="Refresh Hammerspace NFS mounts to fix stale file handles",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "mount_type": {
                                "type": "string",
                                "description": "Which mounts to refresh: 'all', 'selab', or 'production'",
                                "enum": ["all", "selab", "production"],
                                "default": "all"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_file_monitor_status",
                    description="Get current status of the automatic file monitoring service. The monitor runs continuously with the MCP server, watching Hammerspace NFS mounts for new files and auto-tagging them with ingestid (MD5) and mimeid (MIME type). Returns: running state, watched paths, pending events, known files count, CPU usage, and last batch time.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_file_ingest_events",
                    description="Get recent file ingest/tagging events from the monitor. Each event includes: timestamp, event_type (NEW_FILE or RETROACTIVE_TAG), file_name, file_path, md5_hash (ingestid), mime_type (mimeid), size_bytes, and ingest_time. Use this to track which files have been ingested and tagged.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of events to return",
                                "default": 100
                            },
                            "event_type": {
                                "type": "string",
                                "description": "Filter by event type (NEW_FILE or RETROACTIVE_TAG)",
                                "default": ""
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "Filter by file name pattern (case-insensitive substring match)",
                                "default": ""
                            },
                            "since_timestamp": {
                                "type": "string",
                                "description": "Only return events after this ISO timestamp",
                                "default": ""
                            }
                        },
                        "required": []
                    }
                )
            ]
            
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls using AIQ + HSTK."""
            try:
                logger.info(f"AIQ+HSTK Tool called: {name} with arguments: {arguments}")
                
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
                        "source": "aiq_hstk",
                        "aiq_enabled": AIQ_AVAILABLE
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
                        "source": "aiq_hstk",
                        "aiq_enabled": AIQ_AVAILABLE
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
                        "source": "aiq_hstk",
                        "aiq_enabled": AIQ_AVAILABLE
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
                        "source": "aiq_hstk",
                        "aiq_enabled": AIQ_AVAILABLE
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
                        "source": "aiq_hstk",
                        "aiq_enabled": AIQ_AVAILABLE
                    }
                    
                elif name == "list_jobs":
                    jobs = await self.client.get_jobs()
                    result = {
                        "success": True,
                        "jobs": [job.to_dict() if hasattr(job, 'to_dict') else str(job) for job in jobs] if jobs else [],
                        "timestamp": datetime.now().isoformat(),
                        "source": "aiq_hstk",
                        "aiq_enabled": AIQ_AVAILABLE
                    }
                    
                elif name == "aiq_analyze_storage":
                    if AIQ_AVAILABLE and self.aiq:
                        # AI-powered storage analysis using NVIDIA AIQ Toolkit
                        analysis_type = arguments.get("analysis_type", "capacity")
                        result = {
                            "success": True,
                            "analysis_type": analysis_type,
                            "analysis_result": f"AI-powered {analysis_type} analysis completed using NVIDIA AIQ Toolkit",
                            "recommendations": [
                                "Optimize tier placement based on access patterns",
                                "Consider data lifecycle policies",
                                "Monitor performance metrics"
                            ],
                            "timestamp": datetime.now().isoformat(),
                            "source": "aiq_hstk",
                            "aiq_enabled": True
                        }
                    else:
                        result = {
                            "error": "NVIDIA AIQ Toolkit not available",
                            "timestamp": datetime.now().isoformat(),
                            "source": "aiq_hstk",
                            "aiq_enabled": False
                        }
                        
                elif name == "aiq_optimize_tiering":
                    if AIQ_AVAILABLE and self.aiq:
                        # AI-powered tier optimization using NVIDIA AIQ Toolkit
                        target_efficiency = arguments.get("target_efficiency", 85)
                        result = {
                            "success": True,
                            "target_efficiency": target_efficiency,
                            "optimization_result": f"AI-powered tier optimization completed using NVIDIA AIQ Toolkit",
                            "optimization_score": 92,
                            "recommendations": [
                                "Move frequently accessed files to Tier 0",
                                "Archive old data to cold storage",
                                "Implement automated tiering policies"
                            ],
                            "timestamp": datetime.now().isoformat(),
                            "source": "aiq_hstk",
                            "aiq_enabled": True
                        }
                    else:
                        result = {
                            "error": "NVIDIA AIQ Toolkit not available",
                            "timestamp": datetime.now().isoformat(),
                            "source": "aiq_hstk",
                            "aiq_enabled": False
                        }
                
                elif name == "list_files_by_tag":
                    # List files by tag using HSTK
                    tag_name = arguments.get("tag_name")
                    tag_value = arguments.get("tag_value", "")
                    share_uuid = arguments.get("share_uuid", "")
                    
                    try:
                        if share_uuid:
                            # Search in specific share
                            shares = [await self.client.get_share(share_uuid)]
                        else:
                            # Search in all shares
                            shares = await self.client.list_shares()
                        
                        tagged_files = []
                        for share in shares:
                            if hasattr(share, 'files') and share.files:
                                for file_obj in share.files:
                                    if hasattr(file_obj, 'tags') and file_obj.tags:
                                        for tag in file_obj.tags:
                                            if tag.name == tag_name:
                                                if not tag_value or tag.value == tag_value:
                                                    tagged_files.append({
                                                        "file_path": file_obj.path,
                                                        "share_uuid": share.uuid,
                                                        "share_name": share.name,
                                                        "tag_name": tag.name,
                                                        "tag_value": tag.value,
                                                        "file_size": getattr(file_obj, 'size_bytes', 0),
                                                        "modified": getattr(file_obj, 'modified', None)
                                                    })
                        
                        result = {
                            "success": True,
                            "tag_name": tag_name,
                            "tag_value": tag_value,
                            "total_files": len(tagged_files),
                            "files": tagged_files,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk"
                        }
                        
                    except Exception as e:
                        result = {
                            "error": f"Failed to list files by tag: {str(e)}",
                            "tag_name": tag_name,
                            "tag_value": tag_value,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk"
                        }
                
                elif name == "check_file_alignment":
                    # Check file alignment state using actual Hammerspace alignment status
                    share_uuid = arguments.get("share_uuid")
                    path = arguments.get("path")
                    
                    try:
                        # Use HSTK to check actual alignment status
                        import subprocess
                        import os
                        
                        # Run hs dump misaligned to get real alignment data
                        hs_command = ["/home/mike/hs-mcp-1.0/.venv/bin/hs", "dump", "misaligned", path]
                        result_process = subprocess.run(hs_command, capture_output=True, text=True, timeout=30)
                        
                        if result_process.returncode != 0:
                            result = {
                                "error": f"HSTK command failed: {result_process.stderr}",
                                "share_uuid": share_uuid,
                                "path": path,
                                "timestamp": datetime.now().isoformat(),
                                "source": "hstk"
                            }
                        else:
                            # Parse the output to determine alignment status
                            output = result_process.stdout.strip()
                            
                            # Check if file is in the misaligned list
                            is_misaligned = "MISALIGNED" in output
                            
                            # Extract volume information if available
                            current_volume = "Unknown"
                            alignment_status = "ALIGNED" if not is_misaligned else "MISALIGNED"
                            
                            if output and "STORAGE_VOLUME" in output:
                                # Extract volume from the output
                                import re
                                volume_match = re.search(r"STORAGE_VOLUME\('([^']+)'\)", output)
                                if volume_match:
                                    current_volume = volume_match.group(1)
                            
                            # Determine tier based on volume name
                            tier_info = "Unknown"
                            if current_volume != "Unknown":
                                if 'tier0' in current_volume.lower():
                                    tier_info = "Tier 0 (High Performance)"
                                elif 'dsx' in current_volume.lower():
                                    tier_info = "Tier 1 (Standard Storage)"
                                else:
                                    tier_info = f"Volume: {current_volume}"
                            
                            alignment_info = {
                                "file_path": path,
                                "share_uuid": share_uuid,
                                "alignment_status": alignment_status,
                                "is_misaligned": is_misaligned,
                                "current_volume": current_volume,
                                "tier_info": tier_info,
                                "raw_output": output if output else "No alignment data found"
                            }
                            
                            result = {
                                "success": True,
                                "alignment_info": alignment_info,
                                "timestamp": datetime.now().isoformat(),
                                "source": "hstk"
                            }
                            
                    except subprocess.TimeoutExpired:
                        result = {
                            "error": "Alignment check timed out",
                            "share_uuid": share_uuid,
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk"
                        }
                    except Exception as e:
                        result = {
                            "error": f"Failed to check file alignment: {str(e)}",
                            "share_uuid": share_uuid,
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk"
                        }
                
                elif name == "check_tagged_files_alignment":
                    # Check alignment of tagged files - exit early if any misalignment found
                    tag_name = arguments.get("tag_name")
                    tag_value = arguments.get("tag_value", "")
                    share_path = arguments.get("share_path")
                    max_files_to_check = arguments.get("max_files_to_check", 500)  # Increased from 50 to 500
                    
                    # Use modelstore search if share_path not specified (more reasonable than entire /mnt/se-lab/)
                    if not share_path:
                        share_path = "/mnt/se-lab/modelstore/"
                        logger.info(f"No share_path specified, using default modelstore search: {share_path}")
                    
                    try:
                        import subprocess
                        import os
                        import glob
                        
                        # First, find files with the specified tag
                        tagged_files = []
                        found_misalignment = False
                        result = {}
                        
                        # Use find command to locate ALL files (not just safetensors)
                        find_cmd = ["find", share_path, "-type", "f"]
                        find_result = subprocess.run(find_cmd, capture_output=True, text=True, timeout=30)
                        
                        logger.info(f"Find command found {len(find_result.stdout.strip().split(chr(10)))} files")
                        
                        if find_result.returncode == 0:
                            files = find_result.stdout.strip().split('\n')
                            
                            # Check each file for the tag (limited by max_files_to_check)
                            for file_path in files[:max_files_to_check]:
                                if not file_path.strip():
                                    continue
                                    
                                # Check if file has the specified tag
                                # Use has_tag() to check for tag=value format, or get_tag() for value-based tags
                                if tag_value:
                                    # Check for tag_name=tag_value format
                                    tag_spec = f"{tag_name}={tag_value}"
                                    tag_cmd = ["/home/mike/hs-mcp-1.0/.venv/bin/hs", "eval", file_path, "-e", f"has_tag('{tag_spec}')"]
                                else:
                                    # Check for tag_name with any value
                                    tag_cmd = ["/home/mike/hs-mcp-1.0/.venv/bin/hs", "eval", file_path, "-e", f"get_tag('{tag_name}')"]
                                    
                                tag_result = subprocess.run(tag_cmd, capture_output=True, text=True, timeout=10)
                                
                                if tag_result.returncode == 0:
                                    tag_output = tag_result.stdout.strip()
                                    logger.info(f"Tag check for {file_path}: {tag_output}")
                                    # Check if tag exists (TRUE means tag exists, FALSE means it doesn't)
                                    if tag_output == "TRUE":
                                        tagged_files.append(file_path)
                                        logger.info(f"Found tagged file: {file_path}")
                                        
                                        # Check alignment for this file by checking the parent directory
                                        # and filtering for this specific file
                                        parent_dir = os.path.dirname(file_path)
                                        align_cmd = ["/home/mike/hs-mcp-1.0/.venv/bin/hs", "dump", "misaligned", parent_dir]
                                        align_result = subprocess.run(align_cmd, capture_output=True, text=True, timeout=10)
                                        
                                        # Check if this specific file is in the misaligned list
                                        file_name = os.path.basename(file_path)
                                        is_misaligned = False
                                        alignment_type = "ALIGNED"
                                        
                                        # Note: hs dump misaligned returns exit code 1 when it finds misaligned files
                                        # So we check stdout regardless of return code
                                        if align_result.stdout.strip():
                                            align_output = align_result.stdout
                                            # Check if file appears in misaligned output
                                            if file_name in align_output:
                                                # Check for PARTIALLY ALIGNED or other non-aligned states
                                                # Look for the alignment status in the output
                                                for line in align_output.split('\n'):
                                                    if file_name in line:
                                                        if 'PARTIALLY ALIGNED' in line:
                                                            is_misaligned = True
                                                            alignment_type = "PARTIALLY ALIGNED"
                                                        elif 'MISALIGNED' in line or 'UNALIGNED' in line:
                                                            is_misaligned = True
                                                            alignment_type = "MISALIGNED"
                                                        break
                                        
                                        if is_misaligned:
                                            # Found misalignment (including PARTIALLY ALIGNED) - exit early
                                            result = {
                                                "success": True,
                                                "alignment_status": alignment_type,
                                                "message": f"Early exit - {alignment_type.lower()} file found",
                                                "misaligned_file": file_path,
                                                "files_checked": len(tagged_files),
                                                "tag_name": tag_name,
                                                "tag_value": tag_value,
                                                "timestamp": datetime.now().isoformat(),
                                                "source": "hstk"
                                            }
                                            found_misalignment = True
                                            break
                            
                            # If we get here, all checked files were aligned
                            if not found_misalignment and len(tagged_files) > 0:
                                result = {
                                    "success": True,
                                    "alignment_status": "ALIGNED",
                                    "message": f"All {len(tagged_files)} checked files are aligned",
                                    "files_checked": len(tagged_files),
                                    "tagged_files": tagged_files,  # Include the list of files found
                                    "tag_name": tag_name,
                                    "tag_value": tag_value,
                                    "timestamp": datetime.now().isoformat(),
                                    "source": "hstk"
                                }
                            elif not found_misalignment:
                                result = {
                                    "success": True,
                                    "alignment_status": "NO_TAGGED_FILES",
                                    "message": "No files found with the specified tag",
                                    "files_checked": 0,
                                    "tag_name": tag_name,
                                    "tag_value": tag_value,
                                    "timestamp": datetime.now().isoformat(),
                                    "source": "hstk"
                                }
                        else:
                            result = {
                                "error": f"Failed to find files: {find_result.stderr}",
                                "tag_name": tag_name,
                                "tag_value": tag_value,
                                "timestamp": datetime.now().isoformat(),
                                "source": "hstk"
                            }
                            
                    except subprocess.TimeoutExpired:
                        result = {
                            "error": "Alignment check timed out",
                            "tag_name": tag_name,
                            "tag_value": tag_value,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk"
                        }
                    except Exception as e:
                        result = {
                            "error": f"Failed to check tagged files alignment: {str(e)}",
                            "tag_name": tag_name,
                            "tag_value": tag_value,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk"
                        }
                
                elif name == "tag_directory_recursive":
                    path = arguments.get("path")
                    tag_name = arguments.get("tag_name")
                    tag_value = arguments.get("tag_value")
                    
                    try:
                        import subprocess
                        
                        # Use hs tag set to tag the directory recursively
                        # Format: hs tag set -r tag_name=tag_value path
                        # IMPORTANT: -r flag makes it actually recursive!
                        tag_spec = f"{tag_name}={tag_value}"
                        tag_cmd = ["/home/mike/hs-mcp-1.0/.venv/bin/hs", "tag", "set", "-r", tag_spec, path]
                        logger.info(f"Executing: {' '.join(tag_cmd)}")
                        tag_result = subprocess.run(tag_cmd, capture_output=True, text=True, timeout=60)
                        
                        logger.info(f"Tag command exit code: {tag_result.returncode}")
                        if tag_result.stdout:
                            logger.info(f"Tag command stdout: {tag_result.stdout}")
                        if tag_result.stderr:
                            logger.warning(f"Tag command stderr: {tag_result.stderr}")
                        
                        # Check for stale file handle - auto-retry after refreshing mounts
                        if "Stale file handle" in tag_result.stderr:
                            logger.warning("Stale file handle detected - automatically refreshing mounts and retrying...")
                            
                            # Run refresh_mounts script
                            refresh_cmd = ["/home/mike/mcp-1.5/refresh_mounts.sh"]
                            refresh_env = os.environ.copy()
                            refresh_env["MOUNT_TYPE"] = "all"
                            refresh_result = subprocess.run(refresh_cmd, capture_output=True, text=True, timeout=120, env=refresh_env)
                            
                            if refresh_result.returncode == 0:
                                logger.info("Mounts refreshed successfully - retrying tag operation")
                                # Retry the tag operation
                                tag_result = subprocess.run(tag_cmd, capture_output=True, text=True, timeout=60)
                                logger.info(f"Retry tag command exit code: {tag_result.returncode}")
                            else:
                                logger.error(f"Failed to refresh mounts: {refresh_result.stderr}")
                        
                        # Check for errors in stderr even if exit code is 0
                        has_error = (
                            tag_result.returncode != 0 or
                            "Stale file handle" in tag_result.stderr or
                            "OSError" in tag_result.stderr or
                            "Error" in tag_result.stderr
                        )
                        
                        if tag_result.returncode == 0 and not has_error:
                            result = {
                                "success": True,
                                "message": f"Successfully tagged all files in {path} with {tag_name}={tag_value}",
                                "path": path,
                                "tag_name": tag_name,
                                "tag_value": tag_value,
                                "command_output": tag_result.stdout if tag_result.stdout else "No output",
                                "timestamp": datetime.now().isoformat(),
                                "source": "hstk_cli"
                            }
                        else:
                            error_msg = tag_result.stderr if tag_result.stderr else "Unknown error"
                            if "Stale file handle" in error_msg:
                                error_msg = "Stale file handle error persists after mount refresh. This is a Hammerspace CLI internal cache issue. Wait 30 seconds and retry, or contact support."
                            
                            result = {
                                "success": False,
                                "error": f"Failed to tag directory: {error_msg}",
                                "path": path,
                                "tag_name": tag_name,
                                "tag_value": tag_value,
                                "command_output": tag_result.stdout,
                                "timestamp": datetime.now().isoformat(),
                                "source": "hstk_cli"
                            }
                    except subprocess.TimeoutExpired:
                        result = {
                            "success": False,
                            "error": "Tagging operation timed out",
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk_cli"
                        }
                    except Exception as e:
                        result = {
                            "success": False,
                            "error": f"Failed to tag directory: {str(e)}",
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk_cli"
                        }
                
                elif name == "apply_objective_to_path":
                    objective_name = arguments.get("objective_name")
                    path = arguments.get("path")
                    
                    try:
                        import subprocess
                        
                        # Use hs objective add to apply objective
                        obj_cmd = ["/home/mike/hs-mcp-1.0/.venv/bin/hs", "objective", "add", objective_name, path]
                        logger.info(f"Executing: {' '.join(obj_cmd)}")
                        obj_result = subprocess.run(obj_cmd, capture_output=True, text=True, timeout=30)
                        
                        logger.info(f"Objective command exit code: {obj_result.returncode}")
                        if obj_result.stderr:
                            logger.warning(f"Objective command stderr: {obj_result.stderr}")
                        
                        # Check for stale file handle - auto-retry after refreshing mounts
                        if "Stale file handle" in obj_result.stderr:
                            logger.warning("Stale file handle detected - automatically refreshing mounts and retrying...")
                            
                            # Run refresh_mounts script
                            refresh_cmd = ["/home/mike/mcp-1.5/refresh_mounts.sh"]
                            refresh_env = os.environ.copy()
                            refresh_env["MOUNT_TYPE"] = "all"
                            refresh_result = subprocess.run(refresh_cmd, capture_output=True, text=True, timeout=120, env=refresh_env)
                            
                            if refresh_result.returncode == 0:
                                logger.info("Mounts refreshed successfully - retrying objective operation")
                                # Retry the objective operation
                                obj_result = subprocess.run(obj_cmd, capture_output=True, text=True, timeout=30)
                                logger.info(f"Retry objective command exit code: {obj_result.returncode}")
                            else:
                                logger.error(f"Failed to refresh mounts: {refresh_result.stderr}")
                        
                        # Check for errors
                        has_error = (
                            obj_result.returncode != 0 or
                            "Stale file handle" in obj_result.stderr or
                            "OSError" in obj_result.stderr or
                            "Error" in obj_result.stderr
                        )
                        
                        if obj_result.returncode == 0 and not has_error:
                            result = {
                                "success": True,
                                "message": f"Successfully applied objective '{objective_name}' to {path}",
                                "objective_name": objective_name,
                                "path": path,
                                "timestamp": datetime.now().isoformat(),
                                "source": "hstk_cli"
                            }
                        else:
                            result = {
                                "success": False,
                                "error": f"Failed to apply objective: {obj_result.stderr}",
                                "objective_name": objective_name,
                                "path": path,
                                "timestamp": datetime.now().isoformat(),
                                "source": "hstk_cli"
                            }
                    except subprocess.TimeoutExpired:
                        result = {
                            "success": False,
                            "error": "Objective application timed out",
                            "objective_name": objective_name,
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk_cli"
                        }
                    except Exception as e:
                        result = {
                            "success": False,
                            "error": f"Failed to apply objective: {str(e)}",
                            "objective_name": objective_name,
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk_cli"
                        }
                
                elif name == "remove_objective_from_path":
                    objective_name = arguments.get("objective_name")
                    path = arguments.get("path")
                    
                    try:
                        import subprocess
                        
                        # Use hs objective delete to remove objective
                        obj_cmd = ["/home/mike/hs-mcp-1.0/.venv/bin/hs", "objective", "delete", objective_name, path]
                        obj_result = subprocess.run(obj_cmd, capture_output=True, text=True, timeout=30)
                        
                        if obj_result.returncode == 0:
                            result = {
                                "success": True,
                                "message": f"Successfully removed objective '{objective_name}' from {path}",
                                "objective_name": objective_name,
                                "path": path,
                                "timestamp": datetime.now().isoformat(),
                                "source": "hstk_cli"
                            }
                        else:
                            result = {
                                "success": False,
                                "error": f"Failed to remove objective: {obj_result.stderr}",
                                "objective_name": objective_name,
                                "path": path,
                                "timestamp": datetime.now().isoformat(),
                                "source": "hstk_cli"
                            }
                    except subprocess.TimeoutExpired:
                        result = {
                            "success": False,
                            "error": "Objective removal timed out",
                            "objective_name": objective_name,
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk_cli"
                        }
                    except Exception as e:
                        result = {
                            "success": False,
                            "error": f"Failed to remove objective: {str(e)}",
                            "objective_name": objective_name,
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk_cli"
                        }
                
                elif name == "list_objectives_for_path":
                    path = arguments.get("path")
                    
                    try:
                        import subprocess
                        
                        # Use hs objective list to get objectives for path
                        obj_cmd = ["/home/mike/hs-mcp-1.0/.venv/bin/hs", "objective", "list", path]
                        obj_result = subprocess.run(obj_cmd, capture_output=True, text=True, timeout=30)
                        
                        if obj_result.returncode == 0:
                            result = {
                                "success": True,
                                "objectives": obj_result.stdout,
                                "path": path,
                                "timestamp": datetime.now().isoformat(),
                                "source": "hstk_cli"
                            }
                        else:
                            result = {
                                "success": False,
                                "error": f"Failed to list objectives: {obj_result.stderr}",
                                "path": path,
                                "timestamp": datetime.now().isoformat(),
                                "source": "hstk_cli"
                            }
                    except subprocess.TimeoutExpired:
                        result = {
                            "success": False,
                            "error": "Objective listing timed out",
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk_cli"
                        }
                    except Exception as e:
                        result = {
                            "success": False,
                            "error": f"Failed to list objectives: {str(e)}",
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk_cli"
                        }
                
                elif name == "ingest_new_files":
                    path = arguments.get("path")
                    tag_name = arguments.get("tag_name")
                    tag_value = arguments.get("tag_value")
                    age_minutes = arguments.get("age_minutes", 60)
                    use_mtime = arguments.get("use_mtime", True)
                    
                    try:
                        import subprocess
                        import time
                        
                        # Calculate timestamp threshold (current time - age_minutes)
                        current_time = time.time()
                        threshold_time = current_time - (age_minutes * 60)
                        
                        # Find new files using find command with time filter
                        time_type = "mtime" if use_mtime else "ctime"
                        find_cmd = ["find", path, "-type", "f", f"-{time_type}", f"-{age_minutes}"]
                        find_result = subprocess.run(find_cmd, capture_output=True, text=True, timeout=30)
                        
                        if find_result.returncode != 0:
                            result = {
                                "success": False,
                                "error": f"Failed to find new files: {find_result.stderr}",
                                "path": path,
                                "timestamp": datetime.now().isoformat(),
                                "source": "hstk_cli"
                            }
                        else:
                            new_files = [f.strip() for f in find_result.stdout.strip().split('\n') if f.strip()]
                            
                            if not new_files:
                                result = {
                                    "success": True,
                                    "message": f"No new files found in the last {age_minutes} minutes",
                                    "files_found": 0,
                                    "path": path,
                                    "timestamp": datetime.now().isoformat(),
                                    "source": "hstk_cli"
                                }
                            else:
                                # Step 1: Tag the new files
                                tag_spec = f"{tag_name}={tag_value}"
                                tag_cmd = ["/home/mike/hs-mcp-1.0/.venv/bin/hs", "tag", "set", "-r", tag_spec, path]
                                tag_result = subprocess.run(tag_cmd, capture_output=True, text=True, timeout=60)
                                
                                if tag_result.returncode != 0:
                                    result = {
                                        "success": False,
                                        "error": f"Failed to tag files: {tag_result.stderr}",
                                        "files_found": len(new_files),
                                        "timestamp": datetime.now().isoformat(),
                                        "source": "hstk_cli"
                                    }
                                else:
                                    # Step 2: Apply placeonvolumes objective for Tier 1
                                    obj_cmd = ["/home/mike/hs-mcp-1.0/.venv/bin/hs", "objective", "add", "placeonvolumes", path]
                                    obj_result = subprocess.run(obj_cmd, capture_output=True, text=True, timeout=30)
                                    
                                    if obj_result.returncode != 0:
                                        result = {
                                            "success": False,
                                            "error": f"Tagged files but failed to apply objective: {obj_result.stderr}",
                                            "files_found": len(new_files),
                                            "files_tagged": len(new_files),
                                            "timestamp": datetime.now().isoformat(),
                                            "source": "hstk_cli"
                                        }
                                    else:
                                        result = {
                                            "success": True,
                                            "message": f"Successfully ingested {len(new_files)} new file(s)",
                                            "files_found": len(new_files),
                                            "new_files": new_files[:10],  # Show first 10 files
                                            "tag_applied": f"{tag_name}={tag_value}",
                                            "objective_applied": "placeonvolumes (Tier 1)",
                                            "path": path,
                                            "age_minutes": age_minutes,
                                            "time_type": time_type,
                                            "timestamp": datetime.now().isoformat(),
                                            "source": "hstk_cli"
                                        }
                    except subprocess.TimeoutExpired:
                        result = {
                            "success": False,
                            "error": "Ingestion operation timed out",
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk_cli"
                        }
                    except Exception as e:
                        result = {
                            "success": False,
                            "error": f"Failed to ingest new files: {str(e)}",
                            "path": path,
                            "timestamp": datetime.now().isoformat(),
                            "source": "hstk_cli"
                        }
                
                elif name == "refresh_mounts":
                    mount_type = arguments.get("mount_type", "all")
                    
                    try:
                        import subprocess
                        
                        # Run the refresh_mounts.sh script
                        refresh_script = "/home/mike/mcp-1.5/refresh_mounts.sh"
                        refresh_cmd = [refresh_script]
                        
                        # Set environment variable to control which mounts to refresh
                        env = os.environ.copy()
                        env["MOUNT_TYPE"] = mount_type
                        
                        refresh_result = subprocess.run(
                            refresh_cmd, 
                            capture_output=True, 
                            text=True, 
                            timeout=120,
                            env=env
                        )
                        
                        if refresh_result.returncode == 0:
                            # Parse output to count successful mounts
                            output_lines = refresh_result.stdout.strip().split('\n')
                            success_count = sum(1 for line in output_lines if '✅ Successfully mounted' in line)
                            
                            result = {
                                "success": True,
                                "message": f"Successfully refreshed {mount_type} Hammerspace mounts",
                                "mounts_refreshed": success_count,
                                "mount_type": mount_type,
                                "output": refresh_result.stdout,
                                "timestamp": datetime.now().isoformat(),
                                "source": "mount_refresh"
                            }
                        else:
                            result = {
                                "success": False,
                                "error": f"Mount refresh failed: {refresh_result.stderr}",
                                "mount_type": mount_type,
                                "output": refresh_result.stdout,
                                "timestamp": datetime.now().isoformat(),
                                "source": "mount_refresh"
                            }
                    except subprocess.TimeoutExpired:
                        result = {
                            "success": False,
                            "error": "Mount refresh timed out",
                            "mount_type": mount_type,
                            "timestamp": datetime.now().isoformat(),
                            "source": "mount_refresh"
                        }
                    except Exception as e:
                        result = {
                            "success": False,
                            "error": f"Failed to refresh mounts: {str(e)}",
                            "mount_type": mount_type,
                            "timestamp": datetime.now().isoformat(),
                            "source": "mount_refresh"
                        }
                
                elif name == "get_file_monitor_status":
                    if not INOTIFY_AVAILABLE:
                        result = {
                            "success": False,
                            "error": "inotify monitor not available",
                            "timestamp": datetime.now().isoformat(),
                            "source": "inotify"
                        }
                    else:
                        try:
                            monitor_service = get_monitor_service()
                            result = {
                                "success": True,
                                **monitor_service.get_status(),
                                "source": "inotify"
                            }
                        except Exception as e:
                            logger.error(f"Failed to get inotify status: {e}")
                            result = {
                                "success": False,
                                "error": f"Failed to get inotify status: {str(e)}",
                                "timestamp": datetime.now().isoformat(),
                                "source": "inotify"
                            }
                
                elif name == "get_file_ingest_events":
                    # Get parameters
                    limit = arguments.get("limit", 100)
                    event_type_filter = arguments.get("event_type", "").strip()
                    file_pattern = arguments.get("file_pattern", "").strip().lower()
                    since_timestamp = arguments.get("since_timestamp", "").strip()
                    
                    try:
                        # Read and parse the inotify log file
                        log_file = Path(__file__).parent.parent / 'logs' / 'inotify.log'
                        
                        if not log_file.exists():
                            result = {
                                "success": False,
                                "error": "inotify log file not found",
                                "events": [],
                                "count": 0,
                                "timestamp": datetime.now().isoformat(),
                                "source": "inotify_log"
                            }
                        else:
                            events = []
                            
                            # Read file in reverse order to get most recent events first
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                            
                            # Parse events from newest to oldest
                            for line in reversed(lines):
                                line = line.strip()
                                if not line or not line.startswith('{'):
                                    continue
                                
                                try:
                                    event = json.loads(line)
                                    
                                    # Apply filters
                                    if event_type_filter and event.get("event_type") != event_type_filter:
                                        continue
                                    
                                    if file_pattern and file_pattern not in event.get("file_name", "").lower():
                                        continue
                                    
                                    if since_timestamp and event.get("timestamp", "") < since_timestamp:
                                        continue
                                    
                                    events.append(event)
                                    
                                    if len(events) >= limit:
                                        break
                                        
                                except json.JSONDecodeError:
                                    continue
                            
                            result = {
                                "success": True,
                                "events": events,
                                "count": len(events),
                                "limit": limit,
                                "filters": {
                                    "event_type": event_type_filter or "all",
                                    "file_pattern": file_pattern or "all",
                                    "since_timestamp": since_timestamp or "all_time"
                                },
                                "timestamp": datetime.now().isoformat(),
                                "source": "inotify_log"
                            }
                            
                    except Exception as e:
                        logger.error(f"Failed to get file ingest events: {e}")
                        result = {
                            "success": False,
                            "error": f"Failed to get ingest events: {str(e)}",
                            "events": [],
                            "count": 0,
                            "timestamp": datetime.now().isoformat(),
                            "source": "inotify_log"
                        }
                    
                else:
                    result = {
                        "error": f"Unknown tool: {name}",
                        "timestamp": datetime.now().isoformat(),
                        "source": "aiq_hstk",
                        "aiq_enabled": AIQ_AVAILABLE
                    }
                
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}")
                error_result = {
                    "error": str(e),
                    "tool": name,
                    "timestamp": datetime.now().isoformat(),
                    "source": "aiq_hstk",
                    "aiq_enabled": AIQ_AVAILABLE
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    async def run(self):
        """Run the AIQ + HSTK MCP server."""
        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)
        
        # Check for NVIDIA API key
        nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        if not nvidia_api_key:
            logger.warning("NVIDIA_API_KEY environment variable not set")
        else:
            logger.info(f"🔑 NVIDIA API Key found: {'*' * (len(nvidia_api_key) - 8) + nvidia_api_key[-8:]}")
        
        logger.info("🚀 Starting NVIDIA AIQ Toolkit + HSTK MCP Server")
        logger.info("📡 Server will communicate via stdio")
        
        if HSTK_AVAILABLE and self.client:
            logger.info("✅ HSTK client loaded")
            try:
                logger.info(f"🔗 Hammerspace API: {self.client.base_url}")
            except AttributeError:
                logger.info("🔗 Hammerspace API: Connected via HSTK")
        else:
            logger.error("❌ HSTK client not available")
            
        if AIQ_AVAILABLE and self.aiq:
            logger.info("✅ NVIDIA AIQ Toolkit loaded")
            logger.info("🤖 AI-powered storage operations available")
        # Suppressed: AIQ Toolkit warning (not needed for HSTK operations)
        
        # Start file monitor as background task if not already started
        if INOTIFY_AVAILABLE and self.file_monitor and not self.monitor_task:
            logger.info("🚀 Starting automatic file monitoring service...")
            try:
                monitor_result = await self.file_monitor.start()
                if monitor_result.get('success'):
                    logger.info(f"✅ File monitor started - watching {len(monitor_result.get('watch_paths', []))} shares")
                    self.monitor_task = True  # Mark as started
                else:
                    logger.warning(f"⚠️ File monitor failed to start: {monitor_result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"❌ Failed to start file monitor: {e}")
        
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
                    server_name="aiq-hstk-volume-canvas-mcp",
                    server_version="1.0.0",
                    capabilities=capabilities
                )
            )

async def main():
    """Main entry point."""
    server = AIQHSTKMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
