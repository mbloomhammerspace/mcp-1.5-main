"""
Data models for Hammerspace DataSphere API.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class NodeType(Enum):
    """Storage node types."""
    STORAGE = "storage"
    OBJECT = "object"
    HYBRID = "hybrid"
    GENERIC_S3 = "GENERIC_S3"


class VolumeState(Enum):
    """Storage volume states."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    FAILED = "failed"
    OK = "OK"


class TaskStatus(Enum):
    """Task status values."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ObjectiveType(Enum):
    """Objective types for data movement."""
    REPLICATION = "replication"
    MIGRATION = "migration"
    COPY = "copy"
    MOVE = "move"
    SYNC = "sync"
    BACKUP = "backup"
    ARCHIVE = "archive"


class ObjectiveState(Enum):
    """Objective states."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"


class DataMovementType(Enum):
    """Data movement operation types."""
    FILE_COPY = "file_copy"
    FILE_MOVE = "file_move"
    DIRECTORY_COPY = "directory_copy"
    DIRECTORY_MOVE = "directory_move"
    SHARE_REPLICATION = "share_replication"
    VOLUME_MIGRATION = "volume_migration"
    BULK_OPERATION = "bulk_operation"


class ReplicationStatus(Enum):
    """File replication status."""
    NOT_REPLICATED = "not_replicated"
    REPLICATED = "replicated"
    REPLICATING = "replicating"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class Node:
    """Storage node information."""
    uuid: str
    name: str
    node_type: NodeType
    state: str
    endpoint: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    platform_services: Optional[List[str]] = None
    extended_info: Optional[Dict[str, Any]] = None


@dataclass
class StorageVolume:
    """Storage volume information."""
    uuid: str
    name: str
    volume_type: str
    state: VolumeState
    node_uuid: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    size_bytes: Optional[int] = None
    used_bytes: Optional[int] = None
    extended_info: Optional[Dict[str, Any]] = None


@dataclass
class ObjectStorageVolume:
    """Object storage volume information."""
    uuid: str
    name: str
    object_store_logical_volume: Optional[Dict[str, Any]] = None
    storage_volume_state: VolumeState = VolumeState.OK
    created: Optional[str] = None
    modified: Optional[str] = None
    extended_info: Optional[Dict[str, Any]] = None


@dataclass
class Share:
    """Share information."""
    uuid: str
    name: str
    path: str
    created: Optional[str] = None
    modified: Optional[str] = None
    smb_aliases: Optional[List[str]] = None
    active_objectives: Optional[List[Dict[str, Any]]] = None
    applied_objectives: Optional[List[Dict[str, Any]]] = None
    total_number_of_files: Optional[int] = None
    extended_info: Optional[Dict[str, Any]] = None


@dataclass
class File:
    """File information."""
    uuid: str
    path: str
    name: str
    size_bytes: Optional[int] = None
    share_uuid: Optional[str] = None
    volume_uuid: Optional[str] = None
    node_uuid: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    is_directory: Optional[bool] = None
    replication_status: Optional[ReplicationStatus] = None
    extended_info: Optional[Dict[str, Any]] = None


@dataclass
class Task:
    """Task information."""
    uuid: str
    name: str
    status: TaskStatus
    task_type: Optional[str] = None
    progress: int = 0
    created: Optional[str] = None
    modified: Optional[str] = None
    started: Optional[str] = None
    ended: Optional[str] = None
    exit_value: Optional[int] = None
    params_map: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    sub_tasks: Optional[List['Task']] = None
    hidden: bool = False
    extended_info: Optional[Dict[str, Any]] = None


@dataclass
class Objective:
    """Objective information for data movement."""
    uuid: str
    name: str
    objective_type: ObjectiveType
    state: ObjectiveState
    description: Optional[str] = None
    source_path: Optional[str] = None
    destination_path: Optional[str] = None
    source_share_uuid: Optional[str] = None
    destination_share_uuid: Optional[str] = None
    source_volume_uuid: Optional[str] = None
    destination_volume_uuid: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    schedule: Optional[Dict[str, Any]] = None
    extended_info: Optional[Dict[str, Any]] = None


@dataclass
class DataMovementJob:
    """Data movement job information."""
    uuid: str
    name: str
    movement_type: DataMovementType
    status: TaskStatus
    source_path: str
    destination_path: str
    source_share_uuid: Optional[str] = None
    destination_share_uuid: Optional[str] = None
    source_volume_uuid: Optional[str] = None
    destination_volume_uuid: Optional[str] = None
    file_count: Optional[int] = None
    total_size_bytes: Optional[int] = None
    progress: int = 0
    created: Optional[str] = None
    modified: Optional[str] = None
    started: Optional[str] = None
    completed: Optional[str] = None
    error_message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    extended_info: Optional[Dict[str, Any]] = None


@dataclass
class DataMovementRequest:
    """Request for data movement operation."""
    movement_type: DataMovementType
    source_path: str
    destination_path: str
    source_share_uuid: Optional[str] = None
    destination_share_uuid: Optional[str] = None
    source_volume_uuid: Optional[str] = None
    destination_volume_uuid: Optional[str] = None
    overwrite: bool = False
    preserve_metadata: bool = True
    verify_checksum: bool = True
    priority: int = 5
    schedule: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class ObjectiveTemplate:
    """Template for creating objectives."""
    name: str
    objective_type: ObjectiveType
    description: str
    source_pattern: str
    destination_pattern: str
    parameters: Dict[str, Any]
    examples: List[str]
    schedule: Optional[Dict[str, Any]] = None 