#!/usr/bin/env python3
"""
HTTP MCP Server Wrapper
Provides HTTP endpoints for MCP services with direct implementation.
"""

import asyncio
import json
import logging
import threading
import time
from typing import Dict, Any, Optional
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('http_mcp_server')

class HTTPMCPServer:
    """HTTP wrapper for MCP services with direct implementation."""
    
    def __init__(self, service_type: str = "main", port: int = 8000):
        self.service_type = service_type
        self.port = port
        if service_type == "docs":
            title = "RAG Document Management API"
            description = "Document management and RAG (Retrieval-Augmented Generation) capabilities for the Federated Storage MCP system"
        else:
            title = f"Federated Storage MCP {service_type.title()} Server"
            description = f"HTTP API for the Federated Storage MCP {service_type} service"
            
        self.app = FastAPI(
            title=title,
            description=description,
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json"
        )
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup HTTP routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint with API information."""
            if self.service_type == "docs":
                service_name = "rag-document-management"
                description = "Document management and RAG (Retrieval-Augmented Generation) capabilities"
            else:
                service_name = f"federated-storage-mcp-{self.service_type}"
                description = f"HTTP API for the Federated Storage MCP {self.service_type} service"
                
            return {
                "service": service_name,
                "version": "1.0.0",
                "description": description,
                "endpoints": {
                    "health": "/health",
                    "mcp_health": "/mcp/health",
                    "tools": "/tools/{tool_name}",
                    "resources": "/resources/{resource_name}",
                    "systems": "/systems",
                    "sync": "/sync"
                },
                "documentation": {
                    "swagger_ui": "/docs",
                    "redoc": "/redoc",
                    "openapi_schema": "/openapi.json"
                }
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": f"federated-storage-mcp-{self.service_type}",
                "port": self.port,
                "timestamp": time.time()
            }
        
        @self.app.get("/mcp/health")
        async def mcp_health_check():
            """MCP-specific health check."""
            return {
                "status": "healthy",
                "service": f"federated-storage-mcp-{self.service_type}",
                "mcp_available": True,
                "port": self.port
            }
        
        @self.app.get("/")
        async def root():
            """Root endpoint with service information."""
            return {
                "service": f"federated-storage-mcp-{self.service_type}",
                "version": "1.0.0",
                "endpoints": {
                    "health": "/health",
                    "mcp_health": "/mcp/health",
                    "tools": "/tools/{tool_name}",
                    "resources": "/resources/{resource_name}",
                    "systems": "/systems",
                    "sync": "/sync"
                }
            }
        
        @self.app.post("/tools/{tool_name}")
        async def call_tool(tool_name: str, request: Dict[str, Any]):
            """Call an MCP tool."""
            try:
                # Direct implementation of MCP tools
                if self.service_type == "main":
                    result = await self._call_main_tool(tool_name, request)
                else:
                    result = await self._call_docs_tool(tool_name, request)
                
                # Format result to match MCP client expectations
                if isinstance(result, str):
                    formatted_result = {
                        "content": [
                            {"text": result}
                        ]
                    }
                else:
                    formatted_result = result
                
                return {
                    "tool": tool_name,
                    "result": formatted_result,
                    "arguments": request,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                return {
                    "tool": tool_name,
                    "error": str(e),
                    "arguments": request,
                    "timestamp": time.time()
                }
        
        @self.app.get("/resources/{resource_name}")
        async def get_resource(resource_name: str):
            """Get an MCP resource."""
            try:
                if self.service_type == "main":
                    content = await self._get_main_resource(resource_name)
                else:
                    content = await self._get_docs_resource(resource_name)
                
                return {
                    "resource": resource_name,
                    "content": content,
                    "timestamp": time.time()
                }
            except Exception as e:
                return {
                    "resource": resource_name,
                    "error": str(e),
                    "timestamp": time.time()
                }
        
        @self.app.get("/tools")
        async def list_tools():
            """List available MCP tools."""
            tools = {
                "main": [
                    "list_shares",
                    "list_nodes", 
                    "list_volumes",
                    "search_files",
                    "get_file_count",
                    "create_share",
                    "list_objectives",
                    "assimilate_data",
                    "get_task_status",
                    "get_system_status"
                ],
                "docs": [
                    "get_api_reference",
                    "get_tool_help",
                    "get_endpoint_mapping",
                    "get_examples",
                    "get_configuration_guide"
                ]
            }
            
            return {
                "service": self.service_type,
                "tools": tools.get(self.service_type, []),
                "count": len(tools.get(self.service_type, []))
            }
        
        @self.app.get("/resources")
        async def list_resources():
            """List available MCP resources."""
            resources = {
                "main": [
                    "storage_nodes",
                    "storage_volumes", 
                    "shares",
                    "multi_system_overview"
                ],
                "docs": [
                    "api_reference_json",
                    "tool_schemas"
                ]
            }
            
            return {
                "service": self.service_type,
                "resources": resources.get(self.service_type, []),
                "count": len(resources.get(self.service_type, []))
            }
        
        @self.app.get("/systems")
        async def list_systems():
            """List all available storage systems."""
            try:
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
                from multi_config_manager import MultiConfigManager
                manager = MultiConfigManager()
                configs = manager.list_configurations()
                active_config = manager.get_active_configuration()
                
                return {
                    "systems": configs,
                    "active_system": active_config,
                    "total_systems": len(configs)
                }
            except Exception as e:
                logger.error(f"Failed to list systems: {e}")
                return {"error": str(e)}
        
        @self.app.post("/sync")
        async def sync_systems(request: Dict[str, Any]):
            """Sync storage systems."""
            try:
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
                from multi_config_manager import MultiConfigManager
                manager = MultiConfigManager()
                
                system_name = request.get("system_name")
                if system_name:
                    # Sync single system
                    result = await manager.sync_single_system(system_name)
                else:
                    # Sync all systems
                    result = await manager.sync_all_systems()
                
                return result
            except Exception as e:
                logger.error(f"Failed to sync systems: {e}")
                return {"error": str(e)}
    
    async def _call_main_tool(self, tool_name: str, request: Dict[str, Any]) -> str:
        """Call a main service tool."""
        try:
            if tool_name == "get_system_status":
                return await self._get_system_status()
            elif tool_name == "get_file_count":
                query = request.get("query", "*") # Extract query parameter
                return await self._get_file_count(query) # Pass query parameter
            elif tool_name == "list_shares":
                return await self._list_shares()
            elif tool_name == "list_nodes":
                return await self._list_nodes()
            elif tool_name == "list_volumes":
                return await self._list_volumes()
            elif tool_name == "get_queue_stats":
                return await self._get_queue_stats()
            elif tool_name == "get_queue_depth":
                return await self._get_queue_depth()
            elif tool_name == "get_task_queue_status":
                return await self._get_task_queue_status()
            elif tool_name == "list_objectives":
                return await self._list_objectives()
            elif tool_name == "create_objective":
                return await self._create_objective(request)
            elif tool_name == "delete_objective":
                objective_uuid = request.get("objective_uuid")
                return await self._delete_objective(objective_uuid)
            elif tool_name == "get_objective_templates":
                return await self._get_objective_templates()
            elif tool_name == "create_data_movement_job":
                return await self._create_data_movement_job(request)
            elif tool_name == "list_data_movement_jobs":
                return await self._list_data_movement_jobs()
            elif tool_name == "get_data_movement_job":
                job_uuid = request.get("job_uuid")
                return await self._get_data_movement_job(job_uuid)
            elif tool_name == "get_system_configuration":
                return await self._get_system_configuration()
            elif tool_name == "get_resource_utilization":
                return await self._get_resource_utilization()
            elif tool_name == "get_performance_metrics":
                return await self._get_performance_metrics()
            elif tool_name == "get_comprehensive_monitoring":
                return await self._get_comprehensive_monitoring()
            elif tool_name == "copy_files_by_tags":
                return await self._copy_files_by_tags(request)
            elif tool_name == "move_files_by_tags":
                return await self._move_files_by_tags(request)
            elif tool_name == "delete_files_by_tags":
                return await self._delete_files_by_tags(request)
            elif tool_name == "replicate_files_by_tags":
                return await self._replicate_files_by_tags(request)
            elif tool_name == "copy_file":
                return await self._copy_file(request)
            elif tool_name == "move_file":
                return await self._move_file(request)
            elif tool_name == "copy_directory":
                return await self._copy_directory(request)
            elif tool_name == "replicate_share":
                return await self._replicate_share(request)
            elif tool_name == "mcp_clone":
                return await self._mcp_clone(request)
            else:
                return f"Tool '{tool_name}' not implemented"
        except Exception as e:
            return f"Error calling tool '{tool_name}': {str(e)}"
    
    async def _call_docs_tool(self, tool_name: str, request: Dict[str, Any]) -> str:
        """Call a docs service tool."""
        try:
            # Import the document service
            from mcp_docs_service import mcp_docs_service
            
            if tool_name == "list_documents":
                result = await mcp_docs_service.list_documents()
                return json.dumps(result, indent=2)
            elif tool_name == "get_document_content":
                filename = request.get("filename", "")
                result = await mcp_docs_service.get_document_content(filename)
                return json.dumps(result, indent=2)
            elif tool_name == "search_documents":
                query = request.get("query", "")
                top_k = request.get("top_k", 5)
                result = await mcp_docs_service.search_documents(query, top_k)
                return json.dumps(result, indent=2)
            elif tool_name == "get_context_for_query":
                query = request.get("query", "")
                result = await mcp_docs_service.get_context_for_query(query)
                return json.dumps(result, indent=2)
            elif tool_name == "get_document_stats":
                result = await mcp_docs_service.get_document_stats()
                return json.dumps(result, indent=2)
            elif tool_name == "get_objectives_context":
                query = request.get("query", "")
                result = await mcp_docs_service.get_objectives_context(query)
                return json.dumps(result, indent=2)
            elif tool_name == "get_api_reference":
                return await self._get_api_reference()
            elif tool_name == "get_tool_help":
                return await self._get_tool_help()
            else:
                return f"Tool {tool_name} not implemented yet"
        except Exception as e:
            return f"Error calling docs tool {tool_name}: {str(e)}"
    
    async def _get_main_resource(self, resource_name: str) -> str:
        """Get a main service resource."""
        if resource_name == "storage_nodes":
            return await self._list_nodes()
        elif resource_name == "storage_volumes":
            return await self._list_volumes()
        elif resource_name == "shares":
            return await self._list_shares()
        elif resource_name == "multi_system_overview":
            return await self._get_multi_system_overview()
        else:
            return f"Resource {resource_name} not found"
    
    async def _get_docs_resource(self, resource_name: str) -> str:
        """Get a docs service resource."""
        if resource_name == "api_reference_json":
            return await self._get_api_reference()
        else:
            return f"Resource {resource_name} not found"
    
    # Main service tool implementations
    async def _list_shares(self) -> str:
        """List storage shares."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                shares = await client.get_shares()
                
                # Convert to JSON format with actual data
                share_data = []
                for share in shares:
                    share_data.append({
                        "uuid": share.uuid,
                        "name": share.name,
                        "path": share.path,
                        "status": "active",
                        "totalNumberOfFiles": share.total_number_of_files or 0
                    })
                
                return json.dumps(share_data, indent=2)
                
        except Exception as e:
            return f"Error listing shares: {str(e)}"
    
    async def _list_nodes(self) -> str:
        """List storage nodes."""
        try:
            # Get real data from Hammerspace API
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from multi_config_manager import MultiConfigManager
            
            config_manager = MultiConfigManager()
            config = config_manager.get_active_configuration()
            if not config:
                return json.dumps([], indent=2)
            
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            
            hammerspace_config = HammerspaceConfig(
                base_url=config["base_url"],
                username=config["username"],
                password=config["password"],
                verify_ssl=config.get("verify_ssl", True),
                timeout=config.get("timeout", 30)
            )
            
            async with HammerspaceClient(hammerspace_config) as client:
                nodes = await client.get_nodes()
                # Convert to simple format for the WebUI
                node_data = []
                for node in nodes:
                    node_data.append({
                        "name": node.name,
                        "status": "online" if node.state == "OK" else "offline",
                        "capacity": "Unknown",  # API doesn't provide capacity directly
                        "used": "Unknown",      # API doesn't provide used space directly
                        "uuid": node.uuid,
                        "node_type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                        "endpoint": node.endpoint
                    })
                return json.dumps(node_data, indent=2)
        except Exception as e:
            logger.error(f"Error listing nodes: {str(e)}")
            return f"Error listing nodes: {str(e)}"
    
    async def _list_volumes(self) -> str:
        """List storage volumes."""
        try:
            # Get real data from Hammerspace API
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from multi_config_manager import MultiConfigManager
            
            config_manager = MultiConfigManager()
            config = config_manager.get_active_configuration()
            if not config:
                return json.dumps([], indent=2)
            
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            
            hammerspace_config = HammerspaceConfig(
                base_url=config["base_url"],
                username=config["username"],
                password=config["password"],
                verify_ssl=config.get("verify_ssl", True),
                timeout=config.get("timeout", 30)
            )
            
            async with HammerspaceClient(hammerspace_config) as client:
                volumes = await client.get_storage_volumes()
                # Convert to simple format for the WebUI
                volume_data = []
                for volume in volumes:
                    # Format size in human readable format
                    size_str = "Unknown"
                    if hasattr(volume, 'size_bytes') and volume.size_bytes:
                        size_bytes = volume.size_bytes
                        if size_bytes >= 1024**4:  # TB
                            size_str = f"{size_bytes / (1024**4):.1f}TB"
                        elif size_bytes >= 1024**3:  # GB
                            size_str = f"{size_bytes / (1024**3):.1f}GB"
                        elif size_bytes >= 1024**2:  # MB
                            size_str = f"{size_bytes / (1024**2):.1f}MB"
                        else:
                            size_str = f"{size_bytes}B"
                    
                    volume_data.append({
                        "name": volume.name,
                        "size": size_str,
                        "status": "active" if volume.state == "OK" else "inactive",
                        "uuid": volume.uuid,
                        "volume_type": volume.volume_type,
                        "node_uuid": volume.node_uuid
                    })
                return json.dumps(volume_data, indent=2)
        except Exception as e:
            logger.error(f"Error listing volumes: {str(e)}")
            return f"Error listing volumes: {str(e)}"
    
    async def _search_files(self, query: str) -> str:
        """Search for files."""
        try:
            # Mock implementation
            files = [
                {"name": f"file1_{query}.txt", "path": f"/mnt/share1/{query}", "size": "1MB"},
                {"name": f"file2_{query}.pdf", "path": f"/mnt/share2/{query}", "size": "5MB"},
                {"name": f"file3_{query}.doc", "path": f"/mnt/share3/{query}", "size": "2MB"}
            ]
            return json.dumps(files, indent=2)
        except Exception as e:
            return f"Error searching files: {str(e)}"
    
    async def _get_file_count(self, query: str = "*") -> str:
        """Get file count."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                count = await client.get_file_count(query)
                return f"File count for '{query}': {count} files"
                
        except Exception as e:
            return f"Error getting file count: {str(e)}"
    
    async def _get_system_status(self) -> str:
        """Get system status."""
        try:
            # Mock implementation
            status = {
                "overall": "healthy",
                "nodes_online": 2,
                "nodes_total": 3,
                "storage_used": "8TB",
                "storage_total": "20TB",
                "shares_active": 3
            }
            return json.dumps(status, indent=2)
        except Exception as e:
            return f"Error getting system status: {str(e)}"
    
    async def _get_queue_stats(self) -> str:
        """Get queue statistics."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                stats = client.get_queue_stats()
                return f"Queue Statistics: {stats}"
                
        except Exception as e:
            return f"Error getting queue stats: {str(e)}"
    
    async def _get_queue_depth(self) -> str:
        """Get current queue depth."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                depth = await client.get_queue_depth()
                return f"Current queue depth: {depth}"
                
        except Exception as e:
            return f"Error getting queue depth: {str(e)}"
    
    async def _get_task_queue_status(self) -> str:
        """Get task queue status from Hammerspace API."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                status = await client.get_task_queue_status()
                return f"Task Queue Status: {status}"
                
        except Exception as e:
            return f"Error getting task queue status: {str(e)}"
    
    # Objectives Methods
    
    async def _list_objectives(self) -> str:
        """List all objectives."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                objectives = await client.get_objectives()
                if not objectives:
                    return "No objectives found"
                
                result = "📋 **Objectives List**\n\n"
                for obj in objectives:
                    result += f"• **{obj.name}** ({obj.objective_type.value})\n"
                    result += f"  - State: {obj.state.value}\n"
                    result += f"  - Description: {obj.description or 'No description'}\n"
                    if obj.source_path:
                        result += f"  - Source: {obj.source_path}\n"
                    if obj.destination_path:
                        result += f"  - Destination: {obj.destination_path}\n"
                    result += f"  - Created: {obj.created or 'Unknown'}\n\n"
                
                return result
                
        except Exception as e:
            return f"Error listing objectives: {str(e)}"
    
    async def _create_objective(self, request: Dict[str, Any]) -> str:
        """Create a new objective."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                objective = await client.create_objective(request)
                return f"✅ **Objective Created Successfully**\n\n**Name**: {objective.name}\n**Type**: {objective.objective_type.value}\n**State**: {objective.state.value}\n**UUID**: {objective.uuid}"
                
        except Exception as e:
            return f"Error creating objective: {str(e)}"
    
    async def _delete_objective(self, objective_uuid: str) -> str:
        """Delete an objective."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                success = await client.delete_objective(objective_uuid)
                if success:
                    return f"✅ **Objective Deleted Successfully**\n\n**UUID**: {objective_uuid}"
                else:
                    return f"❌ **Failed to delete objective**\n\n**UUID**: {objective_uuid}"
                
        except Exception as e:
            return f"Error deleting objective: {str(e)}"
    
    async def _get_objective_templates(self) -> str:
        """Get objective templates."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                templates = client.get_objective_templates()
                
                result = "📋 **Objective Templates**\n\n"
                for template in templates:
                    result += f"## {template.name}\n"
                    result += f"**Type**: {template.objective_type.value}\n"
                    result += f"**Description**: {template.description}\n"
                    result += f"**Source Pattern**: {template.source_pattern}\n"
                    result += f"**Destination Pattern**: {template.destination_pattern}\n"
                    result += f"**Parameters**: {template.parameters}\n"
                    if template.schedule:
                        result += f"**Schedule**: {template.schedule}\n"
                    result += f"**Examples**:\n"
                    for example in template.examples:
                        result += f"  - {example}\n"
                    result += "\n"
                
                return result
                
        except Exception as e:
            return f"Error getting objective templates: {str(e)}"
    
    # Data Movement Methods
    
    async def _create_data_movement_job(self, request: Dict[str, Any]) -> str:
        """Create a data movement job."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient, DataMovementRequest, DataMovementType
            from src.config import HammerspaceConfig
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                # Convert request to DataMovementRequest
                movement_request = DataMovementRequest(
                    movement_type=DataMovementType(request.get("movement_type", "FILE_COPY")),
                    source_path=request.get("source_path", ""),
                    destination_path=request.get("destination_path", ""),
                    source_share_uuid=request.get("source_share_uuid"),
                    destination_share_uuid=request.get("destination_share_uuid"),
                    source_volume_uuid=request.get("source_volume_uuid"),
                    destination_volume_uuid=request.get("destination_volume_uuid"),
                    overwrite=request.get("overwrite", False),
                    preserve_metadata=request.get("preserve_metadata", True),
                    verify_checksum=request.get("verify_checksum", True),
                    priority=request.get("priority", 5),
                    schedule=request.get("schedule"),
                    parameters=request.get("parameters", {})
                )
                
                job = await client.create_data_movement_job(movement_request)
                return f"✅ **Data Movement Job Created Successfully**\n\n**Name**: {job.name}\n**Type**: {job.movement_type.value}\n**Status**: {job.status.value}\n**UUID**: {job.uuid}\n**Source**: {job.source_path}\n**Destination**: {job.destination_path}"
                
        except Exception as e:
            return f"Error creating data movement job: {str(e)}"
    
    async def _list_data_movement_jobs(self) -> str:
        """List all data movement jobs."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                jobs = await client.get_data_movement_jobs()
                if not jobs:
                    return "No data movement jobs found"
                
                result = "📋 **Data Movement Jobs**\n\n"
                for job in jobs:
                    result += f"• **{job.name}** ({job.movement_type.value})\n"
                    result += f"  - Status: {job.status.value}\n"
                    result += f"  - Progress: {job.progress}%\n"
                    result += f"  - Source: {job.source_path}\n"
                    result += f"  - Destination: {job.destination_path}\n"
                    if job.file_count:
                        result += f"  - Files: {job.file_count}\n"
                    if job.total_size_bytes:
                        result += f"  - Size: {job.total_size_bytes} bytes\n"
                    result += f"  - Created: {job.created or 'Unknown'}\n\n"
                
                return result
                
        except Exception as e:
            return f"Error listing data movement jobs: {str(e)}"
    
    async def _get_data_movement_job(self, job_uuid: str) -> str:
        """Get specific data movement job."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                job = await client.get_data_movement_job(job_uuid)
                return f"📋 **Data Movement Job Details**\n\n**Name**: {job.name}\n**Type**: {job.movement_type.value}\n**Status**: {job.status.value}\n**Progress**: {job.progress}%\n**Source**: {job.source_path}\n**Destination**: {job.destination_path}\n**UUID**: {job.uuid}\n**Created**: {job.created}\n**Started**: {job.started}\n**Completed**: {job.completed}\n**Error**: {job.error_message or 'None'}"
                
        except Exception as e:
            return f"Error getting data movement job: {str(e)}"
    
    async def _get_system_configuration(self) -> str:
        """Get system configuration and settings."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return json.dumps({"error": "No active Hammerspace configuration found"})
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                # Get system components
                nodes = await client.get_nodes()
                volumes = await client.get_storage_volumes()
                shares = await client.get_shares()
                objectives = await client.get_objectives()
                
                # Build configuration summary
                config_data = {
                    "system_info": {
                        "base_url": active_config['base_url'],
                        "username": active_config['username'],
                        "verify_ssl": active_config.get('verify_ssl', False),
                        "timeout": active_config.get('timeout', 30)
                    },
                    "storage_configuration": {
                        "nodes": {
                            "total": len(nodes),
                            "details": [
                                {
                                    "name": node.name,
                                    "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                                    "status": node.state,
                                    "endpoint": node.endpoint
                                } for node in nodes
                            ]
                        },
                        "volumes": {
                            "total": len(volumes),
                            "details": [
                                {
                                    "name": volume.name,
                                    "state": volume.state.value if hasattr(volume.state, 'value') else str(volume.state),
                                    "size": volume.size if hasattr(volume, 'size') else "Unknown"
                                } for volume in volumes
                            ]
                        },
                        "shares": {
                            "total": len(shares),
                            "details": [
                                {
                                    "name": share.name,
                                    "path": share.path,
                                    "status": "active"  # Shares are considered active if they exist
                                } for share in shares
                            ]
                        },
                        "objectives": {
                            "total": len(objectives),
                            "details": [
                                {
                                    "name": obj.name,
                                    "type": obj.objective_type.value if hasattr(obj.objective_type, 'value') else str(obj.objective_type),
                                    "state": obj.state.value if hasattr(obj.state, 'value') else str(obj.state)
                                } for obj in objectives
                            ]
                        }
                    }
                }
                
                return json.dumps(config_data, indent=2)
                
        except Exception as e:
            return f"Error getting system configuration: {str(e)}"
    
    async def _get_resource_utilization(self) -> str:
        """Get resource utilization across all systems."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return json.dumps({"error": "No active Hammerspace configuration found"})
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                # Get system components
                nodes = await client.get_nodes()
                volumes = await client.get_storage_volumes()
                shares = await client.get_shares()
                
                # Get file counts for utilization metrics
                total_files = await client.get_file_count()
                
                # Calculate utilization metrics
                utilization_data = {
                    "storage_utilization": {
                        "total_nodes": len(nodes),
                        "active_nodes": len([n for n in nodes if n.state == "OK"]),
                        "total_volumes": len(volumes),
                        "active_volumes": len([v for v in volumes if (v.state.value == "UP" if hasattr(v.state, 'value') else v.state == "UP")]),
                        "total_shares": len(shares),
                        "active_shares": len(shares),  # All shares are considered active
                        "total_files": total_files
                    },
                    "node_utilization": [
                        {
                            "name": node.name,
                            "status": node.state,
                            "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                            "endpoint": node.endpoint,
                            "utilization": "Unknown"  # API doesn't provide detailed utilization
                        } for node in nodes
                    ],
                    "volume_utilization": [
                        {
                            "name": volume.name,
                            "state": volume.state.value if hasattr(volume.state, 'value') else str(volume.state),
                            "utilization": "Unknown"  # API doesn't provide detailed utilization
                        } for volume in volumes
                    ],
                    "share_utilization": [
                        {
                            "name": share.name,
                            "path": share.path,
                            "status": "active",  # Shares are considered active if they exist
                            "file_count": share.total_number_of_files or 0
                        } for share in shares
                    ]
                }
                
                return json.dumps(utilization_data, indent=2)
                
        except Exception as e:
            return f"Error getting resource utilization: {str(e)}"
    
    async def _get_performance_metrics(self) -> str:
        """Get performance metrics and system health."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return json.dumps({"error": "No active Hammerspace configuration found"})
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                # Get system components
                nodes = await client.get_nodes()
                volumes = await client.get_storage_volumes()
                shares = await client.get_shares()
                tasks = await client.get_tasks()
                
                # Get queue status for performance metrics
                queue_status = await client.get_task_queue_status()
                
                # Calculate performance metrics
                performance_data = {
                    "system_health": {
                        "overall_status": "healthy" if all(n.state == "OK" for n in nodes) else "degraded",
                        "nodes_healthy": len([n for n in nodes if n.state == "OK"]),
                        "nodes_total": len(nodes),
                        "volumes_healthy": len([v for v in volumes if (v.state.value == "UP" if hasattr(v.state, 'value') else v.state == "UP")]),
                        "volumes_total": len(volumes)
                    },
                    "performance_metrics": {
                        "active_tasks": len([t for t in tasks if (t.status.value == "RUNNING" if hasattr(t.status, 'value') else t.status == "RUNNING")]),
                        "total_tasks": len(tasks),
                        "queue_depth": queue_status.get("queue_depth", 0),
                        "active_requests": queue_status.get("active_requests", 0),
                        "average_response_time": queue_status.get("average_response_time", 0.0)
                    },
                    "storage_metrics": {
                        "total_shares": len(shares),
                        "active_shares": len(shares),  # All shares are considered active
                        "total_files": sum(s.total_number_of_files or 0 for s in shares)
                    }
                }
                
                return json.dumps(performance_data, indent=2)
                
        except Exception as e:
            return f"Error getting performance metrics: {str(e)}"
    
    async def _get_comprehensive_monitoring(self) -> str:
        """Get comprehensive monitoring overview of the system."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return json.dumps({"error": "No active Hammerspace configuration found"})
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                # Get all system components
                nodes = await client.get_nodes()
                volumes = await client.get_storage_volumes()
                shares = await client.get_shares()
                objectives = await client.get_objectives()
                tasks = await client.get_tasks()
                
                # Get comprehensive monitoring data
                monitoring_data = {
                    "system_overview": {
                        "timestamp": datetime.now().isoformat(),
                        "total_nodes": len(nodes),
                        "total_volumes": len(volumes),
                        "total_shares": len(shares),
                        "total_objectives": len(objectives),
                        "total_tasks": len(tasks)
                    },
                    "health_status": {
                        "nodes": {
                            "healthy": len([n for n in nodes if n.state == "OK"]),
                            "total": len(nodes),
                            "status": "healthy" if all(n.state == "OK" for n in nodes) else "degraded"
                        },
                        "volumes": {
                            "healthy": len([v for v in volumes if (v.state.value == "UP" if hasattr(v.state, 'value') else v.state == "UP")]),
                            "total": len(volumes),
                            "status": "healthy" if all((v.state.value == "UP" if hasattr(v.state, 'value') else v.state == "UP") for v in volumes) else "degraded"
                        },
                        "shares": {
                            "active": len(shares),  # All shares are considered active
                            "total": len(shares),
                            "status": "healthy"  # All shares are considered healthy if they exist
                        }
                    },
                    "resource_utilization": {
                        "total_files": sum(s.total_number_of_files or 0 for s in shares),
                        "active_tasks": len([t for t in tasks if (t.status.value == "RUNNING" if hasattr(t.status, 'value') else t.status == "RUNNING")]),
                        "completed_tasks": len([t for t in tasks if (t.status.value == "COMPLETED" if hasattr(t.status, 'value') else t.status == "COMPLETED")])
                    },
                    "detailed_components": {
                        "nodes": [
                            {
                                "name": node.name,
                                "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                                "status": node.state,
                                "endpoint": node.endpoint
                            } for node in nodes
                        ],
                        "volumes": [
                            {
                                "name": volume.name,
                                "state": volume.state.value if hasattr(volume.state, 'value') else str(volume.state),
                                "size": volume.size if hasattr(volume, 'size') else "Unknown"
                            } for volume in volumes
                        ],
                        "shares": [
                            {
                                "name": share.name,
                                "path": share.path,
                                "status": "active",  # Shares are considered active if they exist
                                "file_count": share.total_number_of_files or 0
                            } for share in shares
                        ],
                        "objectives": [
                            {
                                "name": obj.name,
                                "type": obj.objective_type.value if hasattr(obj.objective_type, 'value') else str(obj.objective_type),
                                "state": obj.state.value if hasattr(obj.state, 'value') else str(obj.state)
                            } for obj in objectives
                        ]
                    }
                }
                
                return json.dumps(monitoring_data, indent=2)
                
        except Exception as e:
            return f"Error getting comprehensive monitoring: {str(e)}"
    
    async def _copy_files_by_tags(self, request: Dict[str, Any]) -> str:
        """Copy files based on tag criteria."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return json.dumps({"error": "No active Hammerspace configuration found"})
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                source_share_uuid = request.get("source_share_uuid")
                destination_share_uuid = request.get("destination_share_uuid")
                tag_criteria = request.get("tag_criteria", {})
                destination_path = request.get("destination_path", "/")
                
                # Search for files matching tag criteria
                search_query = self._build_tag_search_query(tag_criteria)
                matching_files = await client.search_files(search_query)
                
                if not matching_files:
                    return f"No files found matching tag criteria: {tag_criteria}"
                
                # Create copy operations for each matching file
                copy_results = []
                for file in matching_files:
                    try:
                        # Create data movement job for file copy
                        job_data = {
                            "movement_type": "FILE_COPY",
                            "source_path": file.path,
                            "destination_path": f"{destination_path}/{file.name}",
                            "source_share": source_share_uuid,
                            "destination_share": destination_share_uuid
                        }
                        
                        job = await client.create_data_movement_job(job_data)
                        copy_results.append({
                            "file": file.path,
                            "status": "queued",
                            "job_id": job.uuid
                        })
                    except Exception as e:
                        copy_results.append({
                            "file": file.path,
                            "status": "error",
                            "error": str(e)
                        })
                
                return json.dumps({
                    "operation": "copy_files_by_tags",
                    "total_files": len(matching_files),
                    "successful": len([r for r in copy_results if r["status"] == "queued"]),
                    "failed": len([r for r in copy_results if r["status"] == "error"]),
                    "results": copy_results
                }, indent=2)
                
        except Exception as e:
            return f"Error copying files by tags: {str(e)}"
    
    async def _move_files_by_tags(self, request: Dict[str, Any]) -> str:
        """Move files based on tag criteria."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return json.dumps({"error": "No active Hammerspace configuration found"})
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                source_share_uuid = request.get("source_share_uuid")
                destination_share_uuid = request.get("destination_share_uuid")
                tag_criteria = request.get("tag_criteria", {})
                destination_path = request.get("destination_path", "/")
                
                # Search for files matching tag criteria
                search_query = self._build_tag_search_query(tag_criteria)
                matching_files = await client.search_files(search_query)
                
                if not matching_files:
                    return f"No files found matching tag criteria: {tag_criteria}"
                
                # Create move operations for each matching file
                move_results = []
                for file in matching_files:
                    try:
                        # Create data movement job for file move
                        job_data = {
                            "movement_type": "FILE_MOVE",
                            "source_path": file.path,
                            "destination_path": f"{destination_path}/{file.name}",
                            "source_share": source_share_uuid,
                            "destination_share": destination_share_uuid
                        }
                        
                        job = await client.create_data_movement_job(job_data)
                        move_results.append({
                            "file": file.path,
                            "status": "queued",
                            "job_id": job.uuid
                        })
                    except Exception as e:
                        move_results.append({
                            "file": file.path,
                            "status": "error",
                            "error": str(e)
                        })
                
                return json.dumps({
                    "operation": "move_files_by_tags",
                    "total_files": len(matching_files),
                    "successful": len([r for r in move_results if r["status"] == "queued"]),
                    "failed": len([r for r in move_results if r["status"] == "error"]),
                    "results": move_results
                }, indent=2)
                
        except Exception as e:
            return f"Error moving files by tags: {str(e)}"
    
    async def _delete_files_by_tags(self, request: Dict[str, Any]) -> str:
        """Delete files based on tag criteria."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return json.dumps({"error": "No active Hammerspace configuration found"})
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                share_uuid = request.get("share_uuid")
                tag_criteria = request.get("tag_criteria", {})
                dry_run = request.get("dry_run", False)
                
                # Search for files matching tag criteria
                search_query = self._build_tag_search_query(tag_criteria)
                matching_files = await client.search_files(search_query)
                
                if not matching_files:
                    return f"No files found matching tag criteria: {tag_criteria}"
                
                if dry_run:
                    return json.dumps({
                        "operation": "delete_files_by_tags",
                        "mode": "dry_run",
                        "total_files": len(matching_files),
                        "files_to_delete": [{"path": file.path, "size": file.size} for file in matching_files]
                    }, indent=2)
                
                # Create delete operations for each matching file
                delete_results = []
                for file in matching_files:
                    try:
                        # Create data movement job for file deletion
                        job_data = {
                            "movement_type": "FILE_DELETE",
                            "source_path": file.path,
                            "share": share_uuid
                        }
                        
                        job = await client.create_data_movement_job(job_data)
                        delete_results.append({
                            "file": file.path,
                            "status": "queued",
                            "job_id": job.uuid
                        })
                    except Exception as e:
                        delete_results.append({
                            "file": file.path,
                            "status": "error",
                            "error": str(e)
                        })
                
                return json.dumps({
                    "operation": "delete_files_by_tags",
                    "total_files": len(matching_files),
                    "successful": len([r for r in delete_results if r["status"] == "queued"]),
                    "failed": len([r for r in delete_results if r["status"] == "error"]),
                    "results": delete_results
                }, indent=2)
                
        except Exception as e:
            return f"Error deleting files by tags: {str(e)}"
    
    async def _replicate_files_by_tags(self, request: Dict[str, Any]) -> str:
        """Replicate files based on tag criteria."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return json.dumps({"error": "No active Hammerspace configuration found"})
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                source_share_uuid = request.get("source_share_uuid")
                destination_share_uuid = request.get("destination_share_uuid")
                tag_criteria = request.get("tag_criteria", {})
                sync_mode = request.get("sync_mode", "incremental")
                
                # Search for files matching tag criteria
                search_query = self._build_tag_search_query(tag_criteria)
                matching_files = await client.search_files(search_query)
                
                if not matching_files:
                    return f"No files found matching tag criteria: {tag_criteria}"
                
                # Create replication job
                job_data = {
                    "movement_type": "SHARE_REPLICATION",
                    "source_share": source_share_uuid,
                    "destination_share": destination_share_uuid,
                    "sync_mode": sync_mode,
                    "file_filter": tag_criteria
                }
                
                job = await client.create_data_movement_job(job_data)
                
                return json.dumps({
                    "operation": "replicate_files_by_tags",
                    "total_files": len(matching_files),
                    "sync_mode": sync_mode,
                    "job_id": job.uuid,
                    "status": "queued"
                }, indent=2)
                
        except Exception as e:
            return f"Error replicating files by tags: {str(e)}"
    
    def _build_tag_search_query(self, tag_criteria: Dict[str, Any]) -> str:
        """Build search query from tag criteria."""
        tags = tag_criteria.get("tags", {})
        match_all = tag_criteria.get("match_all", True)
        
        if not tags:
            return "*"
        
        # Build query based on tag criteria
        query_parts = []
        for key, value in tags.items():
            if isinstance(value, str) and value.startswith((">", "<", ">=", "<=")):
                # Numeric comparison
                query_parts.append(f"tag:{key}{value}")
            else:
                # Exact match
                query_parts.append(f"tag:{key}={value}")
        
        if match_all:
            return " AND ".join(query_parts)
        else:
            return " OR ".join(query_parts)
    
    # Convenience Methods
    
    async def _copy_file(self, request: Dict[str, Any]) -> str:
        """Copy a file."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                source_path = request.get("source_path", "")
                destination_path = request.get("destination_path", "")
                
                job = await client.copy_file(source_path, destination_path, **request.get("options", {}))
                return f"✅ **File Copy Job Created Successfully**\n\n**Name**: {job.name}\n**Status**: {job.status.value}\n**UUID**: {job.uuid}\n**Source**: {job.source_path}\n**Destination**: {job.destination_path}"
                
        except Exception as e:
            return f"Error copying file: {str(e)}"
    
    async def _move_file(self, request: Dict[str, Any]) -> str:
        """Move a file."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                source_path = request.get("source_path", "")
                destination_path = request.get("destination_path", "")
                
                job = await client.move_file(source_path, destination_path, **request.get("options", {}))
                return f"✅ **File Move Job Created Successfully**\n\n**Name**: {job.name}\n**Status**: {job.status.value}\n**UUID**: {job.uuid}\n**Source**: {job.source_path}\n**Destination**: {job.destination_path}"
                
        except Exception as e:
            return f"Error moving file: {str(e)}"
    
    async def _copy_directory(self, request: Dict[str, Any]) -> str:
        """Copy a directory."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                source_path = request.get("source_path", "")
                destination_path = request.get("destination_path", "")
                
                job = await client.copy_directory(source_path, destination_path, **request.get("options", {}))
                return f"✅ **Directory Copy Job Created Successfully**\n\n**Name**: {job.name}\n**Status**: {job.status.value}\n**UUID**: {job.uuid}\n**Source**: {job.source_path}\n**Destination**: {job.destination_path}"
                
        except Exception as e:
            return f"Error copying directory: {str(e)}"
    
    async def _replicate_share(self, request: Dict[str, Any]) -> str:
        """Replicate a share."""
        try:
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                source_share_uuid = request.get("source_share_uuid", "")
                destination_share_uuid = request.get("destination_share_uuid", "")
                
                job = await client.replicate_share(source_share_uuid, destination_share_uuid, **request.get("options", {}))
                return f"✅ **Share Replication Job Created Successfully**\n\n**Name**: {job.name}\n**Status**: {job.status.value}\n**UUID**: {job.uuid}\n**Source Share**: {job.source_share_uuid}\n**Destination Share**: {job.destination_share_uuid}"
                
        except Exception as e:
            return f"Error replicating share: {str(e)}"

    async def _mcp_clone(self, request: Dict[str, Any]) -> str:
        """Clone files from source to target using Hammerspace file-snapshots API."""
        try:
            source_path = request.get("source_path")
            target_path = request.get("target_path")
            recursive = request.get("recursive", True)
            overwrite = request.get("overwrite", False)
            
            if not source_path or not target_path:
                return "Error: source_path and target_path are required"
            
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                # Import and use the movement operations
                from src.operations.movement import DataMovementOperations
                
                movement_ops = DataMovementOperations(client)
                result = await movement_ops.mcp_clone(
                    source_path=source_path,
                    target_path=target_path,
                    recursive=recursive,
                    overwrite=overwrite
                )
                
                # Format the result for display
                output = f"=== MCP Clone Operation Results ===\n\n"
                output += f"Source Path: {result['source_path']}\n"
                output += f"Target Path: {result['target_path']}\n"
                output += f"Recursive: {result['recursive']}\n"
                output += f"Overwrite: {result['overwrite']}\n"
                output += f"Task UUID: {result['task_uuid']}\n\n"
                
                output += f"Overall Success: {'✅ Yes' if result['success'] else '❌ No'}\n"
                output += f"Total Files Processed: {result['total_files']}\n"
                output += f"Successfully Cloned: {len(result['cloned_files'])}\n"
                output += f"Failed to Clone: {len(result['failed_files'])}\n\n"
                
                if result['cloned_files']:
                    output += "=== Successfully Cloned Files ===\n"
                    for file_info in result['cloned_files'][:10]:  # Show first 10
                        output += f"✅ {file_info['source']} -> {file_info['target']}\n"
                    if len(result['cloned_files']) > 10:
                        output += f"... and {len(result['cloned_files']) - 10} more\n"
                    output += "\n"
                
                if result['failed_files']:
                    output += "=== Failed Files ===\n"
                    for file_info in result['failed_files'][:10]:  # Show first 10
                        output += f"❌ {file_info['source']} -> {file_info['target']}\n"
                        output += f"   Error: {file_info['error']}\n"
                    if len(result['failed_files']) > 10:
                        output += f"... and {len(result['failed_files']) - 10} more\n"
                
                return output
                
        except Exception as e:
            return f"Error in mcp_clone operation: {str(e)}"

    async def _mcp_clone(self, request: Dict[str, Any]) -> str:
        """Clone files from source to target using Hammerspace file-snapshots API."""
        try:
            source_path = request.get("source_path")
            target_path = request.get("target_path")
            recursive = request.get("recursive", True)
            overwrite = request.get("overwrite", False)
            
            if not source_path or not target_path:
                return "Error: source_path and target_path are required"
            
            # Use real Hammerspace client
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from src.hammerspace_client import HammerspaceClient
            from src.config import HammerspaceConfig
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            
            # Get active configuration
            config_manager = MultiConfigManager()
            active_config = config_manager.get_active_configuration()
            
            if not active_config:
                return {"error": "No active Hammerspace configuration found"}
            
            config = HammerspaceConfig(
                base_url=active_config['base_url'],
                username=active_config['username'],
                password=active_config['password'],
                verify_ssl=active_config.get('verify_ssl', False),
                timeout=active_config.get('timeout', 30)
            )
            
            async with HammerspaceClient(config) as client:
                # Import and use the movement operations
                from src.operations.movement import DataMovementOperations
                
                movement_ops = DataMovementOperations(client)
                result = await movement_ops.mcp_clone(
                    source_path=source_path,
                    target_path=target_path,
                    recursive=recursive,
                    overwrite=overwrite
                )
                
                # Format the result for display
                output = f"=== MCP Clone Operation Results ===\n\n"
                output += f"Source Path: {result['source_path']}\n"
                output += f"Target Path: {result['target_path']}\n"
                output += f"Recursive: {result['recursive']}\n"
                output += f"Overwrite: {result['overwrite']}\n"
                output += f"Task UUID: {result['task_uuid']}\n\n"
                
                output += f"Overall Success: {'✅ Yes' if result['success'] else '❌ No'}\n"
                output += f"Total Files Processed: {result['total_files']}\n"
                output += f"Successfully Cloned: {len(result['cloned_files'])}\n"
                output += f"Failed to Clone: {len(result['failed_files'])}\n\n"
                
                if result['cloned_files']:
                    output += "=== Successfully Cloned Files ===\n"
                    for file_info in result['cloned_files'][:10]:  # Show first 10
                        output += f"✅ {file_info['source']} -> {file_info['target']}\n"
                    if len(result['cloned_files']) > 10:
                        output += f"... and {len(result['cloned_files']) - 10} more\n"
                    output += "\n"
                
                if result['failed_files']:
                    output += "=== Failed Files ===\n"
                    for file_info in result['failed_files'][:10]:  # Show first 10
                        output += f"❌ {file_info['source']} -> {file_info['target']}\n"
                        output += f"   Error: {file_info['error']}\n"
                    if len(result['failed_files']) > 10:
                        output += f"... and {len(result['failed_files']) - 10} more\n"
                
                return output
                
        except Exception as e:
            return f"Error in mcp_clone operation: {str(e)}"
    
    # Docs service tool implementations
    async def _get_api_reference(self) -> str:
        """Get API reference."""
        try:
            return "API Reference Documentation - Federated Storage MCP Service"
        except Exception as e:
            return f"Error getting API reference: {str(e)}"
    
    async def _get_tool_help(self) -> str:
        """Get tool help."""
        try:
            return "Tool Help Documentation - Available MCP Tools and Usage"
        except Exception as e:
            return f"Error getting tool help: {str(e)}"
    
    async def _get_multi_system_overview(self) -> str:
        """Get multi-system overview with optimized performance."""
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webui', 'backend'))
            from multi_config_manager import MultiConfigManager
            manager = MultiConfigManager()
            overview = await manager.get_multi_system_overview()
            return json.dumps(overview, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to get multi-system overview: {e}")
            return json.dumps({"error": str(e)}, indent=2)
    
    def run(self, host: str = "0.0.0.0", port: int = None):
        """Run the HTTP server."""
        if port is None:
            port = self.port
            
        logger.info(f"Starting HTTP MCP server on {host}:{port}")
        
        try:
            # Run the FastAPI server
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                log_level="info"
            )
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="HTTP MCP Server Wrapper")
    parser.add_argument("--service", choices=["main", "docs"], default="main",
                       help="Service type (main or docs)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    # Adjust port for docs service
    if args.service == "docs" and args.port == 8000:
        args.port = 8001
    
    server = HTTPMCPServer(service_type=args.service, port=args.port)
    server.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main() 