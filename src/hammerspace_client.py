"""
Hammerspace DataSphere REST API client for the Federated Storage MCP Service.
Handles authentication, HTTP requests, and response parsing with concurrency control.
"""

import base64
import json
import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
import requests
from urllib.parse import urljoin
from dataclasses import dataclass
from datetime import datetime

from config import get_config, HammerspaceConfig
from models import Node, StorageVolume, ObjectStorageVolume, Share, File, Task, NodeType, VolumeState, TaskStatus, Objective, ObjectiveType, ObjectiveState, DataMovementJob, DataMovementType, DataMovementRequest, ObjectiveTemplate
from logging_config import get_logger, log_api_call


@dataclass
class QueueStats:
    """Queue statistics for monitoring."""
    queue_depth: int
    active_requests: int
    total_requests: int
    failed_requests: int
    average_response_time: float
    last_updated: datetime


class HammerspaceClientError(Exception):
    """Base exception for Hammerspace client errors."""
    pass


class AuthenticationError(HammerspaceClientError):
    """Raised when authentication fails."""
    pass


class APIError(HammerspaceClientError):
    """Raised when API calls fail."""
    pass


class ConcurrencyLimitError(HammerspaceClientError):
    """Raised when concurrency limit is exceeded."""
    pass


class HammerspaceClient:
    """Client for Hammerspace DataSphere REST API with concurrency control."""
    
    def __init__(self, config: Optional[HammerspaceConfig] = None, max_concurrent_requests: int = 2):
        """
        Initialize Hammerspace client with concurrency control.
        
        Args:
            config: Hammerspace configuration. If None, loads from global config.
            max_concurrent_requests: Maximum number of concurrent API requests (default: 2)
        """
        self.config = config or get_config().get_hammerspace_config()
        self.logger = get_logger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self._auth_headers = self._create_auth_headers()
        
        # Concurrency control
        self.max_concurrent_requests = max_concurrent_requests
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._request_queue = asyncio.Queue()
        self._active_requests = 0
        self._total_requests = 0
        self._failed_requests = 0
        self._response_times = []
        self._queue_stats = QueueStats(
            queue_depth=0,
            active_requests=0,
            total_requests=0,
            failed_requests=0,
            average_response_time=0.0,
            last_updated=datetime.now()
        )
        
    def _create_auth_headers(self) -> Dict[str, str]:
        """Create authentication headers for API requests."""
        credentials = f"{self.config.username}:{self.config.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()
    
    async def _create_session(self):
        """Create aiohttp session."""
        if self.session is None:
            connector = aiohttp.TCPConnector(verify_ssl=self.config.verify_ssl)
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self._auth_headers
            )
    
    async def _close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _execute_with_concurrency_control(self, api_call_name: str, api_call_func, *args, **kwargs):
        """
        Execute an API call with concurrency control.
        
        Args:
            api_call_name: Name of the API call for logging
            api_call_func: The actual API call function
            *args, **kwargs: Arguments for the API call
            
        Returns:
            Result of the API call
            
        Raises:
            ConcurrencyLimitError: If concurrency limit is exceeded
            APIError: If API call fails
        """
        start_time = datetime.now()
        request_id = self._total_requests + 1
        
        self.logger.info(f"🔄 API QUEUE: Request #{request_id} '{api_call_name}' queued (queue depth: {self._request_queue.qsize()})")
        
        # Add request to queue
        await self._request_queue.put({
            'id': request_id,
            'name': api_call_name,
            'start_time': start_time,
            'args': args,
            'kwargs': kwargs
        })
        
        try:
            # Acquire semaphore to limit concurrent requests
            async with self._semaphore:
                self._active_requests += 1
                self._total_requests += 1
                
                # Remove from queue
                await self._request_queue.get()
                
                self.logger.info(f"🚀 API EXEC: Request #{request_id} '{api_call_name}' executing (active: {self._active_requests})")
                
                # Execute the actual API call
                result = await api_call_func(*args, **kwargs)
                
                # Record response time
                response_time = (datetime.now() - start_time).total_seconds()
                self._response_times.append(response_time)
                if len(self._response_times) > 100:  # Keep last 100 response times
                    self._response_times.pop(0)
                
                self.logger.info(f"✅ API SUCCESS: Request #{request_id} '{api_call_name}' completed in {response_time:.3f}s")
                
                return result
                
        except Exception as e:
            self._failed_requests += 1
            self.logger.error(f"❌ API ERROR: Request #{request_id} '{api_call_name}' failed: {e}")
            raise APIError(f"API call '{api_call_name}' failed: {e}")
            
        finally:
            self._active_requests -= 1
            self._update_queue_stats()
    
    def _update_queue_stats(self):
        """Update queue statistics."""
        avg_response_time = sum(self._response_times) / len(self._response_times) if self._response_times else 0.0
        
        self._queue_stats = QueueStats(
            queue_depth=self._request_queue.qsize(),
            active_requests=self._active_requests,
            total_requests=self._total_requests,
            failed_requests=self._failed_requests,
            average_response_time=avg_response_time,
            last_updated=datetime.now()
        )
    
    def get_queue_stats(self) -> QueueStats:
        """Get current queue statistics."""
        self._update_queue_stats()
        return self._queue_stats
    
    async def get_queue_depth(self) -> int:
        """Get current queue depth."""
        return self._request_queue.qsize()
    
    async def get_active_requests(self) -> int:
        """Get number of currently active requests."""
        return self._active_requests
    
    async def get_task_queue_status(self) -> Dict[str, Any]:
        """
        Get task queue status from Hammerspace API.
        This checks if there are pending/running tasks that might indicate queue depth.
        """
        try:
            tasks = await self._execute_with_concurrency_control(
                "get_tasks", 
                self._get_tasks_internal
            )
            
            # Analyze task statuses
            pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
            running_tasks = [t for t in tasks if t.status == TaskStatus.RUNNING]
            
            return {
                "pending_tasks": len(pending_tasks),
                "running_tasks": len(running_tasks),
                "total_tasks": len(tasks),
                "queue_depth_estimate": len(pending_tasks),
                "system_load": len(running_tasks)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get task queue status: {e}")
            return {
                "pending_tasks": 0,
                "running_tasks": 0,
                "total_tasks": 0,
                "queue_depth_estimate": 0,
                "system_load": 0,
                "error": str(e)
            }
    
    async def _get_tasks_internal(self) -> List[Task]:
        """Internal method to get tasks without concurrency control."""
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, "tasks")
        
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                
                tasks = []
                for task_data in data:
                    task = self._parse_task(task_data)
                    tasks.append(task)
                
                return tasks
                
        except Exception as e:
            self.logger.error(f"Failed to get tasks: {e}")
            raise APIError(f"Failed to get tasks: {e}")
    
    @log_api_call("/nodes", "GET")
    async def get_nodes(self) -> List[Node]:
        """
        Get all storage nodes.
        
        Returns:
            List of Node objects
            
        Raises:
            APIError: If API call fails
        """
        return await self._execute_with_concurrency_control(
            "get_nodes",
            self._get_nodes_internal
        )
    
    async def _get_nodes_internal(self) -> List[Node]:
        """Internal method to get nodes without concurrency control."""
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, "nodes")
        
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                
                nodes = []
                for node_data in data:
                    node = self._parse_node(node_data)
                    nodes.append(node)
                
                self.logger.info(f"Retrieved {len(nodes)} nodes")
                return nodes
                
        except Exception as e:
            self.logger.error(f"Failed to get nodes: {e}")
            raise APIError(f"Failed to get nodes: {e}")
    
    @log_api_call("/nodes/{identifier}", "GET")
    async def get_node(self, identifier: str) -> Node:
        """
        Get specific node by identifier.
        
        Args:
            identifier: Node UUID or name
            
        Returns:
            Node object
            
        Raises:
            APIError: If API call fails
        """
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, f"nodes/{identifier}")
        
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                
                node = self._parse_node(data)
                self.logger.info(f"Retrieved node: {node.name}")
                return node
                
        except Exception as e:
            self.logger.error(f"Failed to get node {identifier}: {e}")
            raise APIError(f"Failed to get node {identifier}: {e}")
    
    @log_api_call("/storage-volumes", "GET")
    async def get_storage_volumes(self) -> List[StorageVolume]:
        """
        Get all storage volumes.
        """
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
        # Ensure base_url ends with a slash
        base_url = self.config.base_url
        if not base_url.endswith("/"):
            base_url += "/"
        url = urljoin(base_url, "storage-volumes")
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                volumes = []
                for volume_data in data:
                    volume = self._parse_storage_volume(volume_data)
                    volumes.append(volume)
                self.logger.info(f"Retrieved {len(volumes)} storage volumes")
                return volumes
        except Exception as e:
            self.logger.error(f"Failed to get storage volumes: {e}")
            raise APIError(f"Failed to get storage volumes: {e}")
    
    @log_api_call("/object-storage-volumes", "GET")
    async def get_object_storage_volumes(self) -> List[ObjectStorageVolume]:
        """
        Get all object storage volumes.
        
        Returns:
            List of ObjectStorageVolume objects
            
        Raises:
            APIError: If API call fails
        """
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, "object-storage-volumes")
        
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                
                volumes = []
                for volume_data in data:
                    volume = self._parse_object_storage_volume(volume_data)
                    volumes.append(volume)
                
                self.logger.info(f"Retrieved {len(volumes)} object storage volumes")
                return volumes
                
        except Exception as e:
            self.logger.error(f"Failed to get object storage volumes: {e}")
            raise APIError(f"Failed to get object storage volumes: {e}")
    
    @log_api_call("/shares", "GET")
    async def get_shares(self) -> List[Share]:
        """
        Get all shares.
        
        Returns:
            List of Share objects
            
        Raises:
            APIError: If API call fails
        """
        return await self._execute_with_concurrency_control(
            "get_shares",
            self._get_shares_internal
        )
    
    async def _get_shares_internal(self) -> List[Share]:
        """Internal method to get shares without concurrency control."""
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, "shares")
        self.logger.info(f"Making request to: {url}")
        
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                
                shares = []
                for share_data in data:
                    share = self._parse_share(share_data)
                    shares.append(share)
                
                self.logger.info(f"Retrieved {len(shares)} shares")
                return shares
                
        except Exception as e:
            self.logger.error(f"Failed to get shares: {e}")
            raise APIError(f"Failed to get shares: {e}")
    
    @log_api_call("/files", "GET")
    async def get_file_info(self, path: Optional[str] = None) -> Optional[File]:
        """
        Get file information.
        
        Args:
            path: File path (optional)
            
        Returns:
            File object or None if not found
            
        Raises:
            APIError: If API call fails
        """
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, "files")
        
        params = {}
        if path:
            params["path"] = path
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 404:
                    return None
                
                await self._check_response(response)
                data = await response.json()
                
                file_obj = self._parse_file(data)
                self.logger.info(f"Retrieved file info: {file_obj.name}")
                return file_obj
                
        except Exception as e:
            self.logger.error(f"Failed to get file info for {path}: {e}")
            raise APIError(f"Failed to get file info for {path}: {e}")
    
    @log_api_call("/files/search", "GET")
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
            APIError: If API call fails
        """
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, "files")
        
        # The API requires a path parameter starting with "/"
        # If query is "*", use "/" to get all files
        # But we need to ensure the path starts with "/" for the API
        if query == "*":
            path = "/"
        elif query.startswith("/"):
            path = query
        else:
            path = f"/{query}"
        
        params = {
            "path": path,
            "limit": limit,
            "offset": offset
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                await self._check_response(response)
                data = await response.json()
                
                files = []
                # The /files endpoint returns a single file/directory object with a 'children' array
                if data.get("children"):
                    for file_data in data["children"]:
                        file_obj = self._parse_file(file_data)
                        files.append(file_obj)
                
                self.logger.info(f"Retrieved {len(files)} files matching path: {path}")
                return files
                
        except Exception as e:
            self.logger.error(f"Failed to search files with path '{path}': {e}")
            raise APIError(f"Failed to search files with path '{path}': {e}")
    
    @log_api_call("/files/count", "GET")
    async def get_file_count(self, query: str = "*") -> int:
        """
        Get the total count of files matching a query.
        
        Args:
            query: Search query (default: "*" for all files)
            
        Returns:
            Total count of files matching the query
            
        Raises:
            APIError: If API call fails
        """
        return await self._execute_with_concurrency_control(
            "get_file_count",
            self._get_file_count_internal,
            query
        )
    
    async def _get_file_count_internal(self, query: str = "*") -> int:
        """Internal method to get file count without concurrency control."""
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        # Get all shares and sum their file counts
        url = urljoin(self.config.base_url, "shares")
        
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                
                total_files = 0
                for share_data in data:
                    # Each share has a totalNumberOfFiles field
                    share_files = share_data.get("totalNumberOfFiles", 0)
                    total_files += share_files
                
                self.logger.info(f"Retrieved file count: {total_files} files across all shares")
                return total_files
                
        except Exception as e:
            self.logger.error(f"Failed to get file count: {e}")
            raise APIError(f"Failed to get file count: {e}")
    
    @log_api_call("/tasks/{taskId}", "GET")
    async def get_task(self, task_uuid: str) -> Task:
        """
        Get specific task by UUID.
        
        Args:
            task_uuid: Task UUID
            
        Returns:
            Task object
            
        Raises:
            APIError: If API call fails
        """
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, f"tasks/{task_uuid}")
        
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                
                task = self._parse_task(data)
                self.logger.info(f"Retrieved task: {task.name}")
                return task
                
        except Exception as e:
            self.logger.error(f"Failed to get task {task_uuid}: {e}")
            raise APIError(f"Failed to get task {task_uuid}: {e}")
    
    @log_api_call("/tasks", "GET")
    async def get_tasks(self) -> List[Task]:
        """
        Get all tasks.
        
        Returns:
            List of Task objects
            
        Raises:
            APIError: If API call fails
        """
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, "tasks")
        
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                
                tasks = []
                for task_data in data:
                    task = self._parse_task(task_data)
                    tasks.append(task)
                
                self.logger.info(f"Retrieved {len(tasks)} tasks")
                return tasks
                
        except Exception as e:
            self.logger.error(f"Failed to get tasks: {e}")
            raise APIError(f"Failed to get tasks: {e}")
    
    @log_api_call("/tasks", "POST")
    async def create_task(self, task_data: Dict[str, Any]) -> Task:
        """
        Create a new task.
        
        Args:
            task_data: Task data dictionary
            
        Returns:
            Task object
            
        Raises:
            APIError: If API call fails
        """
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, "tasks")
        
        try:
            async with self.session.post(url, json=task_data) as response:
                await self._check_response(response)
                data = await response.json()
                
                task = self._parse_task(data)
                self.logger.info(f"Created task: {task.name}")
                return task
                
        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            raise APIError(f"Failed to create task: {e}")
    
    @log_api_call("/tasks/{taskId}/cancel", "POST")
    async def cancel_task(self, task_uuid: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_uuid: Task UUID to cancel
            
        Returns:
            True if cancellation successful
            
        Raises:
            APIError: If API call fails
        """
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, f"tasks/{task_uuid}/cancel")
        
        try:
            async with self.session.post(url) as response:
                await self._check_response(response)
                self.logger.info(f"Cancelled task: {task_uuid}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to cancel task {task_uuid}: {e}")
            raise APIError(f"Failed to cancel task {task_uuid}: {e}")
    
    async def close(self):
        """Close the client session."""
        await self._close_session()
    
    # Objectives and Data Movement Methods
    
    @log_api_call("/objectives", "GET")
    async def get_objectives(self) -> List[Objective]:
        """
        Get all objectives.
        
        Returns:
            List of Objective objects
            
        Raises:
            APIError: If API call fails
        """
        return await self._execute_with_concurrency_control(
            "get_objectives",
            self._get_objectives_internal
        )
    
    async def _get_objectives_internal(self) -> List[Objective]:
        """Internal method to get objectives without concurrency control."""
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, "objectives")
        
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                
                objectives = []
                for objective_data in data:
                    objective = self._parse_objective(objective_data)
                    objectives.append(objective)
                
                self.logger.info(f"Retrieved {len(objectives)} objectives")
                return objectives
                
        except Exception as e:
            self.logger.error(f"Failed to get objectives: {e}")
            raise APIError(f"Failed to get objectives: {e}")
    
    @log_api_call("/objectives", "POST")
    async def create_objective(self, objective_data: Dict[str, Any]) -> Objective:
        """
        Create a new objective.
        
        Args:
            objective_data: Objective data dictionary
            
        Returns:
            Objective object
            
        Raises:
            APIError: If API call fails
        """
        return await self._execute_with_concurrency_control(
            "create_objective",
            self._create_objective_internal,
            objective_data
        )
    
    async def _create_objective_internal(self, objective_data: Dict[str, Any]) -> Objective:
        """Internal method to create objective without concurrency control."""
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, "objectives")
        
        try:
            async with self.session.post(url, json=objective_data) as response:
                await self._check_response(response)
                data = await response.json()
                
                objective = self._parse_objective(data)
                self.logger.info(f"Created objective: {objective.name}")
                return objective
                
        except Exception as e:
            self.logger.error(f"Failed to create objective: {e}")
            raise APIError(f"Failed to create objective: {e}")
    
    @log_api_call("/objectives/{objectiveId}", "DELETE")
    async def delete_objective(self, objective_uuid: str) -> bool:
        """
        Delete an objective.
        
        Args:
            objective_uuid: Objective UUID to delete
            
        Returns:
            True if deletion successful
            
        Raises:
            APIError: If API call fails
        """
        return await self._execute_with_concurrency_control(
            "delete_objective",
            self._delete_objective_internal,
            objective_uuid
        )
    
    async def _delete_objective_internal(self, objective_uuid: str) -> bool:
        """Internal method to delete objective without concurrency control."""
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, f"objectives/{objective_uuid}")
        
        try:
            async with self.session.delete(url) as response:
                await self._check_response(response)
                self.logger.info(f"Deleted objective: {objective_uuid}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to delete objective {objective_uuid}: {e}")
            raise APIError(f"Failed to delete objective {objective_uuid}: {e}")
    
    # Data Movement Methods
    
    async def create_data_movement_job(self, request: DataMovementRequest) -> DataMovementJob:
        """
        Create a data movement job.
        
        Args:
            request: Data movement request
            
        Returns:
            DataMovementJob object
            
        Raises:
            APIError: If API call fails
        """
        return await self._execute_with_concurrency_control(
            "create_data_movement_job",
            self._create_data_movement_job_internal,
            request
        )
    
    async def _create_data_movement_job_internal(self, request: DataMovementRequest) -> DataMovementJob:
        """Internal method to create data movement job without concurrency control."""
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, "data-movement/jobs")
        
        # Convert request to API format
        job_data = {
            "name": f"{request.movement_type.value}_{request.source_path.replace('/', '_')}",
            "movementType": request.movement_type.value,
            "sourcePath": request.source_path,
            "destinationPath": request.destination_path,
            "sourceShareUuid": request.source_share_uuid,
            "destinationShareUuid": request.destination_share_uuid,
            "sourceVolumeUuid": request.source_volume_uuid,
            "destinationVolumeUuid": request.destination_volume_uuid,
            "overwrite": request.overwrite,
            "preserveMetadata": request.preserve_metadata,
            "verifyChecksum": request.verify_checksum,
            "priority": request.priority,
            "schedule": request.schedule,
            "parameters": request.parameters or {}
        }
        
        try:
            async with self.session.post(url, json=job_data) as response:
                await self._check_response(response)
                data = await response.json()
                
                job = self._parse_data_movement_job(data)
                self.logger.info(f"Created data movement job: {job.name}")
                return job
                
        except Exception as e:
            self.logger.error(f"Failed to create data movement job: {e}")
            raise APIError(f"Failed to create data movement job: {e}")
    
    @log_api_call("/data-movement/jobs", "GET")
    async def get_data_movement_jobs(self) -> List[DataMovementJob]:
        """
        Get all data movement jobs.
        
        Returns:
            List of DataMovementJob objects
            
        Raises:
            APIError: If API call fails
        """
        return await self._execute_with_concurrency_control(
            "get_data_movement_jobs",
            self._get_data_movement_jobs_internal
        )
    
    async def _get_data_movement_jobs_internal(self) -> List[DataMovementJob]:
        """Internal method to get data movement jobs without concurrency control."""
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, "data-movement/jobs")
        
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                
                jobs = []
                for job_data in data:
                    job = self._parse_data_movement_job(job_data)
                    jobs.append(job)
                
                self.logger.info(f"Retrieved {len(jobs)} data movement jobs")
                return jobs
                
        except Exception as e:
            self.logger.error(f"Failed to get data movement jobs: {e}")
            raise APIError(f"Failed to get data movement jobs: {e}")
    
    @log_api_call("/data-movement/jobs/{jobId}", "GET")
    async def get_data_movement_job(self, job_uuid: str) -> DataMovementJob:
        """
        Get specific data movement job by UUID.
        
        Args:
            job_uuid: Job UUID
            
        Returns:
            DataMovementJob object
            
        Raises:
            APIError: If API call fails
        """
        return await self._execute_with_concurrency_control(
            "get_data_movement_job",
            self._get_data_movement_job_internal,
            job_uuid
        )
    
    async def _get_data_movement_job_internal(self, job_uuid: str) -> DataMovementJob:
        """Internal method to get data movement job without concurrency control."""
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, f"data-movement/jobs/{job_uuid}")
        
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                
                job = self._parse_data_movement_job(data)
                self.logger.info(f"Retrieved data movement job: {job.name}")
                return job
                
        except Exception as e:
            self.logger.error(f"Failed to get data movement job {job_uuid}: {e}")
            raise APIError(f"Failed to get data movement job {job_uuid}: {e}")
    
    # Convenience Methods for Common Operations
    
    async def copy_file(self, source_path: str, destination_path: str, **kwargs) -> DataMovementJob:
        """
        Copy a file from source to destination.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            **kwargs: Additional parameters for DataMovementRequest
            
        Returns:
            DataMovementJob object
        """
        request = DataMovementRequest(
            movement_type=DataMovementType.FILE_COPY,
            source_path=source_path,
            destination_path=destination_path,
            **kwargs
        )
        return await self.create_data_movement_job(request)
    
    async def move_file(self, source_path: str, destination_path: str, **kwargs) -> DataMovementJob:
        """
        Move a file from source to destination.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            **kwargs: Additional parameters for DataMovementRequest
            
        Returns:
            DataMovementJob object
        """
        request = DataMovementRequest(
            movement_type=DataMovementType.FILE_MOVE,
            source_path=source_path,
            destination_path=destination_path,
            **kwargs
        )
        return await self.create_data_movement_job(request)
    
    async def copy_directory(self, source_path: str, destination_path: str, **kwargs) -> DataMovementJob:
        """
        Copy a directory from source to destination.
        
        Args:
            source_path: Source directory path
            destination_path: Destination directory path
            **kwargs: Additional parameters for DataMovementRequest
            
        Returns:
            DataMovementJob object
        """
        request = DataMovementRequest(
            movement_type=DataMovementType.DIRECTORY_COPY,
            source_path=source_path,
            destination_path=destination_path,
            **kwargs
        )
        return await self.create_data_movement_job(request)
    
    async def replicate_share(self, source_share_uuid: str, destination_share_uuid: str, **kwargs) -> DataMovementJob:
        """
        Replicate a share to another share.
        
        Args:
            source_share_uuid: Source share UUID
            destination_share_uuid: Destination share UUID
            **kwargs: Additional parameters for DataMovementRequest
            
        Returns:
            DataMovementJob object
        """
        request = DataMovementRequest(
            movement_type=DataMovementType.SHARE_REPLICATION,
            source_path=f"share:{source_share_uuid}",
            destination_path=f"share:{destination_share_uuid}",
            source_share_uuid=source_share_uuid,
            destination_share_uuid=destination_share_uuid,
            **kwargs
        )
        return await self.create_data_movement_job(request)
    
    # Metadata and Tagging Methods
    
    @log_api_call("/shares/{share_uuid}", "PUT")
    async def update_share_metadata(self, share_uuid: str, metadata: Dict[str, Any]) -> Share:
        """
        Update metadata/tags for a share using the extended_info field.
        
        Args:
            share_uuid: Share UUID to update
            metadata: Dictionary of metadata/tags to set
            
        Returns:
            Updated Share object
            
        Raises:
            APIError: If API call fails
        """
        return await self._execute_with_concurrency_control(
            "update_share_metadata",
            self._update_share_metadata_internal,
            share_uuid,
            metadata
        )
    
    async def _update_share_metadata_internal(self, share_uuid: str, metadata: Dict[str, Any]) -> Share:
        """Internal method to update share metadata without concurrency control."""
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
        
        # First, get the current share data to preserve existing fields
        current_share = await self.get_share(share_uuid)
        
        # Prepare the update payload
        update_data = {
            "uoid": {
                "uuid": share_uuid,
                "objectType": "SHARE"
            },
            "name": current_share.name,
            "shareState": "PUBLISHED",  # Assuming published state
            "modified": str(int(datetime.now().timestamp() * 1000)),  # Current timestamp in milliseconds
            "extendedInfo": {
                **(current_share.extended_info or {}),  # Preserve existing extended_info
                **metadata  # Add/update with new metadata
            }
        }
        
        # Add smbAliases if they exist
        if current_share.smb_aliases:
            update_data["smbAliases"] = [
                {
                    "name": alias,
                    "path": "/",  # Default path
                    "modified": int(datetime.now().timestamp() * 1000)
                }
                for alias in current_share.smb_aliases
            ]
        
        url = urljoin(self.config.base_url, f"shares/{share_uuid}")
        
        try:
            async with self.session.put(url, json=update_data) as response:
                await self._check_response(response)
                
                # The API returns a 202 with a task location, so we need to get the updated share
                if response.status == 202:
                    # Wait a moment for the update to complete, then fetch the updated share
                    await asyncio.sleep(1)
                    updated_share = await self.get_share(share_uuid)
                    self.logger.info(f"Updated metadata for share: {updated_share.name}")
                    return updated_share
                else:
                    # If it's not a 202, try to parse the response as a share
                    data = await response.json()
                    share = self._parse_share(data)
                    self.logger.info(f"Updated metadata for share: {share.name}")
                    return share
                
        except Exception as e:
            self.logger.error(f"Failed to update share metadata for {share_uuid}: {e}")
            raise APIError(f"Failed to update share metadata for {share_uuid}: {e}")
    
    async def get_share(self, share_uuid: str) -> Share:
        """
        Get a specific share by UUID.
        
        Args:
            share_uuid: Share UUID
            
        Returns:
            Share object
            
        Raises:
            APIError: If API call fails
        """
        await self._create_session()
        if not self.session:
            raise APIError("Failed to create session")
            
        url = urljoin(self.config.base_url, f"shares/{share_uuid}")
        
        try:
            async with self.session.get(url) as response:
                await self._check_response(response)
                data = await response.json()
                
                share = self._parse_share(data)
                self.logger.info(f"Retrieved share: {share.name}")
                return share
                
        except Exception as e:
            self.logger.error(f"Failed to get share {share_uuid}: {e}")
            raise APIError(f"Failed to get share {share_uuid}: {e}")
    
    async def get_share_tags(self, share_uuid: str) -> Dict[str, Any]:
        """
        Get tags/metadata for a specific share.
        
        Args:
            share_uuid: Share UUID
            
        Returns:
            Dictionary of tags/metadata from extended_info
            
        Raises:
            APIError: If API call fails
        """
        share = await self.get_share(share_uuid)
        return share.extended_info or {}
    
    async def set_share_tags(self, share_uuid: str, tags: Dict[str, Any]) -> Share:
        """
        Set tags/metadata for a specific share.
        
        Args:
            share_uuid: Share UUID
            tags: Dictionary of tags/metadata to set
            
        Returns:
            Updated Share object
            
        Raises:
            APIError: If API call fails
        """
        return await self.update_share_metadata(share_uuid, tags)
    
    # Objective Templates
    
    def get_objective_templates(self) -> List[ObjectiveTemplate]:
        """
        Get predefined objective templates.
        
        Returns:
            List of ObjectiveTemplate objects
        """
        return [
            ObjectiveTemplate(
                name="Daily Backup",
                objective_type=ObjectiveType.BACKUP,
                description="Daily backup of critical data",
                source_pattern="/critical-data/*",
                destination_pattern="/backup/daily/{date}",
                parameters={
                    "retention_days": 30,
                    "compression": True,
                    "encryption": True
                },
                schedule={
                    "type": "daily",
                    "time": "02:00",
                    "timezone": "UTC"
                },
                examples=[
                    "Create daily backup of /opmtesting to /backup/daily",
                    "Backup critical files with 30-day retention"
                ]
            ),
            ObjectiveTemplate(
                name="Cross-Site Replication",
                objective_type=ObjectiveType.REPLICATION,
                description="Replicate data across storage sites",
                source_pattern="/{share}/*",
                destination_pattern="/replica/{share}/*",
                parameters={
                    "sync_interval": 3600,
                    "conflict_resolution": "source_wins",
                    "bandwidth_limit": "100MB/s"
                },
                examples=[
                    "Replicate /opmtesting to remote site",
                    "Sync data between primary and secondary storage"
                ]
            ),
            ObjectiveTemplate(
                name="Archive Old Data",
                objective_type=ObjectiveType.ARCHIVE,
                description="Archive data older than specified days",
                source_pattern="/{share}/*",
                destination_pattern="/archive/{year}/{month}",
                parameters={
                    "age_days": 365,
                    "compression": True,
                    "delete_source": False
                },
                examples=[
                    "Archive files older than 1 year",
                    "Move old data to archive storage"
                ]
            ),
            ObjectiveTemplate(
                name="Performance Migration",
                objective_type=ObjectiveType.MIGRATION,
                description="Migrate data to faster storage",
                source_pattern="/slow-storage/*",
                destination_pattern="/fast-storage/*",
                parameters={
                    "migration_strategy": "incremental",
                    "validate_checksums": True,
                    "preserve_permissions": True
                },
                examples=[
                    "Migrate data from slow to fast storage",
                    "Move frequently accessed files to SSD"
                ]
            )
        ]
    
    async def _check_response(self, response: aiohttp.ClientResponse):
        """Check HTTP response and raise appropriate exceptions."""
        if response.status == 401:
            raise AuthenticationError("Authentication failed. Check credentials.")
        elif response.status == 403:
            raise AuthenticationError("Access denied. Check permissions.")
        elif response.status >= 400:
            error_text = await response.text()
            raise APIError(f"API error {response.status}: {error_text}")
    
    def _parse_node(self, data: Dict[str, Any]) -> Node:
        """Parse node data from API response."""
        try:
            node_type = NodeType(data.get("nodeType", "GENERIC_S3"))
        except ValueError:
            node_type = NodeType.GENERIC_S3
        
        return Node(
            uuid=data.get("uoid", {}).get("uuid", ""),
            name=data.get("name", ""),
            node_type=node_type,
            endpoint=data.get("endpoint"),
            state=data.get("state", "OK"),
            created=self._parse_timestamp(data.get("created")),
            modified=self._parse_timestamp(data.get("modified")),
            platform_services=data.get("platformServices", []),
            extended_info=data.get("extendedInfo", {})
        )
    
    def _parse_storage_volume(self, data: Dict[str, Any]) -> StorageVolume:
        """Parse storage volume data from API response."""
        try:
            state = VolumeState(data.get("storageVolumeState", "OK"))
        except ValueError:
            state = VolumeState.OK
        
        return StorageVolume(
            uuid=data.get("uoid", {}).get("uuid", ""),
            name=data.get("name", ""),
            volume_type=data.get("_type", ""),
            state=state,
            node_uuid=data.get("nodeUuid"),
            created=self._parse_timestamp(data.get("created")),
            modified=self._parse_timestamp(data.get("modified")),
            size_bytes=data.get("sizeBytes"),
            used_bytes=data.get("usedBytes"),
            extended_info=data.get("extendedInfo", {})
        )
    
    def _parse_object_storage_volume(self, data: Dict[str, Any]) -> ObjectStorageVolume:
        """Parse object storage volume data from API response."""
        try:
            state = VolumeState(data.get("storageVolumeState", "OK"))
        except ValueError:
            state = VolumeState.OK
        
        return ObjectStorageVolume(
            uuid=data.get("uoid", {}).get("uuid", ""),
            name=data.get("name", ""),
            object_store_logical_volume=data.get("objectStoreLogicalVolume", {}),
            storage_volume_state=state,
            created=self._parse_timestamp(data.get("created")),
            modified=self._parse_timestamp(data.get("modified")),
            extended_info=data.get("extendedInfo", {})
        )
    
    def _parse_share(self, data: Dict[str, Any]) -> Share:
        """Parse share data from API response."""
        # Extract objectives from the objectives section
        objectives = data.get("objectives", {})
        active_objectives = objectives.get("activeObjectives", [])
        applied_objectives = objectives.get("appliedObjectives", [])
        
        return Share(
            uuid=data.get("uoid", {}).get("uuid", ""),
            name=data.get("name", ""),
            path=data.get("path", ""),
            created=self._parse_timestamp(data.get("created")),
            modified=self._parse_timestamp(data.get("modified")),
            smb_aliases=data.get("smbAliases", []),
            active_objectives=active_objectives,
            applied_objectives=applied_objectives,
            total_number_of_files=data.get("totalNumberOfFiles"),
            extended_info=data.get("extendedInfo", {})
        )
    
    def _parse_file(self, data: Dict[str, Any]) -> File:
        """Parse file data from API response."""
        return File(
            uuid=data.get("uoid", {}).get("uuid", ""),
            path=data.get("path", ""),
            name=data.get("name", ""),
            size_bytes=data.get("sizeBytes"),
            share_uuid=data.get("shareUuid"),
            volume_uuid=data.get("volumeUuid"),
            node_uuid=data.get("nodeUuid"),
            created=self._parse_timestamp(data.get("created")),
            modified=self._parse_timestamp(data.get("modified")),
            extended_info=data.get("extendedInfo", {}),
            is_directory=data.get("type") == "DIRECTORY"
        )
    
    def _parse_task(self, data: Dict[str, Any]) -> Task:
        """Parse task data from API response."""
        try:
            status = TaskStatus(data.get("status", "PENDING"))
        except ValueError:
            status = TaskStatus.PENDING
        
        return Task(
            uuid=data.get("uuid", ""),
            name=data.get("name", ""),
            status=status,
            task_type=data.get("taskType"),
            progress=data.get("progress", 0),
            created=self._parse_timestamp(data.get("created")),
            modified=self._parse_timestamp(data.get("modified")),
            started=self._parse_timestamp(data.get("started")),
            ended=self._parse_timestamp(data.get("ended")),
            exit_value=data.get("exitValue"),
            params_map=data.get("paramsMap", {}),
            parameters=data.get("parameters", {}),
            error_message=data.get("errorMessage"),
            sub_tasks=[self._parse_task(st) for st in data.get("subTasks", [])],
            hidden=data.get("hidden", False),
            extended_info=data.get("extendedInfo", {})
        )
    
    def _parse_objective(self, data: Dict[str, Any]) -> Objective:
        """Parse objective data from API response."""
        try:
            objective_type = ObjectiveType(data.get("objectiveType", "BACKUP"))
        except ValueError:
            objective_type = ObjectiveType.BACKUP
            
        try:
            state = ObjectiveState(data.get("objectiveState", "ACTIVE"))
        except ValueError:
            state = ObjectiveState.ACTIVE
        
        return Objective(
            uuid=data.get("uoid", {}).get("uuid", ""),
            name=data.get("name", ""),
            objective_type=objective_type,
            state=state,
            description=data.get("description", ""),
            source_path=data.get("sourcePath", ""),
            destination_path=data.get("destinationPath", ""),
            source_share_uuid=data.get("sourceShareUuid"),
            destination_share_uuid=data.get("destinationShareUuid"),
            source_volume_uuid=data.get("sourceVolumeUuid"),
            destination_volume_uuid=data.get("destinationVolumeUuid"),
            created=self._parse_timestamp(data.get("created")),
            modified=self._parse_timestamp(data.get("modified")),
            parameters=data.get("parameters", {}),
            schedule=data.get("schedule", {}),
            extended_info=data.get("extendedInfo", {})
        )
    
    def _parse_data_movement_job(self, data: Dict[str, Any]) -> DataMovementJob:
        """Parse data movement job data from API response."""
        try:
            movement_type = DataMovementType(data.get("movementType", "FILE_COPY"))
        except ValueError:
            movement_type = DataMovementType.FILE_COPY
            
        try:
            status = TaskStatus(data.get("status", "PENDING"))
        except ValueError:
            status = TaskStatus.PENDING
        
        return DataMovementJob(
            uuid=data.get("uoid", {}).get("uuid", ""),
            name=data.get("name", ""),
            movement_type=movement_type,
            status=status,
            source_path=data.get("sourcePath", ""),
            destination_path=data.get("destinationPath", ""),
            source_share_uuid=data.get("sourceShareUuid"),
            destination_share_uuid=data.get("destinationShareUuid"),
            source_volume_uuid=data.get("sourceVolumeUuid"),
            destination_volume_uuid=data.get("destinationVolumeUuid"),
            file_count=data.get("fileCount"),
            total_size_bytes=data.get("totalSizeBytes"),
            progress=data.get("progress", 0),
            created=self._parse_timestamp(data.get("created")),
            modified=self._parse_timestamp(data.get("modified")),
            started=self._parse_timestamp(data.get("started")),
            completed=self._parse_timestamp(data.get("completed")),
            error_message=data.get("errorMessage"),
            parameters=data.get("parameters", {}),
            extended_info=data.get("extendedInfo", {})
        )
    
    def _parse_timestamp(self, timestamp: Optional[str]) -> Optional[str]:
        """Parse timestamp from API response."""
        if not timestamp:
            return None
        # For now, return as string. Could be converted to datetime if needed
        # TODO: Convert to datetime object when needed
        return timestamp


# Convenience function for creating client
def create_hammerspace_client(config: Optional[HammerspaceConfig] = None) -> HammerspaceClient:
    """Create a new Hammerspace client instance."""
    return HammerspaceClient(config) 