"""
Data visibility operations for the Federated Storage MCP Service.
Provides high-level functions for discovering storage resources.
"""

from typing import List, Optional, Dict, Any
import asyncio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from hammerspace_client import HammerspaceClient, create_hammerspace_client
from models import Node, StorageVolume, ObjectStorageVolume, Share, File, Task, NodeList, StorageVolumeList, ObjectStorageVolumeList, ShareList, FileList, TaskList
from logging_config import get_logger, log_operation


logger = get_logger(__name__)


class VisibilityOperations:
    """High-level operations for data visibility across the federated storage system."""
    
    def __init__(self, client: Optional[HammerspaceClient] = None):
        """
        Initialize visibility operations.
        
        Args:
            client: Hammerspace client instance. If None, creates a new one.
        """
        self.client = client or create_hammerspace_client()
        self.logger = logger
    
    @log_operation("list_nodes")
    async def list_nodes(self) -> NodeList:
        """
        List all storage nodes in the federated system.
        
        Returns:
            List of Node objects representing all storage nodes
            
        Raises:
            Exception: If API call fails
        """
        try:
            nodes = await self.client.get_nodes()
            self.logger.info(f"Successfully retrieved {len(nodes)} storage nodes")
            return nodes
        except Exception as e:
            self.logger.error(f"Failed to list nodes: {e}")
            raise
    
    @log_operation("get_node")
    async def get_node(self, identifier: str) -> Node:
        """
        Get specific node by identifier.
        
        Args:
            identifier: Node UUID or name
            
        Returns:
            Node object
            
        Raises:
            Exception: If API call fails
        """
        try:
            node = await self.client.get_node(identifier)
            self.logger.info(f"Successfully retrieved node: {node.name}")
            return node
        except Exception as e:
            self.logger.error(f"Failed to get node {identifier}: {e}")
            raise
    
    @log_operation("list_storage_volumes")
    async def list_storage_volumes(self) -> StorageVolumeList:
        """
        List all storage volumes in the federated system.
        
        Returns:
            List of StorageVolume objects
            
        Raises:
            Exception: If API call fails
        """
        try:
            volumes = await self.client.get_storage_volumes()
            self.logger.info(f"Successfully retrieved {len(volumes)} storage volumes")
            return volumes
        except Exception as e:
            self.logger.error(f"Failed to list storage volumes: {e}")
            raise
    
    @log_operation("list_object_storage_volumes")
    async def list_object_storage_volumes(self) -> ObjectStorageVolumeList:
        """
        List all object storage volumes in the federated system.
        
        Returns:
            List of ObjectStorageVolume objects
            
        Raises:
            Exception: If API call fails
        """
        try:
            volumes = await self.client.get_object_storage_volumes()
            self.logger.info(f"Successfully retrieved {len(volumes)} object storage volumes")
            return volumes
        except Exception as e:
            self.logger.error(f"Failed to list object storage volumes: {e}")
            raise
    
    @log_operation("list_shares")
    async def list_shares(self) -> ShareList:
        """
        List all shares in the federated system.
        
        Returns:
            List of Share objects
            
        Raises:
            Exception: If API call fails
        """
        try:
            shares = await self.client.get_shares()
            self.logger.info(f"Successfully retrieved {len(shares)} shares")
            return shares
        except Exception as e:
            self.logger.error(f"Failed to list shares: {e}")
            raise
    
    @log_operation("get_file_info")
    async def get_file_info(self, path: Optional[str] = None) -> Optional[File]:
        """
        Get file information by path.
        
        Args:
            path: File path (optional)
            
        Returns:
            File object or None if not found
            
        Raises:
            Exception: If API call fails
        """
        try:
            file_obj = await self.client.get_file_info(path)
            if file_obj:
                self.logger.info(f"Successfully retrieved file info: {file_obj.name}")
            else:
                self.logger.info(f"File not found: {path}")
            return file_obj
        except Exception as e:
            self.logger.error(f"Failed to get file info for {path}: {e}")
            raise
    
    @log_operation("search_files")
    async def search_files(self, query: str = "*", limit: int = 1000, offset: int = 0) -> List[File]:
        """
        Search for files across the system.
        
        Args:
            query: Search query (default: "*" for all files)
            limit: Maximum number of results
            offset: Result offset for pagination
            
        Returns:
            List of File objects matching the search criteria
            
        Raises:
            Exception: If API call fails
        """
        try:
            files = await self.client.search_files(query, limit, offset)
            self.logger.info(f"Successfully retrieved {len(files)} files matching query: {query}")
            return files
        except Exception as e:
            self.logger.error(f"Failed to search files with query '{query}': {e}")
            raise
    
    @log_operation("get_file_count")
    async def get_file_count(self, query: str = "*") -> int:
        """
        Get the total count of files matching a query.
        
        Args:
            query: Search query (default: "*" for all files)
            
        Returns:
            Total count of files matching the query
            
        Raises:
            Exception: If API call fails
        """
        try:
            count = await self.client.get_file_count(query)
            self.logger.info(f"Successfully retrieved file count: {count} files matching query: {query}")
            return count
        except Exception as e:
            self.logger.error(f"Failed to get file count for query '{query}': {e}")
            raise
    
    @log_operation("monitor_task")
    async def monitor_task(self, task_uuid: str) -> Task:
        """
        Monitor a long-running task.
        
        Args:
            task_uuid: Task UUID
            
        Returns:
            Task object with current status
            
        Raises:
            Exception: If API call fails
        """
        try:
            task = await self.client.get_task(task_uuid)
            self.logger.info(f"Successfully retrieved task: {task.name} (status: {task.status})")
            return task
        except Exception as e:
            self.logger.error(f"Failed to monitor task {task_uuid}: {e}")
            raise
    
    @log_operation("get_federated_overview")
    async def get_federated_overview(self) -> Dict[str, Any]:
        """
        Get an overview of the entire federated storage system.
        
        Returns:
            Dictionary containing counts and summary information
            
        Raises:
            Exception: If any API call fails
        """
        try:
            # Get all resources concurrently
            nodes_task = self.list_nodes()
            storage_volumes_task = self.list_storage_volumes()
            object_storage_volumes_task = self.list_object_storage_volumes()
            shares_task = self.list_shares()
            
            # Wait for all tasks to complete
            nodes, storage_volumes, object_storage_volumes, shares = await asyncio.gather(
                nodes_task,
                storage_volumes_task,
                object_storage_volumes_task,
                shares_task,
                return_exceptions=True
            )
            
            # Handle any exceptions
            nodes_list: NodeList = []
            storage_volumes_list: StorageVolumeList = []
            object_storage_volumes_list: ObjectStorageVolumeList = []
            shares_list: ShareList = []
            
            if isinstance(nodes, Exception):
                self.logger.error(f"Failed to get nodes: {nodes}")
            else:
                nodes_list = nodes  # type: ignore
                
            if isinstance(storage_volumes, Exception):
                self.logger.error(f"Failed to get storage volumes: {storage_volumes}")
            else:
                storage_volumes_list = storage_volumes  # type: ignore
                
            if isinstance(object_storage_volumes, Exception):
                self.logger.error(f"Failed to get object storage volumes: {object_storage_volumes}")
            else:
                object_storage_volumes_list = object_storage_volumes  # type: ignore
                
            if isinstance(shares, Exception):
                self.logger.error(f"Failed to get shares: {shares}")
            else:
                shares_list = shares  # type: ignore
            
            # Create overview
            overview = {
                "total_nodes": len(nodes_list),
                "total_storage_volumes": len(storage_volumes_list),
                "total_object_storage_volumes": len(object_storage_volumes_list),
                "total_shares": len(shares_list),
                "node_types": {},
                "volume_states": {},
                "summary": {
                    "nodes": [{"uuid": n.uuid, "name": n.name, "type": n.node_type.value} for n in nodes_list],
                    "storage_volumes": [{"uuid": v.uuid, "name": v.name, "state": v.state.value} for v in storage_volumes_list],
                    "object_storage_volumes": [{"uuid": v.uuid, "name": v.name, "state": v.storage_volume_state.value} for v in object_storage_volumes_list],
                    "shares": [{"uuid": s.uuid, "name": s.name, "path": s.path} for s in shares_list]
                }
            }
            
            # Count node types
            for node in nodes_list:
                node_type = node.node_type.value
                overview["node_types"][node_type] = overview["node_types"].get(node_type, 0) + 1
            
            # Count volume states
            for volume in storage_volumes_list:
                state = volume.state.value
                overview["volume_states"][state] = overview["volume_states"].get(state, 0) + 1
            
            for volume in object_storage_volumes_list:
                state = volume.storage_volume_state.value
                overview["volume_states"][state] = overview["volume_states"].get(state, 0) + 1
            
            self.logger.info(f"Successfully generated federated overview: {overview['total_nodes']} nodes, {overview['total_storage_volumes']} storage volumes, {overview['total_object_storage_volumes']} object storage volumes, {overview['total_shares']} shares")
            return overview
            
        except Exception as e:
            self.logger.error(f"Failed to get federated overview: {e}")
            raise
    
    @log_operation("get_node_details")
    async def get_node_details(self, node_identifier: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific node.
        
        Args:
            node_identifier: Node UUID or name
            
        Returns:
            Dictionary containing node details and associated resources
            
        Raises:
            Exception: If API call fails
        """
        try:
            # Get node information
            node = await self.get_node(node_identifier)
            
            # Get all storage volumes and filter by node
            storage_volumes = await self.list_storage_volumes()
            node_volumes = [v for v in storage_volumes if v.node_uuid == node.uuid]
            
            # Get object storage volumes (these might not have direct node association)
            object_storage_volumes = await self.list_object_storage_volumes()
            
            details = {
                "node": {
                    "uuid": node.uuid,
                    "name": node.name,
                    "type": node.node_type.value,
                    "endpoint": node.endpoint,
                    "state": node.state,
                    "created": node.created,
                    "modified": node.modified,
                    "platform_services": node.platform_services
                },
                "storage_volumes": [
                    {
                        "uuid": v.uuid,
                        "name": v.name,
                        "type": v.volume_type,
                        "state": v.state.value,
                        "size_bytes": v.size_bytes,
                        "used_bytes": v.used_bytes
                    }
                    for v in node_volumes
                ],
                "object_storage_volumes": [
                    {
                        "uuid": v.uuid,
                        "name": v.name,
                        "state": v.storage_volume_state.value
                    }
                    for v in object_storage_volumes
                ],
                "summary": {
                    "total_storage_volumes": len(node_volumes),
                    "total_object_storage_volumes": len(object_storage_volumes)
                }
            }
            
            self.logger.info(f"Successfully retrieved details for node {node.name}: {details['summary']['total_storage_volumes']} storage volumes, {details['summary']['total_object_storage_volumes']} object storage volumes")
            return details
            
        except Exception as e:
            self.logger.error(f"Failed to get node details for {node_identifier}: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the client session."""
        if hasattr(self.client, '__aexit__'):
            await self.client.__aexit__(None, None, None)


# Convenience functions for direct usage
async def list_all_nodes() -> NodeList:
    """List all storage nodes."""
    ops = VisibilityOperations()
    try:
        return await ops.list_nodes()
    finally:
        await ops.close()


async def list_all_shares() -> ShareList:
    """List all shares."""
    ops = VisibilityOperations()
    try:
        return await ops.list_shares()
    finally:
        await ops.close()


async def get_federated_overview() -> Dict[str, Any]:
    """Get federated storage system overview."""
    ops = VisibilityOperations()
    try:
        return await ops.get_federated_overview()
    finally:
        await ops.close() 