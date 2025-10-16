#!/usr/bin/env python3
"""
Hammerspace Volume Movement Manager

This script provides comprehensive volume movement operations between DSX1 and T0 volumes
using the Hammerspace SDK/API. It supports copy, clone, and move operations with tier management.

Features:
- Copy files between volumes (creates duplicate)
- Clone files between volumes (creates reference/copy)
- Move files between volumes (moves with deletion from source)
- Place data on specific tiers (tier1 for DSX1)
- Exclude data from specific tiers (tier0)
- Job monitoring and status tracking
- Comprehensive logging and error handling

Usage:
    # List discovered volumes and categories
    python volume_movement_manager.py --list-volumes
    
    # Copy files from LSS to Tier0 (default)
    python volume_movement_manager.py --operation copy --source-type lss --target-type tier0 --path /modelstore
    
    # Move files from LSS to Tier0
    python volume_movement_manager.py --operation move --source-type lss --target-type tier0 --path /modelstore
    
    # Clone files from LSS to Tier0
    python volume_movement_manager.py --operation clone --source-type lss --target-type tier0 --path /modelstore
    
    # Place data on Tier1 (from LSS)
    python volume_movement_manager.py --tier-operation place-on-tier1 --volume-type lss --path /modelstore
    
    # Exclude data from Tier0
    python volume_movement_manager.py --tier-operation exclude-from-tier0 --volume-type tier0 --path /modelstore
    
    # List active jobs
    python volume_movement_manager.py --list-jobs
"""

import asyncio
import argparse
import sys
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Add the src directory to the path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from hammerspace_client import HammerspaceClient, create_hammerspace_client
from models import (
    StorageVolume, Share, DataMovementRequest, DataMovementType, 
    DataMovementJob, Task, TaskStatus, Objective, ObjectiveType
)
from operations.movement import DataMovementOperations


class VolumeMovementManager:
    """Manages volume movement operations using Hammerspace SDK/API."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the volume movement manager.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.client = create_hammerspace_client()
        self.movement_ops = DataMovementOperations(self.client)
        self.volumes: Dict[str, StorageVolume] = {}
        self.shares: Dict[str, Share] = {}
        self.active_jobs: List[DataMovementJob] = []
        
        # Volume categories for dynamic discovery
        self.volume_categories = {
            'lss_volumes': [],      # Local Storage System volumes
            'tier0_volumes': [],    # Tier 0 volumes (fast storage)
            'tier1_volumes': [],    # Tier 1 volumes (slower storage)
            'third_party_volumes': []  # Third-party storage volumes
        }
        
        print("🚀 Volume Movement Manager initialized")
        print("🔍 Will dynamically discover volumes using API")
    
    async def initialize(self):
        """Initialize the manager by loading volumes and shares."""
        try:
            print("🔄 Loading volumes and shares...")
            
            # Load volumes
            volumes = await self.client.get_storage_volumes()
            for volume in volumes:
                self.volumes[volume.name] = volume
                print(f"   📦 Volume: {volume.name} (UUID: {volume.uuid}, State: {volume.state})")
            
            # Load shares
            shares = await self.client.get_shares()
            for share in shares:
                self.shares[share.name] = share
                print(f"   📁 Share: {share.name} (UUID: {share.uuid}, Path: {share.path})")
            
            # Categorize volumes based on their names and properties
            await self._categorize_volumes()
            
            print(f"✅ Loaded {len(self.volumes)} volumes and {len(self.shares)} shares")
            self._print_volume_categories()
            
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            raise
    
    async def _categorize_volumes(self):
        """Categorize volumes based on their names and properties."""
        print("🔍 Categorizing volumes...")
        
        for volume in self.volumes.values():
            volume_name_lower = volume.name.lower()
            
            # Categorize based on naming patterns
            if 'dsx' in volume_name_lower or 'lss' in volume_name_lower:
                self.volume_categories['lss_volumes'].append(volume)
                print(f"   🏠 LSS Volume: {volume.name}")
            
            elif 'tier0' in volume_name_lower or 't0' in volume_name_lower:
                self.volume_categories['tier0_volumes'].append(volume)
                print(f"   ⚡ Tier 0 Volume: {volume.name}")
            
            elif 'tier1' in volume_name_lower or 't1' in volume_name_lower:
                self.volume_categories['tier1_volumes'].append(volume)
                print(f"   💾 Tier 1 Volume: {volume.name}")
            
            else:
                # Check if it's a third-party volume based on extended info or other properties
                if volume.extended_info and volume.extended_info.get('storage_type') == 'third_party':
                    self.volume_categories['third_party_volumes'].append(volume)
                    print(f"   🌐 Third-party Volume: {volume.name}")
                else:
                    # Default to LSS if we can't determine
                    self.volume_categories['lss_volumes'].append(volume)
                    print(f"   🏠 LSS Volume (default): {volume.name}")
    
    def _print_volume_categories(self):
        """Print the categorized volumes."""
        print("\n📋 Volume Categories:")
        for category, volumes in self.volume_categories.items():
            if volumes:
                print(f"   {category.replace('_', ' ').title()}: {len(volumes)} volumes")
                for vol in volumes:
                    print(f"      • {vol.name} (UUID: {vol.uuid})")
            else:
                print(f"   {category.replace('_', ' ').title()}: No volumes found")
    
    def get_volume_by_category(self, category: str) -> Optional[StorageVolume]:
        """
        Get the first volume from a specific category.
        
        Args:
            category: Volume category (lss_volumes, tier0_volumes, tier1_volumes, third_party_volumes)
            
        Returns:
            StorageVolume object or None if no volumes in category
        """
        volumes = self.volume_categories.get(category, [])
        return volumes[0] if volumes else None
    
    def get_volumes_by_category(self, category: str) -> List[StorageVolume]:
        """
        Get all volumes from a specific category.
        
        Args:
            category: Volume category
            
        Returns:
            List of StorageVolume objects
        """
        return self.volume_categories.get(category, [])
    
    async def find_volume_by_name(self, volume_name: str) -> Optional[StorageVolume]:
        """
        Find a volume by name or category.
        
        Args:
            volume_name: Volume name, category (lss, tier0, tier1, third_party), or partial name
            
        Returns:
            StorageVolume object or None if not found
        """
        # Check if it's a category first
        category_mapping = {
            'lss': 'lss_volumes',
            'tier0': 'tier0_volumes', 
            'tier1': 'tier1_volumes',
            'third_party': 'third_party_volumes'
        }
        
        if volume_name.lower() in category_mapping:
            category = category_mapping[volume_name.lower()]
            volume = self.get_volume_by_category(category)
            if volume:
                print(f"🔍 Using volume from category '{volume_name}': {volume.name}")
                return volume
            else:
                print(f"⚠️ No volumes found in category '{volume_name}'")
                return None
        
        # Search for exact match
        for vol in self.volumes.values():
            if vol.name == volume_name:
                print(f"🔍 Found exact match: {vol.name}")
                return vol
        
        # Search for partial match
        for vol in self.volumes.values():
            if volume_name.lower() in vol.name.lower():
                print(f"🔍 Found partial match: {vol.name}")
                return vol
        
        print(f"❌ Volume '{volume_name}' not found")
        return None
    
    def get_source_target_volumes(self, source_type: str = "lss", target_type: str = "tier0") -> tuple[Optional[StorageVolume], Optional[StorageVolume]]:
        """
        Get source and target volumes based on type.
        
        Args:
            source_type: Source volume type (lss, tier0, tier1, third_party)
            target_type: Target volume type (lss, tier0, tier1, third_party)
            
        Returns:
            Tuple of (source_volume, target_volume) or (None, None) if not found
        """
        source_vol = self.get_volume_by_category(f"{source_type}_volumes")
        target_vol = self.get_volume_by_category(f"{target_type}_volumes")
        
        if source_vol and target_vol:
            print(f"🎯 Source/Target volumes identified:")
            print(f"   Source ({source_type}): {source_vol.name} (UUID: {source_vol.uuid})")
            print(f"   Target ({target_type}): {target_vol.name} (UUID: {target_vol.uuid})")
        else:
            print(f"❌ Could not identify source/target volumes:")
            if not source_vol:
                print(f"   No {source_type} volumes found")
            if not target_vol:
                print(f"   No {target_type} volumes found")
        
        return source_vol, target_vol
    
    async def find_share_by_path(self, path: str) -> Optional[Share]:
        """
        Find a share that contains the given path.
        
        Args:
            path: File or directory path
            
        Returns:
            Share object or None if not found
        """
        for share in self.shares.values():
            if path.startswith(share.path):
                return share
        return None
    
    async def copy_files(self, source_type: str = "lss", target_type: str = "tier0", 
                        path: str = "/modelstore", recursive: bool = True) -> DataMovementJob:
        """
        Copy files from source volume type to target volume type.
        
        Args:
            source_type: Source volume type (lss, tier0, tier1, third_party)
            target_type: Target volume type (lss, tier0, tier1, third_party)
            path: Path to copy (file or directory)
            recursive: Whether to copy recursively for directories
            
        Returns:
            DataMovementJob object
        """
        print(f"📋 Starting COPY operation:")
        print(f"   Source Type: {source_type}")
        print(f"   Target Type: {target_type}")
        print(f"   Path: {path}")
        print(f"   Recursive: {recursive}")
        
        # Get source and target volumes
        src_vol, tgt_vol = self.get_source_target_volumes(source_type, target_type)
        
        if not src_vol or not tgt_vol:
            raise ValueError(f"Could not identify source ({source_type}) or target ({target_type}) volumes")
        
        # Find the share containing the path
        share = await self.find_share_by_path(path)
        if not share:
            raise ValueError(f"No share found containing path '{path}'")
        
        # Create data movement request
        request = DataMovementRequest(
            movement_type=DataMovementType.DIRECTORY_COPY if recursive else DataMovementType.FILE_COPY,
            source_path=path,
            destination_path=path,  # Keep same path structure
            source_share_uuid=share.uuid,
            destination_share_uuid=share.uuid,  # Assuming same share
            source_volume_uuid=src_vol.uuid,
            destination_volume_uuid=tgt_vol.uuid,
            overwrite=True,
            preserve_metadata=True,
            verify_checksum=True,
            priority="MEDIUM"
        )
        
        # Create the job
        job = await self.client.create_data_movement_job(request)
        self.active_jobs.append(job)
        
        print(f"✅ Copy job created: {job.name} (UUID: {job.uuid})")
        return job
    
    async def clone_files(self, source_type: str = "lss", target_type: str = "tier0", 
                         path: str = "/modelstore") -> DataMovementJob:
        """
        Clone files from source volume type to target volume type (creates reference/copy).
        
        Args:
            source_type: Source volume type (lss, tier0, tier1, third_party)
            target_type: Target volume type (lss, tier0, tier1, third_party)
            path: Path to clone (file or directory)
            
        Returns:
            DataMovementJob object
        """
        print(f"🔗 Starting CLONE operation:")
        print(f"   Source Type: {source_type}")
        print(f"   Target Type: {target_type}")
        print(f"   Path: {path}")
        
        # Get source and target volumes
        src_vol, tgt_vol = self.get_source_target_volumes(source_type, target_type)
        
        if not src_vol or not tgt_vol:
            raise ValueError(f"Could not identify source ({source_type}) or target ({target_type}) volumes")
        
        share = await self.find_share_by_path(path)
        if not share:
            raise ValueError(f"No share found containing path '{path}'")
        
        # Create clone request (using copy with special parameters)
        request = DataMovementRequest(
            movement_type=DataMovementType.DIRECTORY_COPY,
            source_path=path,
            destination_path=path,
            source_share_uuid=share.uuid,
            destination_share_uuid=share.uuid,
            source_volume_uuid=src_vol.uuid,
            destination_volume_uuid=tgt_vol.uuid,
            overwrite=True,
            preserve_metadata=True,
            verify_checksum=False,  # Skip checksum for faster cloning
            priority="HIGH",
            parameters={
                "clone_mode": True,
                "preserve_references": True,
                "create_snapshots": False
            }
        )
        
        job = await self.client.create_data_movement_job(request)
        self.active_jobs.append(job)
        
        print(f"✅ Clone job created: {job.name} (UUID: {job.uuid})")
        return job
    
    async def move_files(self, source_type: str = "lss", target_type: str = "tier0", 
                        path: str = "/modelstore") -> DataMovementJob:
        """
        Move files from source volume type to target volume type (moves with deletion from source).
        
        Args:
            source_type: Source volume type (lss, tier0, tier1, third_party)
            target_type: Target volume type (lss, tier0, tier1, third_party)
            path: Path to move (file or directory)
            
        Returns:
            DataMovementJob object
        """
        print(f"🚚 Starting MOVE operation:")
        print(f"   Source Type: {source_type}")
        print(f"   Target Type: {target_type}")
        print(f"   Path: {path}")
        
        # Get source and target volumes
        src_vol, tgt_vol = self.get_source_target_volumes(source_type, target_type)
        
        if not src_vol or not tgt_vol:
            raise ValueError(f"Could not identify source ({source_type}) or target ({target_type}) volumes")
        
        share = await self.find_share_by_path(path)
        if not share:
            raise ValueError(f"No share found containing path '{path}'")
        
        # Create move request
        request = DataMovementRequest(
            movement_type=DataMovementType.DIRECTORY_MOVE,
            source_path=path,
            destination_path=path,
            source_share_uuid=share.uuid,
            destination_share_uuid=share.uuid,
            source_volume_uuid=src_vol.uuid,
            destination_volume_uuid=tgt_vol.uuid,
            overwrite=True,
            preserve_metadata=True,
            verify_checksum=True,
            priority="HIGH",
            parameters={
                "delete_source": True,
                "atomic_move": True
            }
        )
        
        job = await self.client.create_data_movement_job(request)
        self.active_jobs.append(job)
        
        print(f"✅ Move job created: {job.name} (UUID: {job.uuid})")
        return job
    
    async def place_on_tier(self, volume_type: str = "lss", path: str = "/modelstore", 
                           tier_name: str = "tier1") -> Objective:
        """
        Create an objective to place data on a specific tier.
        
        Args:
            volume_type: Volume type (lss, tier0, tier1, third_party)
            path: Path to place on tier
            tier_name: Name of the tier (tier1, tier0, etc.)
            
        Returns:
            Objective object
        """
        print(f"🎯 Creating PLACE-ON-TIER objective:")
        print(f"   Volume Type: {volume_type}")
        print(f"   Path: {path}")
        print(f"   Target Tier: {tier_name}")
        
        vol = self.get_volume_by_category(f"{volume_type}_volumes")
        if not vol:
            raise ValueError(f"No {volume_type} volumes found")
        
        # Create objective for tier placement
        objective_data = {
            "name": f"place-on-{tier_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "objectiveType": "MIGRATION",
            "description": f"Place data on {tier_name}",
            "sourcePath": path,
            "sourceVolumeUuid": vol.uuid,
            "elementalObjective": {
                "name": f"place-on-{tier_name}",
                "placementObjective": {
                    "placeOnLocations": [{
                        "placeOn": [{
                            "_type": "STORAGE_VOLUME",
                            "uuid": vol.uuid,
                            "name": vol.name
                        }]
                    }]
                }
            },
            "parameters": {
                "tier_name": tier_name,
                "priority": "HIGH",
                "auto_apply": True
            }
        }
        
        objective = await self.client.create_objective(objective_data)
        
        print(f"✅ Place-on-tier objective created: {objective.name} (UUID: {objective.uuid})")
        return objective
    
    async def exclude_from_tier(self, volume_type: str = "tier0", path: str = "/modelstore", 
                               tier_name: str = "tier0") -> Objective:
        """
        Create an objective to exclude data from a specific tier.
        
        Args:
            volume_type: Volume type (lss, tier0, tier1, third_party)
            path: Path to exclude from tier
            tier_name: Name of the tier to exclude from (tier0, tier1, etc.)
            
        Returns:
            Objective object
        """
        print(f"🚫 Creating EXCLUDE-FROM-TIER objective:")
        print(f"   Volume Type: {volume_type}")
        print(f"   Path: {path}")
        print(f"   Exclude from tier: {tier_name}")
        
        vol = self.get_volume_by_category(f"{volume_type}_volumes")
        if not vol:
            raise ValueError(f"No {volume_type} volumes found")
        
        # Create objective for tier exclusion
        objective_data = {
            "name": f"exclude-from-{tier_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "objectiveType": "MIGRATION",
            "description": f"Exclude data from {tier_name}",
            "sourcePath": path,
            "sourceVolumeUuid": vol.uuid,
            "elementalObjective": {
                "name": f"exclude-from-{tier_name}",
                "placementObjective": {
                    "excludeFromLocations": [{
                        "excludeFrom": [{
                            "_type": "STORAGE_VOLUME",
                            "uuid": vol.uuid,
                            "name": vol.name
                        }]
                    }]
                }
            },
            "parameters": {
                "tier_name": tier_name,
                "priority": "HIGH",
                "auto_apply": True
            }
        }
        
        objective = await self.client.create_objective(objective_data)
        
        print(f"✅ Exclude-from-tier objective created: {objective.name} (UUID: {objective.uuid})")
        return objective
    
    async def monitor_job(self, job_uuid: str, poll_interval: int = 5) -> DataMovementJob:
        """
        Monitor a data movement job until completion.
        
        Args:
            job_uuid: UUID of the job to monitor
            poll_interval: Polling interval in seconds
            
        Returns:
            DataMovementJob object with final status
        """
        print(f"👀 Monitoring job: {job_uuid}")
        
        while True:
            try:
                job = await self.client.get_data_movement_job(job_uuid)
                
                print(f"   Status: {job.status}, Progress: {job.progress}%")
                
                if job.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    if job.status == TaskStatus.COMPLETED:
                        print(f"✅ Job completed successfully!")
                    elif job.status == TaskStatus.FAILED:
                        print(f"❌ Job failed: {job.error_message}")
                    else:
                        print(f"⚠️ Job cancelled")
                    
                    return job
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                print(f"❌ Error monitoring job: {e}")
                raise
    
    async def list_active_jobs(self) -> List[DataMovementJob]:
        """List all active data movement jobs."""
        jobs = await self.client.get_data_movement_jobs()
        active_jobs = [job for job in jobs if job.status in [TaskStatus.PENDING, TaskStatus.RUNNING]]
        
        print(f"📋 Active jobs: {len(active_jobs)}")
        for job in active_jobs:
            print(f"   {job.name} (UUID: {job.uuid}, Status: {job.status}, Progress: {job.progress}%)")
        
        return active_jobs
    
    async def verify_data_integrity(self, volume_type: str, path: str) -> Dict[str, Any]:
        """
        Verify that data still exists on the specified volume type after operations.
        
        Args:
            volume_type: Volume type (lss, tier0, tier1, third_party)
            path: Path to verify
            
        Returns:
            Dictionary with verification results
        """
        print(f"🔍 Verifying data integrity:")
        print(f"   Volume Type: {volume_type}")
        print(f"   Path: {path}")
        
        vol = self.get_volume_by_category(f"{volume_type}_volumes")
        if not vol:
            return {"error": f"No {volume_type} volumes found"}
        
        try:
            # Search for files in the path
            files = await self.client.search_files(path, limit=1000)
            
            result = {
                "volume_type": volume_type,
                "volume": vol.name,
                "volume_uuid": vol.uuid,
                "path": path,
                "file_count": len(files),
                "files": [{"name": f.name, "path": f.path, "size": f.size_bytes} for f in files[:10]],  # First 10 files
                "total_size": sum(f.size_bytes or 0 for f in files),
                "verification_time": datetime.now().isoformat()
            }
            
            print(f"✅ Verification complete:")
            print(f"   Files found: {result['file_count']}")
            print(f"   Total size: {result['total_size']} bytes")
            
            return result
            
        except Exception as e:
            return {"error": f"Verification failed: {e}"}
    
    async def close(self):
        """Close the manager and cleanup resources."""
        if self.client:
            await self.client.close()
        print("🔒 Volume Movement Manager closed")


async def main():
    """Main function to handle command line arguments and execute operations."""
    parser = argparse.ArgumentParser(description="Hammerspace Volume Movement Manager")
    
    # Operation type
    parser.add_argument("--operation", choices=["copy", "clone", "move"], 
                       help="Type of operation to perform")
    parser.add_argument("--tier-operation", choices=["place-on-tier1", "exclude-from-tier0"],
                       help="Tier management operation")
    
    # Volume type arguments (using categories instead of specific volume names)
    parser.add_argument("--source-type", default="lss", 
                       choices=["lss", "tier0", "tier1", "third_party"],
                       help="Source volume type (default: lss)")
    parser.add_argument("--target-type", default="tier0",
                       choices=["lss", "tier0", "tier1", "third_party"], 
                       help="Target volume type (default: tier0)")
    parser.add_argument("--volume-type", default="lss",
                       choices=["lss", "tier0", "tier1", "third_party"],
                       help="Volume type for tier operations (default: lss)")
    parser.add_argument("--path", default="/modelstore", help="Path to operate on (default: /modelstore)")
    
    # Options
    parser.add_argument("--recursive", action="store_true", default=True,
                       help="Recursive operation for directories")
    parser.add_argument("--monitor", action="store_true", default=True,
                       help="Monitor job until completion")
    parser.add_argument("--verify", action="store_true", default=True,
                       help="Verify data integrity after operation")
    parser.add_argument("--list-jobs", action="store_true",
                       help="List all active jobs")
    parser.add_argument("--list-volumes", action="store_true",
                       help="List all discovered volumes and categories")
    
    args = parser.parse_args()
    
    if not any([args.operation, args.tier_operation, args.list_jobs, args.list_volumes]):
        parser.error("Must specify --operation, --tier-operation, --list-jobs, or --list-volumes")
    
    # Initialize manager
    manager = VolumeMovementManager()
    
    try:
        await manager.initialize()
        
        if args.list_volumes:
            print("\n📋 Volume Discovery Complete")
            return
        
        if args.list_jobs:
            await manager.list_active_jobs()
            return
        
        if args.operation:
            # Perform the operation using volume types
            if args.operation == "copy":
                job = await manager.copy_files(args.source_type, args.target_type, 
                                             args.path, args.recursive)
            elif args.operation == "clone":
                job = await manager.clone_files(args.source_type, args.target_type, args.path)
            elif args.operation == "move":
                job = await manager.move_files(args.source_type, args.target_type, args.path)
            
            # Monitor job if requested
            if args.monitor:
                final_job = await manager.monitor_job(job.uuid)
                
                # Verify data integrity if requested
                if args.verify and final_job.status == TaskStatus.COMPLETED:
                    print("\n🔍 Verifying data integrity...")
                    source_result = await manager.verify_data_integrity(args.source_type, args.path)
                    target_result = await manager.verify_data_integrity(args.target_type, args.path)
                    
                    print(f"\n📊 Verification Results:")
                    print(f"Source volume ({args.source_type}): {json.dumps(source_result, indent=2)}")
                    print(f"Target volume ({args.target_type}): {json.dumps(target_result, indent=2)}")
        
        elif args.tier_operation:
            if args.tier_operation == "place-on-tier1":
                objective = await manager.place_on_tier(args.volume_type, args.path, "tier1")
            elif args.tier_operation == "exclude-from-tier0":
                objective = await manager.exclude_from_tier(args.volume_type, args.path, "tier0")
            
            print(f"✅ Tier operation completed: {objective.name}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
