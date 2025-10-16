"""
Storage management operations for the Federated Storage MCP Service.
Provides high-level functions for managing storage volumes, shares, and storage-related operations.
"""

import asyncio
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid

from hammerspace_client import HammerspaceClient, create_hammerspace_client
from models import (
    StorageVolume, ObjectStorageVolume, Share, Node, VolumeState, 
    StorageVolumeList, ObjectStorageVolumeList, ShareList, NodeList
)
from operations.visibility import VisibilityOperations
from logging_config import get_logger, log_operation


logger = get_logger(__name__)


class StorageManagementOperations:
    """High-level operations for storage management across the federated storage system."""
    
    def __init__(self, client: Optional[HammerspaceClient] = None):
        """
        Initialize storage management operations.
        
        Args:
            client: Hammerspace client instance. If None, creates a new one.
        """
        self.client = client or create_hammerspace_client()
        self.visibility_ops = VisibilityOperations(client)
        self.logger = logger
        
        # Check if we should use mock mode
        from config import get_config
        try:
            config = get_config()
            if config.load_config():
                dev_config = config.get_dev_config()
                self.mock_mode = dev_config.mock_api
            else:
                self.mock_mode = False
        except Exception:
            self.mock_mode = False
    
    @log_operation("get_storage_overview")
    async def get_storage_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive storage overview across all nodes.
        
        Returns:
            Dictionary with storage statistics and information
            
        Raises:
            Exception: If overview retrieval fails
        """
        try:
            self.logger.info("Getting storage overview")
            
            # Check if we should use mock data
            if hasattr(self, 'mock_mode') and self.mock_mode:
                return await self._get_mock_storage_overview()
            
            # Get all storage components
            nodes = await self.visibility_ops.list_nodes()
            storage_volumes = await self.visibility_ops.list_storage_volumes()
            object_volumes = await self.visibility_ops.list_object_storage_volumes()
            shares = await self.visibility_ops.list_shares()
            
            # Calculate statistics
            total_nodes = len(nodes)
            total_storage_volumes = len(storage_volumes)
            total_object_volumes = len(object_volumes)
            total_shares = len(shares)
            
            # Calculate storage capacity
            total_capacity = 0
            total_used = 0
            for volume in storage_volumes:
                if volume.size_bytes:
                    total_capacity += volume.size_bytes
                if volume.used_bytes:
                    total_used += volume.used_bytes
            
            # Group by node
            node_storage = {}
            for node in nodes:
                node_volumes = [v for v in storage_volumes if v.node_uuid == node.uuid]
                node_shares = [s for s in shares if any(
                    v.node_uuid == node.uuid for v in storage_volumes
                )]
                
                node_capacity = sum(v.size_bytes or 0 for v in node_volumes)
                node_used = sum(v.used_bytes or 0 for v in node_volumes)
                
                node_storage[node.uuid] = {
                    "name": node.name,
                    "node_type": node.node_type.value,
                    "state": node.state,
                    "volumes": len(node_volumes),
                    "shares": len(node_shares),
                    "capacity_bytes": node_capacity,
                    "used_bytes": node_used,
                    "utilization_percent": (node_used / node_capacity * 100) if node_capacity > 0 else 0
                }
            
            overview = {
                "summary": {
                    "total_nodes": total_nodes,
                    "total_storage_volumes": total_storage_volumes,
                    "total_object_volumes": total_object_volumes,
                    "total_shares": total_shares,
                    "total_capacity_bytes": total_capacity,
                    "total_used_bytes": total_used,
                    "total_utilization_percent": (total_used / total_capacity * 100) if total_capacity > 0 else 0
                },
                "nodes": node_storage,
                "volume_states": {
                    state.value: len([v for v in storage_volumes if v.state == state])
                    for state in VolumeState
                }
            }
            
            self.logger.info(f"Storage overview: {total_nodes} nodes, {total_storage_volumes} volumes, {total_shares} shares")
            return overview
            
        except Exception as e:
            self.logger.error(f"Failed to get storage overview: {e}")
            raise
    
    async def _get_mock_storage_overview(self) -> Dict[str, Any]:
        """Get mock storage overview using test data."""
        try:
            import json
            import os
            
            # Load mock storage data
            mock_data_path = "tests/mock_data/storage_overview.json"
            if not os.path.exists(mock_data_path):
                return {
                    "status": "ERROR",
                    "message": "Mock storage data not found",
                    "summary": {
                        "total_nodes": 0,
                        "total_storage_volumes": 0,
                        "total_object_volumes": 0,
                        "total_shares": 0,
                        "total_capacity_bytes": 0,
                        "total_used_bytes": 0,
                        "total_utilization_percent": 0
                    },
                    "nodes": {},
                    "volume_states": {}
                }
            
            with open(mock_data_path, 'r') as f:
                mock_data = json.load(f)
            
            # Format the mock data to match the expected structure
            system_info = mock_data.get("system_info", {})
            nodes = mock_data.get("nodes", [])
            volumes = mock_data.get("volumes", [])
            shares = mock_data.get("shares", [])
            
            # Calculate node storage statistics
            node_storage = {}
            for node in nodes:
                node_volumes = [v for v in volumes if v.get("node_id") == node.get("id")]
                node_shares = [s for s in shares if s.get("node_id") == node.get("id")]
                
                node_capacity = sum(v.get("capacity", 0) for v in node_volumes)
                node_used = sum(v.get("used", 0) for v in node_volumes)
                
                node_storage[node.get("id")] = {
                    "name": node.get("name"),
                    "node_type": "storage",
                    "state": node.get("status"),
                    "volumes": len(node_volumes),
                    "shares": len(node_shares),
                    "capacity_bytes": node_capacity,
                    "used_bytes": node_used,
                    "utilization_percent": (node_used / node_capacity * 100) if node_capacity > 0 else 0
                }
            
            overview = {
                "status": "SUCCESS",
                "message": "Mock storage overview retrieved",
                "summary": {
                    "total_nodes": system_info.get("total_nodes", 0),
                    "total_storage_volumes": system_info.get("total_volumes", 0),
                    "total_object_volumes": 0,
                    "total_shares": system_info.get("total_shares", 0),
                    "total_capacity_bytes": system_info.get("total_capacity", 0),
                    "total_used_bytes": system_info.get("used_capacity", 0),
                    "total_utilization_percent": (system_info.get("used_capacity", 0) / system_info.get("total_capacity", 1) * 100)
                },
                "nodes": node_storage,
                "volume_states": {
                    "mounted": len([v for v in volumes if v.get("status") == "mounted"]),
                    "unmounted": len([v for v in volumes if v.get("status") == "unmounted"])
                },
                "mock_data": True
            }
            
            self.logger.info(f"Mock storage overview: {system_info.get('total_nodes', 0)} nodes, {system_info.get('total_volumes', 0)} volumes, {system_info.get('total_shares', 0)} shares")
            return overview
            
        except Exception as e:
            self.logger.error(f"Failed to get mock storage overview: {e}")
            return {
                "status": "ERROR",
                "message": f"Mock storage overview failed: {e}",
                "summary": {
                    "total_nodes": 0,
                    "total_storage_volumes": 0,
                    "total_object_volumes": 0,
                    "total_shares": 0,
                    "total_capacity_bytes": 0,
                    "total_used_bytes": 0,
                    "total_utilization_percent": 0
                },
                "nodes": {},
                "volume_states": {},
                "mock_data": True
            }
    
    @log_operation("get_node_storage_details")
    async def get_node_storage_details(self, node_uuid: str) -> Dict[str, Any]:
        """
        Get detailed storage information for a specific node.
        
        Args:
            node_uuid: UUID of the node
            
        Returns:
            Dictionary with detailed node storage information
            
        Raises:
            Exception: If details retrieval fails
        """
        try:
            self.logger.info(f"Getting storage details for node: {node_uuid}")
            
            # Get node information
            node = await self.visibility_ops.get_node_details(node_uuid)
            
            # Get volumes for this node
            all_volumes = await self.visibility_ops.list_storage_volumes()
            node_volumes = [v for v in all_volumes if v.node_uuid == node_uuid]
            
            # Get object storage volumes
            all_object_volumes = await self.visibility_ops.list_object_storage_volumes()
            node_object_volumes = [v for v in all_object_volumes if v.storage_volume_state]
            
            # Get shares associated with this node's volumes
            all_shares = await self.visibility_ops.list_shares()
            node_shares = []
            for share in all_shares:
                # This is a simplified association - in a real implementation,
                # you'd need to check the actual share-to-volume mapping
                if any(v.node_uuid == node_uuid for v in node_volumes):
                    node_shares.append(share)
            
            # Calculate storage statistics
            total_capacity = sum(v.size_bytes or 0 for v in node_volumes)
            total_used = sum(v.used_bytes or 0 for v in node_volumes)
            
            details = {
                "node": {
                    "uuid": node.uuid,
                    "name": node.name,
                    "node_type": node.node_type.value,
                    "state": node.state,
                    "endpoint": node.endpoint,
                    "created": node.created,
                    "modified": node.modified
                },
                "storage_volumes": [
                    {
                        "uuid": v.uuid,
                        "name": v.name,
                        "volume_type": v.volume_type,
                        "state": v.state.value,
                        "size_bytes": v.size_bytes,
                        "used_bytes": v.used_bytes,
                        "utilization_percent": (v.used_bytes / v.size_bytes * 100) if v.size_bytes and v.used_bytes else 0
                    }
                    for v in node_volumes
                ],
                "object_storage_volumes": [
                    {
                        "uuid": v.uuid,
                        "name": v.name,
                        "state": v.storage_volume_state.value,
                        "created": v.created,
                        "modified": v.modified
                    }
                    for v in node_object_volumes
                ],
                "shares": [
                    {
                        "uuid": s.uuid,
                        "name": s.name,
                        "path": s.path,
                        "created": s.created,
                        "modified": s.modified
                    }
                    for s in node_shares
                ],
                "statistics": {
                    "total_volumes": len(node_volumes),
                    "total_object_volumes": len(node_object_volumes),
                    "total_shares": len(node_shares),
                    "total_capacity_bytes": total_capacity,
                    "total_used_bytes": total_used,
                    "utilization_percent": (total_used / total_capacity * 100) if total_capacity > 0 else 0
                }
            }
            
            self.logger.info(f"Node {node.name} storage details: {len(node_volumes)} volumes, {len(node_shares)} shares")
            return details
            
        except Exception as e:
            self.logger.error(f"Failed to get node storage details for {node_uuid}: {e}")
            raise
    
    @log_operation("get_volume_details")
    async def get_volume_details(self, volume_uuid: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific storage volume.
        
        Args:
            volume_uuid: UUID of the storage volume
            
        Returns:
            Dictionary with detailed volume information
            
        Raises:
            Exception: If details retrieval fails
        """
        try:
            self.logger.info(f"Getting details for volume: {volume_uuid}")
            
            # Get all volumes and find the specific one
            all_volumes = await self.visibility_ops.list_storage_volumes()
            volume = next((v for v in all_volumes if v.uuid == volume_uuid), None)
            
            if not volume:
                raise ValueError(f"Volume {volume_uuid} not found")
            
            # Get associated node
            node = None
            if volume.node_uuid:
                try:
                    node = await self.visibility_ops.get_node_details(volume.node_uuid)
                except Exception:
                    self.logger.warning(f"Could not retrieve node details for {volume.node_uuid}")
            
            # Get associated shares (simplified - would need proper mapping in real implementation)
            all_shares = await self.visibility_ops.list_shares()
            volume_shares = []  # In a real implementation, you'd filter by actual volume association
            
            details = {
                "volume": {
                    "uuid": volume.uuid,
                    "name": volume.name,
                    "volume_type": volume.volume_type,
                    "state": volume.state.value,
                    "size_bytes": volume.size_bytes,
                    "used_bytes": volume.used_bytes,
                    "utilization_percent": (volume.used_bytes / volume.size_bytes * 100) if volume.size_bytes and volume.used_bytes else 0,
                    "created": volume.created,
                    "modified": volume.modified
                },
                "node": {
                    "uuid": node.uuid,
                    "name": node.name,
                    "node_type": node.node_type.value,
                    "state": node.state
                } if node else None,
                "shares": volume_shares,
                "extended_info": volume.extended_info
            }
            
            self.logger.info(f"Volume {volume.name} details retrieved")
            return details
            
        except Exception as e:
            self.logger.error(f"Failed to get volume details for {volume_uuid}: {e}")
            raise
    
    @log_operation("get_share_details")
    async def get_share_details(self, share_uuid: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific share.
        
        Args:
            share_uuid: UUID of the share
            
        Returns:
            Dictionary with detailed share information
            
        Raises:
            Exception: If details retrieval fails
        """
        try:
            self.logger.info(f"Getting details for share: {share_uuid}")
            
            # Get all shares and find the specific one
            all_shares = await self.visibility_ops.list_shares()
            share = next((s for s in all_shares if s.uuid == share_uuid), None)
            
            if not share:
                raise ValueError(f"Share {share_uuid} not found")
            
            # Get associated volumes (simplified - would need proper mapping in real implementation)
            all_volumes = await self.visibility_ops.list_storage_volumes()
            share_volumes = []  # In a real implementation, you'd filter by actual share association
            
            details = {
                "share": {
                    "uuid": share.uuid,
                    "name": share.name,
                    "path": share.path,
                    "created": share.created,
                    "modified": share.modified,
                    "smb_aliases": share.smb_aliases,
                    "active_objectives": share.active_objectives,
                    "applied_objectives": share.applied_objectives
                },
                "volumes": share_volumes,
                "extended_info": share.extended_info
            }
            
            self.logger.info(f"Share {share.name} details retrieved")
            return details
            
        except Exception as e:
            self.logger.error(f"Failed to get share details for {share_uuid}: {e}")
            raise
    
    @log_operation("monitor_storage_health")
    async def monitor_storage_health(self) -> Dict[str, Any]:
        """
        Monitor overall storage system health.
        
        Returns:
            Dictionary with health status and issues
            
        Raises:
            Exception: If health monitoring fails
        """
        try:
            self.logger.info("Monitoring storage system health")
            
            # Get all storage components
            nodes = await self.visibility_ops.list_nodes()
            storage_volumes = await self.visibility_ops.list_storage_volumes()
            object_volumes = await self.visibility_ops.list_object_storage_volumes()
            
            # Check for issues
            issues = []
            warnings = []
            
            # Check node health
            for node in nodes:
                if node.state != "OK":
                    issues.append({
                        "type": "node",
                        "severity": "error",
                        "uuid": node.uuid,
                        "name": node.name,
                        "issue": f"Node state is {node.state}"
                    })
            
            # Check volume health
            for volume in storage_volumes:
                if volume.state == VolumeState.ERROR:
                    issues.append({
                        "type": "volume",
                        "severity": "error",
                        "uuid": volume.uuid,
                        "name": volume.name,
                        "issue": "Volume in ERROR state"
                    })
                elif volume.state == VolumeState.DEGRADED:
                    warnings.append({
                        "type": "volume",
                        "severity": "warning",
                        "uuid": volume.uuid,
                        "name": volume.name,
                        "issue": "Volume in DEGRADED state"
                    })
                
                # Check utilization
                if volume.size_bytes and volume.used_bytes:
                    utilization = (volume.used_bytes / volume.size_bytes) * 100
                    if utilization > 90:
                        warnings.append({
                            "type": "volume",
                            "severity": "warning",
                            "uuid": volume.uuid,
                            "name": volume.name,
                            "issue": f"Volume utilization is {utilization:.1f}%"
                        })
            
            # Check object storage volumes
            for volume in object_volumes:
                if volume.storage_volume_state == VolumeState.ERROR:
                    issues.append({
                        "type": "object_volume",
                        "severity": "error",
                        "uuid": volume.uuid,
                        "name": volume.name,
                        "issue": "Object storage volume in ERROR state"
                    })
            
            # Calculate overall health
            total_components = len(nodes) + len(storage_volumes) + len(object_volumes)
            error_components = len([i for i in issues if i["severity"] == "error"])
            warning_components = len(warnings)
            
            if error_components > 0:
                overall_status = "ERROR"
            elif warning_components > 0:
                overall_status = "WARNING"
            else:
                overall_status = "HEALTHY"
            
            health_status = {
                "overall_status": overall_status,
                "total_components": total_components,
                "error_count": error_components,
                "warning_count": warning_components,
                "issues": issues,
                "warnings": warnings,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Storage health: {overall_status} ({error_components} errors, {warning_components} warnings)")
            return health_status
            
        except Exception as e:
            self.logger.error(f"Failed to monitor storage health: {e}")
            raise
    
    @log_operation("get_storage_utilization")
    async def get_storage_utilization(self, node_uuid: Optional[str] = None) -> Dict[str, Any]:
        """
        Get storage utilization statistics.
        
        Args:
            node_uuid: Optional node UUID to filter by
            
        Returns:
            Dictionary with utilization statistics
            
        Raises:
            Exception: If utilization calculation fails
        """
        try:
            self.logger.info("Getting storage utilization statistics")
            
            # Get storage volumes
            all_volumes = await self.visibility_ops.list_storage_volumes()
            
            # Filter by node if specified
            if node_uuid:
                volumes = [v for v in all_volumes if v.node_uuid == node_uuid]
            else:
                volumes = all_volumes
            
            # Calculate statistics
            total_capacity = 0
            total_used = 0
            volume_stats = []
            
            for volume in volumes:
                capacity = volume.size_bytes or 0
                used = volume.used_bytes or 0
                utilization = (used / capacity * 100) if capacity > 0 else 0
                
                total_capacity += capacity
                total_used += used
                
                volume_stats.append({
                    "uuid": volume.uuid,
                    "name": volume.name,
                    "capacity_bytes": capacity,
                    "used_bytes": used,
                    "utilization_percent": utilization,
                    "state": volume.state.value
                })
            
            overall_utilization = (total_used / total_capacity * 100) if total_capacity > 0 else 0
            
            utilization_data = {
                "overall": {
                    "total_capacity_bytes": total_capacity,
                    "total_used_bytes": total_used,
                    "utilization_percent": overall_utilization,
                    "available_bytes": total_capacity - total_used
                },
                "volumes": volume_stats,
                "node_filter": node_uuid
            }
            
            self.logger.info(f"Storage utilization: {overall_utilization:.1f}% ({total_used}/{total_capacity} bytes)")
            return utilization_data
            
        except Exception as e:
            self.logger.error(f"Failed to get storage utilization: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the storage management operations."""
        if self.client:
            await self.client.close()


# Convenience functions for common operations
async def get_storage_overview() -> Dict[str, Any]:
    """
    Convenience function to get storage overview.
    
    Returns:
        Dictionary with storage overview information
    """
    async with StorageManagementOperations() as ops:
        return await ops.get_storage_overview()


async def get_node_storage_details(node_uuid: str) -> Dict[str, Any]:
    """
    Convenience function to get node storage details.
    
    Args:
        node_uuid: UUID of the node
        
    Returns:
        Dictionary with node storage details
    """
    async with StorageManagementOperations() as ops:
        return await ops.get_node_storage_details(node_uuid)


async def monitor_storage_health() -> Dict[str, Any]:
    """
    Convenience function to monitor storage health.
    
    Returns:
        Dictionary with health status
    """
    async with StorageManagementOperations() as ops:
        return await ops.monitor_storage_health() 