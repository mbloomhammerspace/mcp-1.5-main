"""
Data movement operations for the Federated Storage MCP Service.
Provides high-level functions for replication, copying, and moving data across the federated storage system.
"""

import asyncio
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from hammerspace_client import HammerspaceClient, create_hammerspace_client
from models import Task, TaskList, File, ReplicationStatus
from operations.visibility import VisibilityOperations
from operations.catalog import search_catalog_advanced
from logging_config import get_logger, log_operation


logger = get_logger(__name__)


class DataMovementOperations:
    """High-level operations for data movement across the federated storage system."""
    
    def __init__(self, client: Optional[HammerspaceClient] = None):
        """
        Initialize data movement operations.
        
        Args:
            client: Hammerspace client instance. If None, creates a new one.
        """
        self.client = client or create_hammerspace_client()
        self.visibility_ops = VisibilityOperations(client)
        self.logger = logger
    
    @log_operation("replicate_file")
    async def replicate_file(self, source_path: str, target_node_uuid: str, 
                           target_share_uuid: Optional[str] = None,
                           target_path: Optional[str] = None) -> Task:
        """
        Replicate a file to a target node.
        
        Args:
            source_path: Path to the source file
            target_node_uuid: UUID of the target node
            target_share_uuid: UUID of the target share (optional)
            target_path: Target path (optional, defaults to source path)
            
        Returns:
            Task object representing the replication operation
            
        Raises:
            Exception: If replication fails
        """
        try:
            self.logger.info(f"Starting file replication: {source_path} -> node {target_node_uuid}")
            
            # Use target_path if provided, otherwise use source_path
            if not target_path:
                target_path = source_path
            
            # Create replication task via API
            task_data = {
                "name": f"Replicate {source_path}",
                "task_type": "REPLICATION",
                "source_path": source_path,
                "target_node_uuid": target_node_uuid,
                "target_share_uuid": target_share_uuid,
                "target_path": target_path,
                "parameters": {
                    "operation": "replicate",
                    "source": source_path,
                    "target_node": target_node_uuid,
                    "target_share": target_share_uuid,
                    "target_path": target_path
                }
            }
            
            task = await self.client.create_task(task_data)
            self.logger.info(f"Replication task created: {task.uuid}")
            
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to replicate file {source_path}: {e}")
            raise
    
    @log_operation("copy_file")
    async def copy_file(self, source_path: str, target_path: str, 
                       target_node_uuid: Optional[str] = None,
                       target_share_uuid: Optional[str] = None) -> Task:
        """
        Copy a file to a new location.
        
        Args:
            source_path: Path to the source file
            target_path: Path for the target file
            target_node_uuid: UUID of the target node (optional)
            target_share_uuid: UUID of the target share (optional)
            
        Returns:
            Task object representing the copy operation
            
        Raises:
            Exception: If copy fails
        """
        try:
            self.logger.info(f"Starting file copy: {source_path} -> {target_path}")
            
            # Create copy task via API
            task_data = {
                "name": f"Copy {source_path}",
                "task_type": "COPY",
                "source_path": source_path,
                "target_path": target_path,
                "target_node_uuid": target_node_uuid,
                "target_share_uuid": target_share_uuid,
                "parameters": {
                    "operation": "copy",
                    "source": source_path,
                    "target": target_path,
                    "target_node": target_node_uuid,
                    "target_share": target_share_uuid
                }
            }
            
            task = await self.client.create_task(task_data)
            self.logger.info(f"Copy task created: {task.uuid}")
            
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to copy file {source_path}: {e}")
            raise
    
    @log_operation("move_file")
    async def move_file(self, source_path: str, target_path: str, 
                       target_node_uuid: Optional[str] = None,
                       target_share_uuid: Optional[str] = None) -> Task:
        """
        Move a file to a new location.
        
        Args:
            source_path: Path to the source file
            target_path: Path for the target file
            target_node_uuid: UUID of the target node (optional)
            target_share_uuid: UUID of the target share (optional)
            
        Returns:
            Task object representing the move operation
            
        Raises:
            Exception: If move fails
        """
        try:
            self.logger.info(f"Starting file move: {source_path} -> {target_path}")
            
            # Create move task via API
            task_data = {
                "name": f"Move {source_path}",
                "task_type": "MOVE",
                "source_path": source_path,
                "target_path": target_path,
                "target_node_uuid": target_node_uuid,
                "target_share_uuid": target_share_uuid,
                "parameters": {
                    "operation": "move",
                    "source": source_path,
                    "target": target_path,
                    "target_node": target_node_uuid,
                    "target_share": target_share_uuid
                }
            }
            
            task = await self.client.create_task(task_data)
            self.logger.info(f"Move task created: {task.uuid}")
            
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to move file {source_path}: {e}")
            raise
    
    @log_operation("replicate_directory")
    async def replicate_directory(self, source_path: str, target_node_uuid: str,
                                target_share_uuid: Optional[str] = None,
                                target_path: Optional[str] = None,
                                recursive: bool = True) -> List[Task]:
        """
        Replicate an entire directory to a target node.
        
        Args:
            source_path: Path to the source directory
            target_node_uuid: UUID of the target node
            target_share_uuid: UUID of the target share (optional)
            target_path: Target path (optional)
            recursive: Whether to replicate subdirectories
            
        Returns:
            List of Task objects representing the replication operations
            
        Raises:
            Exception: If replication fails
        """
        try:
            self.logger.info(f"Starting directory replication: {source_path} -> node {target_node_uuid}")
            
            # Find all files in the directory
            files = await self._find_files_in_directory(source_path, recursive)
            
            if not files:
                self.logger.warning(f"No files found in directory: {source_path}")
                return []
            
            # Create replication tasks for each file
            tasks = []
            for file_info in files:
                file_path = file_info['path']
                if target_path:
                    # Calculate relative path and append to target_path
                    relative_path = file_path[len(source_path):].lstrip('/')
                    target_file_path = f"{target_path}/{relative_path}"
                else:
                    target_file_path = file_path
                
                task = await self.replicate_file(
                    source_path=file_path,
                    target_node_uuid=target_node_uuid,
                    target_share_uuid=target_share_uuid,
                    target_path=target_file_path
                )
                tasks.append(task)
            
            self.logger.info(f"Created {len(tasks)} replication tasks for directory {source_path}")
            return tasks
            
        except Exception as e:
            self.logger.error(f"Failed to replicate directory {source_path}: {e}")
            raise
    
    @log_operation("monitor_task")
    async def monitor_task(self, task_uuid: str, poll_interval: int = 5) -> Task:
        """
        Monitor a data movement task until completion.
        
        Args:
            task_uuid: UUID of the task to monitor
            poll_interval: Polling interval in seconds
            
        Returns:
            Task object with final status
            
        Raises:
            Exception: If monitoring fails
        """
        try:
            self.logger.info(f"Monitoring task: {task_uuid}")
            
            while True:
                task = await self.visibility_ops.monitor_task(task_uuid)
                
                if task.status in ['COMPLETED', 'FAILED', 'CANCELLED']:
                    self.logger.info(f"Task {task_uuid} completed with status: {task.status}")
                    return task
                
                self.logger.debug(f"Task {task_uuid} status: {task.status}, progress: {task.progress}%")
                await asyncio.sleep(poll_interval)
                
        except Exception as e:
            self.logger.error(f"Failed to monitor task {task_uuid}: {e}")
            raise
    
    @log_operation("get_task_status")
    async def get_task_status(self, task_uuid: str) -> Dict[str, Any]:
        """
        Get detailed status of a data movement task.
        
        Args:
            task_uuid: UUID of the task
            
        Returns:
            Dictionary with task status information
            
        Raises:
            Exception: If status retrieval fails
        """
        try:
            task = await self.visibility_ops.monitor_task(task_uuid)
            
            status_info = {
                'uuid': task.uuid,
                'name': task.name,
                'status': task.status,
                'progress': task.progress,
                'created': task.created,
                'modified': task.modified,
                'parameters': task.parameters,
                'error_message': task.error_message if hasattr(task, 'error_message') else None
            }
            
            self.logger.info(f"Task {task_uuid} status: {task.status}")
            return status_info
            
        except Exception as e:
            self.logger.error(f"Failed to get task status {task_uuid}: {e}")
            raise
    
    @log_operation("cancel_task")
    async def cancel_task(self, task_uuid: str) -> bool:
        """
        Cancel a running data movement task.
        
        Args:
            task_uuid: UUID of the task to cancel
            
        Returns:
            True if cancellation successful
            
        Raises:
            Exception: If cancellation fails
        """
        try:
            self.logger.info(f"Cancelling task: {task_uuid}")
            
            # Cancel task via API
            success = await self.client.cancel_task(task_uuid)
            
            if success:
                self.logger.info(f"Task {task_uuid} cancelled successfully")
            else:
                self.logger.warning(f"Failed to cancel task {task_uuid}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to cancel task {task_uuid}: {e}")
            raise
    
    @log_operation("list_active_tasks")
    async def list_active_tasks(self, task_type: Optional[str] = None) -> TaskList:
        """
        List all active data movement tasks.
        
        Args:
            task_type: Filter by task type (REPLICATION, COPY, MOVE)
            
        Returns:
            List of active Task objects
            
        Raises:
            Exception: If task listing fails
        """
        try:
            self.logger.info("Listing active data movement tasks")
            
            # Get all tasks and filter for active ones
            all_tasks = await self.client.get_tasks()
            
            active_tasks = [
                task for task in all_tasks
                if task.status in ['PENDING', 'RUNNING', 'PAUSED']
            ]
            
            if task_type:
                active_tasks = [
                    task for task in active_tasks
                    if task.task_type == task_type
                ]
            
            self.logger.info(f"Found {len(active_tasks)} active tasks")
            return active_tasks
            
        except Exception as e:
            self.logger.error(f"Failed to list active tasks: {e}")
            raise
    
    async def _find_files_in_directory(self, directory_path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Find all files in a directory using the catalog search.
        
        Args:
            directory_path: Path to the directory
            recursive: Whether to include subdirectories
            
        Returns:
            List of file information dictionaries
        """
        try:
            # Search for files in the directory
            query = ""
            filters = {
                "item_type": "file"
            }
            
            if recursive:
                # Search for files that start with the directory path
                query = directory_path
            else:
                # Search for files directly in the directory (not in subdirectories)
                # This is a simplified approach - in a real implementation,
                # you might need more sophisticated path matching
                query = directory_path
            
            files = await search_catalog_advanced(
                query=query,
                filters=filters,
                limit=1000  # Adjust as needed
            )
            
            # Filter results to ensure they're actually in the directory
            if not recursive:
                # For non-recursive, only include files directly in the directory
                filtered_files = []
                for file_info in files:
                    file_path = file_info['path']
                    if file_path.startswith(directory_path):
                        # Remove the directory path and check if there are no more slashes
                        relative_path = file_path[len(directory_path):].lstrip('/')
                        if '/' not in relative_path:
                            filtered_files.append(file_info)
                files = filtered_files
            
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to find files in directory {directory_path}: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the data movement operations."""
        if self.client:
            await self.client.close()


# Convenience functions for common operations
async def replicate_file_to_node(source_path: str, target_node_uuid: str, 
                                target_share_uuid: Optional[str] = None,
                                target_path: Optional[str] = None) -> Task:
    """
    Convenience function to replicate a file to a specific node.
    
    Args:
        source_path: Path to the source file
        target_node_uuid: UUID of the target node
        target_share_uuid: UUID of the target share (optional)
        target_path: Target path (optional)
        
    Returns:
        Task object representing the replication operation
    """
    async with DataMovementOperations() as ops:
        return await ops.replicate_file(source_path, target_node_uuid, target_share_uuid, target_path)


async def copy_file_to_location(source_path: str, target_path: str,
                               target_node_uuid: Optional[str] = None,
                               target_share_uuid: Optional[str] = None) -> Task:
    """
    Convenience function to copy a file to a new location.
    
    Args:
        source_path: Path to the source file
        target_path: Path for the target file
        target_node_uuid: UUID of the target node (optional)
        target_share_uuid: UUID of the target share (optional)
        
    Returns:
        Task object representing the copy operation
    """
    async with DataMovementOperations() as ops:
        return await ops.copy_file(source_path, target_path, target_node_uuid, target_share_uuid)


async def move_file_to_location(source_path: str, target_path: str,
                               target_node_uuid: Optional[str] = None,
                               target_share_uuid: Optional[str] = None) -> Task:
    """
    Convenience function to move a file to a new location.
    
    Args:
        source_path: Path to the source file
        target_path: Path for the target file
        target_node_uuid: UUID of the target node (optional)
        target_share_uuid: UUID of the target share (optional)
        
    Returns:
        Task object representing the move operation
    """
    async with DataMovementOperations() as ops:
        return await ops.move_file(source_path, target_path, target_node_uuid, target_share_uuid) 