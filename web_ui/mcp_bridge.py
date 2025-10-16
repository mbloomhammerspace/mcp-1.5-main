#!/usr/bin/env python3
"""
MCP Bridge - Simple HTTP API bridge to communicate with the running MCP server
This bridge allows the web UI to communicate with the existing MCP server service
without starting new instances.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def call_mcp_tool_via_cli(tool_name: str, arguments: dict) -> dict:
    """Call MCP tool via command line interface"""
    try:
        # For now, we'll implement a simple bridge that calls the tools directly
        # This is a temporary solution until we can implement proper MCP communication
        
        # Map tool names to their implementations
        if tool_name == "tag_directory_recursive":
            return tag_directory_recursive(arguments)
        elif tool_name == "check_tagged_files_alignment":
            return check_tagged_files_alignment(arguments)
        elif tool_name == "apply_objective_to_path":
            return apply_objective_to_path(arguments)
        elif tool_name == "remove_objective_from_path":
            return remove_objective_from_path(arguments)
        elif tool_name == "list_objectives_for_path":
            return list_objectives_for_path(arguments)
        elif tool_name == "get_file_monitor_status":
            return get_file_monitor_status(arguments)
        else:
            return {"error": f"Tool {tool_name} not implemented in bridge"}
    
    except Exception as e:
        return {"error": f"Error calling tool {tool_name}: {str(e)}"}

def get_available_tools() -> List[dict]:
    """Get list of available tools"""
    return [
        {
            "name": "tag_directory_recursive",
            "description": "Tag all files in a directory recursively with a given tag name and value",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to tag"},
                    "tag_name": {"type": "string", "description": "Tag name"},
                    "tag_value": {"type": "string", "description": "Tag value"}
                },
                "required": ["path", "tag_name", "tag_value"]
            }
        },
        {
            "name": "check_tagged_files_alignment",
            "description": "Check alignment status of files with a specific tag",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tag_name": {"type": "string", "description": "Tag name to search for"},
                    "tag_value": {"type": "string", "description": "Tag value to search for"},
                    "share_path": {"type": "string", "description": "Share path to search in"}
                },
                "required": ["tag_name", "tag_value"]
            }
        },
        {
            "name": "apply_objective_to_path",
            "description": "Apply an objective (like tier0 promotion) to a path",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "objective_name": {"type": "string", "description": "Objective name"},
                    "path": {"type": "string", "description": "Path to apply objective to"}
                },
                "required": ["objective_name", "path"]
            }
        },
        {
            "name": "remove_objective_from_path",
            "description": "Remove an objective from a path",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "objective_name": {"type": "string", "description": "Objective name"},
                    "path": {"type": "string", "description": "Path to remove objective from"}
                },
                "required": ["objective_name", "path"]
            }
        },
        {
            "name": "list_objectives_for_path",
            "description": "List objectives applied to a path",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to check objectives for"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "get_file_monitor_status",
            "description": "Get status of the file monitoring service",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        }
    ]

def tag_directory_recursive(arguments: dict) -> dict:
    """Tag directory recursively using HSTK CLI"""
    try:
        path = arguments.get("path")
        tag_name = arguments.get("tag_name")
        tag_value = arguments.get("tag_value")
        
        if not all([path, tag_name, tag_value]):
            return {"error": "Missing required parameters: path, tag_name, tag_value"}
        
        # Use HSTK CLI to tag directory
        cmd = ["/home/ubuntu/.local/bin/hs", "tag", "set", f"{tag_name}={tag_value}", path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="/mnt/anvil/hub")
        
        if result.returncode == 0:
            return {"success": True, "message": f"Successfully tagged {path} with {tag_name}={tag_value}"}
        else:
            return {"error": f"HSTK CLI error: {result.stderr}"}
    
    except Exception as e:
        return {"error": f"Error in tag_directory_recursive: {str(e)}"}

def check_tagged_files_alignment(arguments: dict) -> dict:
    """Check alignment of tagged files using HSTK CLI"""
    try:
        tag_name = arguments.get("tag_name")
        tag_value = arguments.get("tag_value")
        share_path = arguments.get("share_path", "/mnt/anvil")
        
        if not all([tag_name, tag_value]):
            return {"error": "Missing required parameters: tag_name, tag_value"}
        
        # Use HSTK CLI to find files with tag
        cmd = ["/home/ubuntu/.local/bin/hs", "tag", "get", f"{tag_name}={tag_value}", share_path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=share_path)
        
        if result.returncode == 0:
            # Parse the output to extract file information
            files = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    files.append({"path": line.strip()})
            
            return {
                "success": True, 
                "tagged_files": files,
                "count": len(files),
                "tag": f"{tag_name}={tag_value}"
            }
        else:
            return {"error": f"HSTK CLI error: {result.stderr}"}
    
    except Exception as e:
        return {"error": f"Error in check_tagged_files_alignment: {str(e)}"}

def apply_objective_to_path(arguments: dict) -> dict:
    """Apply objective to path using HSTK CLI"""
    try:
        objective_name = arguments.get("objective_name")
        path = arguments.get("path")
        
        if not all([objective_name, path]):
            return {"error": "Missing required parameters: objective_name, path"}
        
        # Map user-friendly objective names to actual Hammerspace objective names
        objective_mapping = {
            "Place-on-tier0": "place-on-tier0",
            "Promote to tier0": "placeontier1-alpha-site",  # Legacy support
        }
        
        # Use mapped objective name if available, otherwise use the original name
        actual_objective_name = objective_mapping.get(objective_name, objective_name)
        
        # Use HSTK CLI to apply objective
        cmd = ["/home/ubuntu/.local/bin/hs", "objective", "add", actual_objective_name, path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=path)
        
        if result.returncode == 0:
            return {"success": True, "message": f"Successfully applied {objective_name} to {path}"}
        else:
            return {"error": f"HSTK CLI error: {result.stderr}"}
    
    except Exception as e:
        return {"error": f"Error in apply_objective_to_path: {str(e)}"}

def remove_objective_from_path(arguments: dict) -> dict:
    """Remove objective from path using HSTK CLI"""
    try:
        objective_name = arguments.get("objective_name")
        path = arguments.get("path")
        
        if not all([objective_name, path]):
            return {"error": "Missing required parameters: objective_name, path"}
        
        # Map user-friendly objective names to actual Hammerspace objective names
        objective_mapping = {
            "Place-on-tier0": "place-on-tier0",
            "Promote to tier0": "placeontier1-alpha-site",  # Legacy support
        }
        
        # Use mapped objective name if available, otherwise use the original name
        actual_objective_name = objective_mapping.get(objective_name, objective_name)
        
        # Use HSTK CLI to remove objective
        cmd = ["/home/ubuntu/.local/bin/hs", "objective", "delete", actual_objective_name, path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=path)
        
        if result.returncode == 0:
            return {"success": True, "message": f"Successfully removed {objective_name} from {path}"}
        else:
            return {"error": f"HSTK CLI error: {result.stderr}"}
    
    except Exception as e:
        return {"error": f"Error in remove_objective_from_path: {str(e)}"}

def list_objectives_for_path(arguments: dict) -> dict:
    """List objectives for path using HSTK CLI"""
    try:
        path = arguments.get("path")
        
        if not path:
            return {"error": "Missing required parameter: path"}
        
        # Use HSTK CLI to check for applied objectives
        # First, get the list of available objectives to check against
        cmd_list = ["/home/ubuntu/.local/bin/hs", "objective", "list", path]
        result_list = subprocess.run(cmd_list, capture_output=True, text=True, cwd=path)
        
        if result_list.returncode != 0:
            return {"error": f"HSTK CLI error listing objectives: {result_list.stderr}"}
        
        # Extract objective names from the system list
        available_objectives = []
        for line in result_list.stdout.strip().split('\n'):
            if "OBJECTIVE = SLO(" in line:
                # Extract objective name from line like: |OBJECTIVE = SLO('objective-name'),
                import re
                match = re.search(r"SLO\('([^']+)'\)", line)
                if match:
                    available_objectives.append(match.group(1))
        
        # Check which objectives are actually applied to this path
        applied_objectives = []
        for obj_name in available_objectives:
            cmd_has = ["/home/ubuntu/.local/bin/hs", "objective", "has", obj_name, path]
            result_has = subprocess.run(cmd_has, capture_output=True, text=True, cwd=path)
            
            if result_has.returncode == 0 and result_has.stdout.strip() == "TRUE":
                applied_objectives.append({"name": obj_name, "applied": True})
        
        return {
            "success": True,
            "objectives": applied_objectives,
            "path": path,
            "total_applied": len(applied_objectives)
        }
    
    except Exception as e:
        return {"error": f"Error in list_objectives_for_path: {str(e)}"}

def get_file_monitor_status(arguments: dict) -> dict:
    """Get file monitor status"""
    try:
        # Check if file monitor is running by looking at the log file
        log_file = "/home/ubuntu/mcp-1.5-main/logs/inotify.log"
        if Path(log_file).exists():
            # Get recent log entries
            result = subprocess.run(['tail', '-10', log_file], capture_output=True, text=True)
            if result.returncode == 0:
                return {
                    "success": True,
                    "status": "running",
                    "recent_activity": result.stdout.strip().split('\n')[-5:]  # Last 5 lines
                }
        
        return {"success": False, "status": "not_running"}
    
    except Exception as e:
        return {"error": f"Error in get_file_monitor_status: {str(e)}"}
