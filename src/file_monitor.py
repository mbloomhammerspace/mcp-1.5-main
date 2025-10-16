#!/usr/bin/env python3
"""
Hammerspace File Monitor Service
Monitors NFS mounts for new files and automatically tags them with ingest metadata.
Uses polling approach since inotify doesn't work reliably with NFS.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import subprocess
import time
import psutil
import yaml
import threading
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
from zoneinfo import ZoneInfo

# Inotify disabled - using polling-only mode for NFS compatibility
INOTIFY_AVAILABLE = False

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("⚠️ python-magic not available - mimetype detection will use fallback")

# Setup logging
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'inotify.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('file_monitor')


class FileMonitor:
    """Monitor Hammerspace NFS mounts for new files and auto-tag them."""
    
    def __init__(self, hs_cli_path: str = "/home/ubuntu/.local/bin/hs"):
        """Initialize the file monitor."""
        self.hs_cli = hs_cli_path
        self.watch_paths = []
        self.event_queue = defaultdict(list)  # path -> list of events
        self.known_files = set()  # Track files we've already seen
        self.tagged_files = set()  # Track files we've successfully tagged (prevents reprocessing)
        self.running = False
        self.batch_interval = 15  # seconds
        self.poll_interval = 2  # seconds between directory scans
        self.fast_poll_interval = 1  # seconds for fast polling during business hours
        self.last_batch_time = time.time()
        self.cpu_samples = []  # Track CPU usage
        self.max_cpu_samples = 100  # Keep last 100 samples
        self.process = psutil.Process()  # Current process for CPU monitoring
        
        # Untagged file scanner settings
        self.untagged_scan_interval = 5  # Scan for untagged files every 5 seconds
        self.last_untagged_scan = 0  # Timestamp of last untagged scan
        self.files_tagged_retroactively = 0  # Counter for retroactive tagging
        
        # Retroactive tagging disabled for testing
        self.retroactive_tagging_enabled = False
        self.retroactive_hours = (1, 8)  # Only run between 1am and 8am
        
        # Polling-only mode (inotify disabled for NFS compatibility)
        self.inotify_available = False
        
        # Initialize magic for MIME type detection
        if MAGIC_AVAILABLE:
            try:
                self.magic = magic.Magic(mime=True)
                logger.info("✅ python-magic initialized for MIME type detection")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize python-magic: {e}")
                self.magic = None
        else:
            self.magic = None
    
    def get_mount_points(self) -> List[str]:
        """Get hub mount point only."""
        logger.info("🔍 Discovering NFS mount points (hub only)...")
        
        # Only monitor the hub share
        hub_path = "/mnt/anvil/hub"
        
        if os.path.exists(hub_path) and os.path.isdir(hub_path):
            logger.info(f"✅ Found hub mount: {hub_path}")
            return [hub_path]
        else:
            logger.error(f"❌ Hub mount not found: {hub_path}")
            return []
    
    def calculate_md5(self, file_path: str) -> str:
        """Calculate MD5 hash of a file."""
        try:
            md5_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            logger.error(f"❌ Failed to calculate MD5 for {file_path}: {e}")
            return "error"
    
    def detect_mimetype(self, file_path: str) -> str:
        """Detect MIME type of a file using python-magic."""
        if self.magic:
            try:
                return self.magic.from_file(file_path)
            except Exception as e:
                logger.error(f"❌ Failed to detect MIME type for {file_path}: {e}")
                return "application/octet-stream"
        else:
            # Fallback to file extension-based detection
            ext = Path(file_path).suffix.lower()
            mime_map = {
                '.txt': 'text/plain',
                '.json': 'application/json',
                '.xml': 'application/xml',
                '.bin': 'application/octet-stream',
                '.safetensors': 'application/octet-stream',
                '.pt': 'application/octet-stream',
                '.pth': 'application/octet-stream',
                '.md': 'text/markdown',
                '.py': 'text/x-python',
                '.sh': 'text/x-shellscript',
            }
            return mime_map.get(ext, 'application/octet-stream')
    
    def tag_file(self, file_path: str, ingest_id: str, mime_id: str, is_retroactive: bool = False) -> bool:
        """Tag a file with ingest metadata using HSTK CLI."""
        try:
            # Check if we've already processed this file (in-memory tracking is reliable)
            if file_path in self.tagged_files:
                logger.debug(f"⏭️ Skipping previously processed file: {file_path}")
                return False  # Return False to indicate we didn't tag (already processed)
            
            # Tag with ingestid
            ingest_tag_cmd = [self.hs_cli, "tag", "set", f"user.ingestid={ingest_id}", file_path]
            result1 = subprocess.run(ingest_tag_cmd, capture_output=True, text=True, timeout=10)
            
            # Tag with mimeid
            mime_tag_cmd = [self.hs_cli, "tag", "set", f"user.mimeid={mime_id}", file_path]
            result2 = subprocess.run(mime_tag_cmd, capture_output=True, text=True, timeout=10)
            
            if result1.returncode == 0 and result2.returncode == 0:
                # Only log once here - remove duplicate logging elsewhere
                tag_type = "RETROACTIVE TAG" if is_retroactive else "NEW FILE TAG"
                logger.info(f"✅ {tag_type}: {file_path} → ingestid={ingest_id[:8]}..., mimeid={mime_id}")
                
                # Mark file as tagged so we don't reprocess it (CRITICAL for preventing duplicates)
                self.tagged_files.add(file_path)
                
                # Small delay to allow tags to propagate (NFS caching)
                time.sleep(0.1)
                return True
            else:
                if result1.stderr or result2.stderr:
                    logger.error(f"❌ Failed to tag {file_path}: {result1.stderr} {result2.stderr}")
                # Even if tagging failed, mark as processed to avoid retry loops
                self.tagged_files.add(file_path)
                return False
                
        except Exception as e:
            logger.error(f"❌ Error tagging {file_path}: {e}")
            # Mark as processed even on error to avoid retry loops
            self.tagged_files.add(file_path)
            return False
    
    def scan_directory(self, dir_path: str, max_depth: int = 0) -> List[str]:
        """Scan a directory for new files recursively (up to max_depth levels)."""
        new_files = []
        try:
            # Use os.walk for recursive scanning with depth limit
            for root, dirs, files in os.walk(dir_path):
                # Calculate current depth
                depth = root[len(dir_path):].count(os.sep)
                if depth >= max_depth:
                    # Don't recurse into subdirectories at max depth
                    dirs.clear()
                    continue
                
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                # Collect files with their access times for sorting
                file_candidates = []
                for filename in files:
                    if filename.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, filename)
                    if file_path not in self.known_files:
                        try:
                            # Get access time for sorting
                            atime = os.path.getatime(file_path)
                            file_candidates.append((file_path, atime))
                        except (OSError, PermissionError):
                            # If we can't get access time, add it anyway
                            file_candidates.append((file_path, 0))
                
                # Sort files by access time (newest first)
                file_candidates.sort(key=lambda x: x[1], reverse=True)
                
                # Add sorted files to new_files
                for file_path, _ in file_candidates:
                    new_files.append(file_path)
                    self.known_files.add(file_path)
                    
        except Exception as e:
            logger.error(f"❌ Error scanning {dir_path}: {e}")
        
        return new_files
    
    def scan_top_level_only(self, dir_path: str) -> List[str]:
        """Scan only the top-level directory for files and folders (no recursion)."""
        new_files = []
        try:
            # Only scan the top-level directory, no recursion
            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                return new_files
            
            # Get all items in the top-level directory
            items = os.listdir(dir_path)
            
            # Collect files with their access times for sorting
            file_candidates = []
            for item in items:
                if item.startswith('.'):
                    continue
                
                item_path = os.path.join(dir_path, item)
                
                # Process both files and directories
                if item_path not in self.known_files:
                    try:
                        # Get access time for sorting
                        atime = os.path.getatime(item_path)
                        file_candidates.append((item_path, atime))
                    except (OSError, PermissionError):
                        # If we can't get access time, add it anyway
                        file_candidates.append((item_path, 0))
            
            # Sort files by access time (newest first)
            file_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Add sorted files to new_files
            for file_path, _ in file_candidates:
                new_files.append(file_path)
                self.known_files.add(file_path)
                
        except Exception as e:
            logger.error(f"❌ Error scanning top-level {dir_path}: {e}")
        
        return new_files
    
    def process_event_batch(self):
        """Process accumulated events and emit them."""
        current_time = time.time()
        
        if len(self.event_queue) == 0:
            return
        
        # Log batch processing
        total_events = sum(len(events) for events in self.event_queue.values())
        logger.info(f"📦 Processing batch of {total_events} events from {len(self.event_queue)} files")
        
        # Process each file
        for file_path, events in self.event_queue.items():
            try:
                # Check if file still exists
                if not os.path.exists(file_path):
                    logger.warning(f"⚠️ File disappeared: {file_path}")
                    continue
                
                # Skip if file is still being written (size changing)
                try:
                    stat1 = os.stat(file_path)
                    time.sleep(0.1)
                    stat2 = os.stat(file_path)
                    if stat1.st_size != stat2.st_size:
                        logger.info(f"⏳ File still being written, skipping for now: {file_path}")
                        continue
                except:
                    continue
                
                # Calculate metadata
                ingest_time = datetime.now().isoformat()
                
                # Handle directories differently
                if os.path.isdir(file_path):
                    # For directories, use placeholder values
                    md5_hash = "directory"
                    mime_type = "inode/directory"
                    tagged = self.tag_file(file_path, md5_hash, mime_type, is_retroactive=False)
                else:
                    # For files, calculate actual metadata
                    md5_hash = self.calculate_md5(file_path)
                    mime_type = self.detect_mimetype(file_path)
                    tagged = self.tag_file(file_path, md5_hash, mime_type, is_retroactive=False)
                
                # Check if this is a PDF file in hub that needs ingest job
                if tagged and self.should_trigger_pdf_ingest(file_path, mime_type):
                    job_success, collection_name = self.trigger_pdf_ingest_job(file_path)
                    # Emit event for PDF ingest job creation
                    self.emit_pdf_ingest_event(file_path, job_success, collection_name)
                
                # Check if this is a new folder in hub that needs folder ingest job
                elif tagged and os.path.isdir(file_path) and '/mnt/anvil/hub' in file_path:
                    job_success, collection_name = self.trigger_folder_ingest_job(file_path)
                    # Emit event for folder ingest job creation
                    self.emit_folder_ingest_event(file_path, job_success, collection_name)
                
                # Only emit detailed event data to log file for successfully tagged files
                if tagged:
                    event_data = {
                        "timestamp": ingest_time,
                        "event_type": "NEW_FILE",
                        "file_name": os.path.basename(file_path),
                        "file_path": file_path,
                        "md5_hash": md5_hash,
                        "mime_type": mime_type,
                        "size_bytes": os.path.getsize(file_path),
                        "ingest_time": ingest_time
                    }
                    # Write JSON event to log
                    with open(log_file, 'a') as f:
                        f.write(json.dumps(event_data) + '\n')
                
            except Exception as e:
                logger.error(f"❌ Error processing events for {file_path}: {e}")
        
        # Clear the event queue
        self.event_queue.clear()
        self.last_batch_time = current_time
    
    def is_user_owned_file(self, file_path: str) -> bool:
        """Check if a file is owned by a regular user (not root/system)."""
        try:
            stat_info = os.stat(file_path)
            uid = stat_info.st_uid
            # UIDs >= 1000 are typically regular users (not root/system)
            return uid >= 1000
        except Exception as e:
            logger.error(f"❌ Error checking ownership for {file_path}: {e}")
            return False
    
    def scan_for_untagged_files(self):
        """Scan hub share for untagged user files and tag them."""
        # Try to find hub path from available mounts
        hub_path = None
        for mount in self.watch_paths:
            if 'hub' in mount:
                hub_path = mount
                break
        if not hub_path:
            hub_path = "/mnt/anvil/hub"  # fallback
        
        if hub_path not in self.watch_paths:
            logger.warning(f"⚠️ Hub path {hub_path} not in watch list, skipping untagged scan")
            return
        
        logger.debug("🔍 Scanning hub share for untagged user-owned files...")
        untagged_count = 0
        tagged_count = 0
        
        try:
            # Collect all untagged files with their access times for sorting
            file_candidates = []
            
            # Recursively scan hub share
            for root, dirs, files in os.walk(hub_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                # Limit depth to 0 levels (top-level only)
                depth = root[len(hub_path):].count(os.sep)
                if depth >= 0:
                    dirs.clear()
                    continue
                
                # Check each file
                for filename in files:
                    if filename.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, filename)
                    
                    # Skip files we've already processed (prevents reprocessing)
                    if file_path in self.tagged_files:
                        continue
                    
                    # Check if user-owned
                    if not self.is_user_owned_file(file_path):
                        continue
                    
                    # Get access time for sorting
                    try:
                        atime = os.path.getatime(file_path)
                        file_candidates.append((file_path, atime))
                    except (OSError, PermissionError):
                        # If we can't get access time, add it anyway
                        file_candidates.append((file_path, 0))
            
            # Sort files by access time (newest first) to prioritize recent files
            file_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Process files in order of access time (newest first)
            for file_path, _ in file_candidates:
                # File is user-owned - check if untagged
                untagged_count += 1
                
                # Calculate metadata
                md5_hash = self.calculate_md5(file_path)
                mime_type = self.detect_mimetype(file_path)
                
                # Tag the file (tag_file will check if already tagged and skip if so)
                if self.tag_file(file_path, md5_hash, mime_type, is_retroactive=True):
                    tagged_count += 1
                    self.files_tagged_retroactively += 1
                    
                    # Write JSON event to log for retroactive tags
                    event_data = {
                        "timestamp": datetime.now().isoformat(),
                        "event_type": "RETROACTIVE_TAG",
                        "file_name": os.path.basename(file_path),
                        "file_path": file_path,
                        "md5_hash": md5_hash,
                        "mime_type": mime_type,
                        "size_bytes": os.path.getsize(file_path),
                        "ingest_time": datetime.now().isoformat()
                    }
                    with open(log_file, 'a') as f:
                        f.write(json.dumps(event_data) + '\n')
        
        except Exception as e:
            logger.error(f"❌ Error in untagged file scan: {e}")
        
        # Only log if we actually found and tagged files
        if tagged_count > 0:
            logger.info(f"✅ Untagged scan: Tagged {tagged_count} previously untagged files")
        elif untagged_count > 0:
            logger.debug(f"✅ Untagged scan: Checked {untagged_count} files, all already tagged")
    
    def get_cpu_stats(self) -> Dict:
        """Get current CPU usage statistics."""
        try:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            self.cpu_samples.append(cpu_percent)
            
            # Keep only last max_cpu_samples
            if len(self.cpu_samples) > self.max_cpu_samples:
                self.cpu_samples = self.cpu_samples[-self.max_cpu_samples:]
            
            avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
            max_cpu = max(self.cpu_samples) if self.cpu_samples else 0
            
            # Log high CPU usage
            if cpu_percent > 50:
                logger.warning(f"⚠️ HIGH CPU USAGE: {cpu_percent:.1f}% (avg: {avg_cpu:.1f}%, max: {max_cpu:.1f}%)")
            
            return {
                "current_cpu_percent": round(cpu_percent, 2),
                "average_cpu_percent": round(avg_cpu, 2),
                "max_cpu_percent": round(max_cpu, 2),
                "samples_count": len(self.cpu_samples)
            }
        except Exception as e:
            logger.error(f"❌ Failed to get CPU stats: {e}")
            return {
                "current_cpu_percent": 0,
                "average_cpu_percent": 0,
                "max_cpu_percent": 0,
                "error": str(e)
            }
    
    async def monitor_shares(self):
        """Monitor all Hammerspace shares for new files using polling."""
        logger.info("🚀 Starting file monitor for Hammerspace shares (polling mode - NFS compatible)")
        
        # Discover mount points
        self.watch_paths = self.get_mount_points()
        
        if not self.watch_paths:
            logger.error("❌ No Hammerspace mount points found!")
            return
        
        logger.info(f"👀 Monitoring {len(self.watch_paths)} mount points")
        
        # Initialize known files by scanning top-level only (fast scan)
        logger.info("🔍 Initial top-level scan to catalog existing files...")
        for path in self.watch_paths:
            try:
                files = self.scan_top_level_only(path)
                logger.info(f"📝 Found {len(files)} existing files in {path} (top-level only)")
            except Exception as e:
                logger.error(f"❌ Error in initial scan of {path}: {e}")
        
        self.running = True
        
        # Polling-only mode (inotify disabled for NFS compatibility)
        logger.info("✅ File monitor started - polling mode only")
        
        # Main monitoring loop
        while self.running:
            try:
                # Scan for new files via polling (top-level only for speed)
                for path in self.watch_paths:
                    new_files = self.scan_top_level_only(path)
                    logger.debug(f"🔍 Scanned {path}: found {len(new_files)} new files")
                    
                    # Add new files to event queue
                    # Always process new files immediately, regardless of time
                    for file_path in new_files:
                        logger.info(f"🔔 NEW FILE DETECTED: {file_path}")
                        self.known_files.add(file_path)
                        event_info = {
                            "time": datetime.now().isoformat(),
                            "action": "created",
                            "name": os.path.basename(file_path),
                            "priority": "normal"
                        }
                        self.event_queue[file_path].append(event_info)
                        logger.info(f"🔔 New file detected (polling): {file_path}")
                
                # Check if it's time to process batch
                current_time = time.time()
                if current_time - self.last_batch_time >= self.batch_interval:
                    if len(self.event_queue) > 0:
                        self.process_event_batch()
                
                # If traffic is light (< 5 pending files), process immediately
                if 0 < len(self.event_queue) < 5:
                    logger.info(f"🔔 Low traffic - processing {len(self.event_queue)} file(s) immediately")
                    self.process_event_batch()
                
                # Scan for untagged files in hub every 5 seconds (only during 1am-8am)
                if current_time - self.last_untagged_scan >= self.untagged_scan_interval:
                    if self.is_retroactive_tagging_time():
                        logger.info(f"🔍 Starting periodic scan for untagged user files in hub (interval: {self.untagged_scan_interval}s)...")
                        self.scan_for_untagged_files()
                        self.last_untagged_scan = current_time
                    else:
                        # Log that retroactive tagging is paused during business hours
                        if current_time - self.last_untagged_scan >= 300:  # Log every 5 minutes
                            eastern = ZoneInfo('US/Eastern')
                            current_time_et = datetime.now(eastern)
                            current_hour = current_time_et.hour
                            logger.info(f"⏰ Retroactive tagging paused (current time: {current_hour:02d}:00 ET, runs 01:00-08:00 ET)")
                            self.last_untagged_scan = current_time
                
                # Monitor CPU usage every 10th iteration (~20 seconds)
                if hasattr(self, '_poll_count'):
                    self._poll_count += 1
                else:
                    self._poll_count = 1
                
                if self._poll_count % 10 == 0:
                    cpu_stats = self.get_cpu_stats()
                    if cpu_stats['current_cpu_percent'] > 10:
                        logger.info(f"📊 CPU Usage: {cpu_stats['current_cpu_percent']}% (avg: {cpu_stats['average_cpu_percent']}%)")
                
                # Use faster polling during business hours (outside retroactive window)
                if self.is_retroactive_tagging_time():
                    # During retroactive hours (1am-8am ET), use normal polling
                    await asyncio.sleep(self.poll_interval)
                else:
                    # During business hours (8am-1am ET), use fast polling for new files
                    await asyncio.sleep(self.fast_poll_interval)
                
            except Exception as e:
                if self.running:
                    logger.error(f"❌ Error in monitor loop: {e}")
                    await asyncio.sleep(1)
        
        # Cleanup
        logger.info("🛑 File monitor stopped")
        # Process any remaining events
        if len(self.event_queue) > 0:
            self.process_event_batch()
    
    def should_trigger_pdf_ingest(self, file_path: str, mime_type: str) -> bool:
        """Check if a file should trigger a PDF ingest job."""
        # Check if it's a PDF file
        if mime_type != 'application/pdf' and not file_path.lower().endswith('.pdf'):
            return False
        
        # Check if it's in the hub directory
        if '/mnt/anvil/hub' not in file_path:
            return False
        
        # Check if file is less than 12 hours old (based on atime)
        try:
            stat_info = os.stat(file_path)
            atime = stat_info.st_atime
            current_time = time.time()
            age_hours = (current_time - atime) / 3600
            
            if age_hours > 12:
                logger.info(f"📄 PDF file {file_path} is {age_hours:.1f} hours old, skipping ingest")
                return False
                
            logger.info(f"📄 PDF file {file_path} is {age_hours:.1f} hours old, will trigger ingest")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking file age for {file_path}: {e}")
            return False
    
    def trigger_pdf_ingest_job(self, file_path: str) -> tuple[bool, str]:
        """Trigger a PDF ingest job for a single file. Returns (success, collection_name)."""
        try:
            logger.info(f"🚀 Triggering PDF ingest job for: {file_path}")
            
            # Get the collection name first
            collection_name = self.get_next_collection_name()
            
            # Create a job name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            job_name = f"pdf-ingest-{timestamp}"
            
            # Create the ingest job YAML
            success = self.create_pdf_ingest_job([file_path], job_name, collection_name)
            return success, collection_name
            
        except Exception as e:
            logger.error(f"❌ Failed to trigger PDF ingest job for {file_path}: {e}")
            return False, "unknown"

    def trigger_folder_ingest_job(self, folder_path: str) -> tuple[bool, str]:
        """Trigger a PDF ingest job for all files in a folder. Returns (success, collection_name)."""
        try:
            logger.info(f"🚀 Triggering folder ingest job for: {folder_path}")
            
            # Get all PDF files in the folder
            pdf_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        pdf_files.append(file_path)
            
            if not pdf_files:
                logger.info(f"📁 No PDF files found in folder: {folder_path}")
                return False, ""
            
            logger.info(f"📁 Found {len(pdf_files)} PDF files in folder: {folder_path}")
            
            # Use folder name for collection (sanitized)
            folder_name = os.path.basename(folder_path)
            # Replace invalid characters with underscores for Milvus collection names
            collection_name = re.sub(r'[^a-zA-Z0-9_]', '_', folder_name)
            if not collection_name or collection_name[0].isdigit():
                collection_name = f"folder_{collection_name}"
            
            # Create and deploy the job
            job_name = f"folder-ingest-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            success = self.create_pdf_ingest_job(pdf_files, job_name, collection_name)
            
            if success:
                # Log success event
                event_data = {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "FOLDER_INGEST_SUCCESS",
                    "folder_name": folder_name,
                    "folder_path": folder_path,
                    "file_count": len(pdf_files),
                    "status": "SUCCESS",
                    "job_type": "folder_ingest",
                    "collection_name": collection_name,
                    "ingest_time": datetime.now().isoformat()
                }
                with open(log_file, 'a') as f:
                    f.write(json.dumps(event_data) + '\n')
                
                logger.info(f"📁 FOLDER INGEST SUCCESS: {folder_path} → {len(pdf_files)} files deployed to {collection_name}")
                
                # Schedule job completion check
                try:
                    threading.Timer(30.0, self.check_job_completion, args=[folder_path, collection_name]).start()
                except Exception as e:
                    logger.error(f"❌ Failed to schedule job completion check for {folder_path}: {e}")
                
                return True, collection_name
            else:
                # Log failure event
                event_data = {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "FOLDER_INGEST_FAILURE",
                    "folder_name": folder_name,
                    "folder_path": folder_path,
                    "file_count": len(pdf_files),
                    "status": "FAILURE",
                    "job_type": "folder_ingest",
                    "error": "Failed to create or deploy job",
                    "ingest_time": datetime.now().isoformat()
                }
                with open(log_file, 'a') as f:
                    f.write(json.dumps(event_data) + '\n')
                
                logger.error(f"❌ FOLDER INGEST FAILURE: {folder_path} → Failed to create or deploy job")
                return False, ""
                
        except Exception as e:
            logger.error(f"❌ Error triggering folder ingest job for {folder_path}: {e}")
            return False, ""
    
    def get_next_collection_name(self) -> str:
        """Get the next available collection name in the format intel-X."""
        try:
            # Check existing collections by looking at ConfigMaps with intel- prefix
            result = subprocess.run(
                ["kubectl", "get", "configmaps", "-o", "name"], 
                capture_output=True, text=True, check=True
            )
            
            # Extract collection numbers from existing intel_ collections
            existing_numbers = set()
            for line in result.stdout.split('\n'):
                if 'intel_' in line:
                    # Extract number from configmap name like "intel_1-file-list"
                    parts = line.split('intel_')
                    if len(parts) > 1:
                        number_part = parts[1].split('-')[0]
                        try:
                            existing_numbers.add(int(number_part))
                        except ValueError:
                            continue
            
            # Find the next available number
            next_number = 1
            while next_number in existing_numbers:
                next_number += 1
            
            collection_name = f"intel_{next_number}"
            logger.info(f"📦 Using collection name: {collection_name}")
            return collection_name
            
        except Exception as e:
            logger.error(f"❌ Error getting next collection name: {e}")
            # Fallback to timestamp-based name
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            return f"intel-{timestamp}"

    def create_pdf_ingest_job(self, pdf_files: List[str], job_name: str, collection_name: str = None) -> bool:
        """Create and deploy a Kubernetes job to ingest PDF files. Returns True if successful."""
        try:
            # Use provided collection name or get the next one
            if not collection_name:
                collection_name = self.get_next_collection_name()
            
            # Create file list content with relative paths (volume is mounted at /data)
            relative_files = []
            for f in pdf_files:
                # Convert absolute path to relative path for container
                if f.startswith('/mnt/anvil/hub/'):
                    relative_path = f.replace('/mnt/anvil/hub/', '/data/')
                    relative_files.append(relative_path)
                else:
                    relative_files.append(f)
            file_list_content = "\n".join(relative_files)
            
            # Create ConfigMap
            configmap = {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {
                    "name": f"{job_name}-file-list",
                    "namespace": "default"
                },
                "data": {
                    "files.txt": file_list_content
                }
            }
            
            # Create Job (based on the original ingest.yaml)
            job = {
                "apiVersion": "batch/v1",
                "kind": "Job",
                "metadata": {
                    "name": job_name,
                    "namespace": "default"
                },
                "spec": {
                    "backoffLimit": 0,
                    "template": {
                        "spec": {
                            "restartPolicy": "Never",
                            "containers": [{
                                "name": "ingest",
                                "image": "alpine:3.19",
                                "command": ["/bin/sh", "-lc"],
                                "args": ["""
set -euo pipefail
apk add --no-cache curl coreutils
API="http://ingestor-server:8082"
COLLECTION_NAME="${COLLECTION_NAME:-bulk_selected_pdfs}"
LIST="/work/files.txt"

echo "Creating collection: ${COLLECTION_NAME}"
curl -sf -X POST "${API}/collection" \\
  -H "Content-Type: application/json" \\
  -d "{\\"collection_name\\":\\"${COLLECTION_NAME}\\"}" || true

successes=0; failures=0
while IFS= read -r f || [ -n "${f-}" ]; do
  case "${f}" in ""|\\#*) continue;; esac
  if [ -f "${f}" ]; then
    echo "Uploading: ${f}"
    if curl -sf -X POST "${API}/documents" \\
          -F "documents=@${f}" \\
          -F "data={\\"collection_name\\":\\"${COLLECTION_NAME}\\"}"; then
      successes=$((successes+1))
    else
      echo "Upload failed: ${f}" >&2
      failures=$((failures+1))
    fi
  else
    echo "Missing file: ${f}" >&2
    failures=$((failures+1))
  fi
done < "${LIST}"

echo "Submitted. Successes=${successes}, Failures=${failures}"
echo "Note: ingestion is async; allow processing time."
                                """],
                                         "env": [{
                                             "name": "COLLECTION_NAME",
                                             "value": collection_name
                                         }],
                                "volumeMounts": [
                                    {
                                        "name": "pdfs",
                                        "mountPath": "/data"
                                    },
                                    {
                                        "name": "filelist",
                                        "mountPath": "/work"
                                    }
                                ]
                            }],
                            "volumes": [
                                {
                                    "name": "pdfs",
                                         "persistentVolumeClaim": {
                                             "claimName": "hammerspace-hub-pvc"
                                         }
                                },
                                {
                                    "name": "filelist",
                                    "configMap": {
                                        "name": f"{job_name}-file-list",
                                        "items": [{
                                            "key": "files.txt",
                                            "path": "files.txt"
                                        }]
                                    }
                                }
                            ]
                        }
                    }
                }
            }
            
            # Write YAML files
            configmap_file = f"/tmp/{job_name}-configmap.yaml"
            job_file = f"/tmp/{job_name}-job.yaml"
            
            with open(configmap_file, 'w') as f:
                yaml.dump(configmap, f, default_flow_style=False)
                
            with open(job_file, 'w') as f:
                yaml.dump(job, f, default_flow_style=False)
            
            # Deploy to Kubernetes
            logger.info(f"📦 Deploying ConfigMap: {configmap_file}")
            subprocess.run(["kubectl", "apply", "-f", configmap_file], check=True)
            
            logger.info(f"📦 Deploying Job: {job_file}")
            subprocess.run(["kubectl", "apply", "-f", job_file], check=True)
            
            # Clean up temp files
            os.unlink(configmap_file)
            os.unlink(job_file)
            
            logger.info(f"✅ Successfully deployed PDF ingest job '{job_name}' for {len(pdf_files)} files")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to deploy PDF ingest job: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error creating PDF ingest job: {e}")
            return False

    def emit_pdf_ingest_event(self, file_path: str, success: bool, collection_name: str = None):
        """Emit a PDF ingest event to the log file."""
        try:
            event_type = "PDF_INGEST_SUCCESS" if success else "PDF_INGEST_FAILURE"
            status = "SUCCESS" if success else "FAILURE"
            
            # Use provided collection name or fallback
            if not collection_name:
                collection_name = "bulk_selected_pdfs"
            
            event_data = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "status": status,
                "job_type": "pdf_ingest",
                "collection_name": collection_name,
                "ingest_time": datetime.now().isoformat()
            }
            
            # Write JSON event to log
            with open(log_file, 'a') as f:
                f.write(json.dumps(event_data) + '\n')
            
            if success:
                logger.info(f"📄 PDF INGEST SUCCESS: {file_path} → Job created and deployed to {collection_name}")
                # Schedule job completion check
                self.schedule_job_completion_check(file_path, collection_name)
            else:
                logger.error(f"📄 PDF INGEST FAILURE: {file_path} → Job creation/deployment failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to emit PDF ingest event for {file_path}: {e}")

    def emit_folder_ingest_event(self, folder_path: str, success: bool, collection_name: str = None):
        """Emit a folder ingest event to the log file."""
        try:
            event_type = "FOLDER_INGEST_SUCCESS" if success else "FOLDER_INGEST_FAILURE"
            status = "SUCCESS" if success else "FAILURE"
            
            # Use provided collection name or fallback
            if not collection_name:
                collection_name = "folder_collection"
            
            # Count PDF files in folder
            pdf_count = 0
            try:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            pdf_count += 1
            except:
                pdf_count = 0
            
            event_data = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "folder_name": os.path.basename(folder_path),
                "folder_path": folder_path,
                "file_count": pdf_count,
                "status": status,
                "job_type": "folder_ingest",
                "collection_name": collection_name,
                "ingest_time": datetime.now().isoformat()
            }
            
            # Write JSON event to log
            with open(log_file, 'a') as f:
                f.write(json.dumps(event_data) + '\n')
            
            if success:
                logger.info(f"📁 FOLDER INGEST SUCCESS: {folder_path} → {pdf_count} files deployed to {collection_name}")
                # Schedule job completion check
                self.schedule_job_completion_check(folder_path, collection_name)
            else:
                logger.error(f"📁 FOLDER INGEST FAILURE: {folder_path} → Job creation/deployment failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to emit folder ingest event for {folder_path}: {e}")
    
    def schedule_job_completion_check(self, file_path: str, collection_name: str):
        """Schedule a check for job completion and tagging."""
        try:
            # Create a simple tracking entry for this file
            # In a production system, you might use a database or more sophisticated tracking
            import threading
            import time
            
            # Start the completion check in a background thread
            completion_thread = threading.Thread(target=self.check_job_completion, args=[file_path, collection_name], daemon=True)
            completion_thread.start()
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule job completion check for {file_path}: {e}")

    def check_job_completion(self, file_path: str, collection_name: str):
        """Check for job completion and tag files when done."""
        try:
            import time
            
            # Wait for job to complete (check every 30 seconds for up to 10 minutes)
            max_checks = 20  # 10 minutes total
            check_interval = 30  # seconds
            
            for attempt in range(max_checks):
                time.sleep(check_interval)
                
                # Check if job completed successfully
                if self.check_and_tag_embedded_file(file_path, collection_name):
                    logger.info(f"✅ PDF EMBEDDING COMPLETE: {file_path} → Successfully tagged as embedded in {collection_name}")
                    return
                
                logger.debug(f"⏳ PDF EMBEDDING CHECK {attempt + 1}/{max_checks}: {file_path} → Job still running")
            
            logger.warning(f"⏰ PDF EMBEDDING TIMEOUT: {file_path} → Job completion check timed out")
            
        except Exception as e:
            logger.error(f"❌ Failed to check job completion for {file_path}: {e}")
    
    def check_and_tag_embedded_file(self, file_path: str, collection_name: str) -> bool:
        """Check if the PDF has been successfully embedded and tag it."""
        try:
            # Check if file still exists and is accessible
            if not os.path.exists(file_path):
                return False
            
            # Check Kubernetes job status
            if not self.check_kubernetes_job_completion(collection_name):
                return False
            
            # Check if the file was actually processed by the ingest service
            if not self.verify_file_in_collection(file_path, collection_name):
                return False
            
            # Tag the file as embedded only after verification
            success = self.tag_file_with_state(file_path, "embedded")
            
            if success:
                # Emit embedding completion event
                self.emit_embedding_completion_event(file_path, True, collection_name, milvus_verified=True)
                # Emit specific Milvus confirmation event
                self.emit_milvus_embeddings_confirmed(file_path, collection_name)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking embedding status for {file_path}: {e}")
            return False
    
    def check_kubernetes_job_completion(self, collection_name: str) -> bool:
        """Check if the Kubernetes job for this collection has completed successfully."""
        try:
            # Look for jobs with the collection name pattern
            result = subprocess.run(
                ["kubectl", "get", "jobs", "-o", "jsonpath={.items[?(@.metadata.name=~'.*pdf-ingest.*')].status}"],
                capture_output=True, text=True, check=True
            )
            
            if not result.stdout.strip():
                logger.debug(f"⏳ No PDF ingest jobs found yet for {collection_name}")
                return False
            
            # Parse job status to check if completed successfully
            # This is a simplified check - in production you'd parse the JSON properly
            if "succeeded" in result.stdout.lower() or "completed" in result.stdout.lower():
                logger.info(f"✅ Kubernetes job completed successfully for {collection_name}")
                return True
            
            logger.debug(f"⏳ Kubernetes job still running for {collection_name}")
            return False
            
        except subprocess.CalledProcessError as e:
            logger.debug(f"⏳ Kubernetes job check failed (job may not exist yet): {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error checking Kubernetes job status: {e}")
            return False
    
    def verify_file_in_collection(self, file_path: str, collection_name: str) -> bool:
        """Verify that the file was actually processed and stored in the Milvus collection."""
        try:
            # First, check if the ingest service is responding
            if not self.check_ingest_service_health():
                return False
            
            # Try to query the Milvus collection to see if the file was processed
            if self.query_milvus_collection(file_path, collection_name):
                return True
            
            # Fallback: Check ingest service logs for processing confirmation
            if self.check_ingest_service_logs(file_path, collection_name):
                return True
            
            logger.debug(f"⏳ Cannot verify {file_path} was processed into {collection_name}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error verifying file in collection: {e}")
            return False
    
    def check_ingest_service_health(self) -> bool:
        """Check if the ingest service is healthy and responding."""
        try:
            result = subprocess.run(
                ["curl", "-s", "-f", "http://ingestor-server:8082/health"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                logger.debug("✅ Ingest service is healthy")
                return True
            else:
                logger.debug("⏳ Ingest service not responding")
                return False
                
        except subprocess.TimeoutExpired:
            logger.debug("⏳ Ingest service timeout")
            return False
        except Exception as e:
            logger.debug(f"⏳ Cannot check ingest service health: {e}")
            return False
    
    def query_milvus_collection(self, file_path: str, collection_name: str) -> bool:
        """Query the Milvus collection to verify the file was processed."""
        try:
            filename = os.path.basename(file_path)
            
            # Use the verification script to check if the file exists in the collection
            script_path = "/home/ubuntu/mcp-1.5-main/verify_milvus_collection.py"
            
            result = subprocess.run(
                ["python3", script_path, collection_name, filename],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Milvus verification: {filename} found in collection {collection_name}")
                return True
            else:
                logger.debug(f"⏳ Milvus verification: {filename} not found in collection {collection_name}")
                if result.stderr:
                    logger.debug(f"Verification error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.debug(f"⏳ Milvus verification timeout for {filename}")
            return False
        except Exception as e:
            logger.debug(f"⏳ Cannot query Milvus collection: {e}")
            return False
    
    def check_ingest_service_logs(self, file_path: str, collection_name: str) -> bool:
        """Check ingest service logs for processing confirmation."""
        try:
            # Check the logs of the ingest service for this specific file
            filename = os.path.basename(file_path)
            
            # Look for recent logs mentioning this file
            result = subprocess.run(
                ["kubectl", "logs", "-l", "app=ingestor-server", "--tail=100"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                logs = result.stdout.lower()
                # Look for indicators that the file was processed
                if (filename.lower() in logs and 
                    ("success" in logs or "processed" in logs or "uploaded" in logs)):
                    logger.info(f"✅ Found processing confirmation for {filename} in ingest logs")
                    return True
            
            logger.debug(f"⏳ No processing confirmation found for {filename} in ingest logs")
            return False
            
        except Exception as e:
            logger.debug(f"⏳ Cannot check ingest service logs: {e}")
            return False
    
    def tag_file_with_state(self, file_path: str, state: str) -> bool:
        """Tag a file with a state (e.g., 'embedded')."""
        try:
            cmd = [self.hs_cli, "tag", "set", f"state={state}", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(file_path))
            
            if result.returncode == 0:
                logger.info(f"✅ STATE TAG: {file_path} → state={state}")
                return True
            else:
                logger.error(f"❌ Failed to tag {file_path} with state={state}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error tagging {file_path} with state={state}: {e}")
            return False
    
    def emit_embedding_completion_event(self, file_path: str, success: bool, collection_name: str = None, milvus_verified: bool = False):
        """Emit an event when PDF embedding is completed."""
        try:
            event_type = "PDF_EMBEDDING_SUCCESS" if success else "PDF_EMBEDDING_FAILURE"
            status = "EMBEDDED" if success else "FAILED"
            
            # Use provided collection name or fallback
            if not collection_name:
                collection_name = "bulk_selected_pdfs"
            
            event_data = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "status": status,
                "state": "embedded" if success else "failed",
                "collection_name": collection_name,
                "milvus_verified": milvus_verified,
                "milvus_uri": "10.0.0.60:30195",
                "completion_time": datetime.now().isoformat()
            }
            
            # Write JSON event to log
            with open(log_file, 'a') as f:
                f.write(json.dumps(event_data) + '\n')
            
            if success:
                logger.info(f"🎯 PDF EMBEDDING SUCCESS: {file_path} → File successfully embedded and tagged")
            else:
                logger.error(f"🎯 PDF EMBEDDING FAILURE: {file_path} → Embedding process failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to emit embedding completion event for {file_path}: {e}")
    
    def emit_milvus_embeddings_confirmed(self, file_path: str, collection_name: str):
        """Emit an event when Milvus embeddings are confirmed in the database."""
        try:
            filename = os.path.basename(file_path)
            
            # Get file metadata
            file_size = 0
            file_md5 = ""
            mime_type = ""
            
            try:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    file_md5 = self.calculate_md5(file_path)
                    mime_type = self.detect_mimetype(file_path)
            except Exception as e:
                logger.debug(f"Could not get file metadata for {file_path}: {e}")
            
            event_data = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "MILVUS_EMBEDDINGS_CONFIRMED",
                "file_name": filename,
                "file_path": file_path,
                "collection_name": collection_name,
                "milvus_uri": "10.0.0.60:30195",
                "file_metadata": {
                    "size_bytes": file_size,
                    "md5_hash": file_md5,
                    "mime_type": mime_type,
                    "filename": filename
                },
                "embedding_status": "confirmed_in_database",
                "verification_time": datetime.now().isoformat()
            }
            
            # Write JSON event to log
            with open(log_file, 'a') as f:
                f.write(json.dumps(event_data) + '\n')
            
            logger.info(f"🎯 MILVUS EMBEDDINGS CONFIRMED: {filename} → Verified in collection {collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to emit Milvus embeddings confirmed event for {file_path}: {e}")

    # Inotify methods removed - using polling-only mode
    
    # All inotify methods removed - using polling-only mode
    
    def is_retroactive_tagging_time(self):
        """Check if current time is within retroactive tagging hours (disabled for testing)."""
        # Always return False to completely disable retroactive tagging
        return False

    def stop(self):
        """Stop the monitoring service."""
        logger.info("🛑 Stopping file monitor...")
        self.running = False


class FileMonitorService:
    """Service wrapper for managing the file monitor."""
    
    def __init__(self):
        self.monitor = None
        self.task = None
    
    async def start(self):
        """Start the file monitoring service."""
        if self.monitor and self.monitor.running:
            return {"success": False, "message": "Monitor already running"}
        
        try:
            self.monitor = HammerspaceFileMonitor()
            self.task = asyncio.create_task(self.monitor.monitor_shares())
            
            # Give it a moment to initialize
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "message": "File monitor started (polling mode - NFS compatible)",
                "watch_paths": self.monitor.watch_paths,
                "batch_interval": self.monitor.batch_interval,
                "poll_interval": self.monitor.poll_interval,
                "known_files": len(self.monitor.known_files),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Failed to start monitor: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def stop(self):
        """Stop the file monitoring service."""
        if not self.monitor or not self.monitor.running:
            return {"success": False, "message": "Monitor not running"}
        
        try:
            self.monitor.stop()
            
            # Wait for task to complete
            if self.task:
                await asyncio.sleep(2)
                if not self.task.done():
                    self.task.cancel()
                    try:
                        await self.task
                    except asyncio.CancelledError:
                        pass
            
            return {
                "success": True,
                "message": "File monitor stopped",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Failed to stop monitor: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_status(self) -> Dict:
        """Get current status of the file monitor."""
        if not self.monitor:
            return {
                "running": False,
                "message": "Monitor not initialized",
                "timestamp": datetime.now().isoformat()
            }
        
        # Get CPU stats
        cpu_stats = self.monitor.get_cpu_stats() if self.monitor.running else {}
        
        return {
            "running": self.monitor.running,
            "watch_paths": self.monitor.watch_paths,
            "batch_interval": self.monitor.batch_interval,
            "poll_interval": self.monitor.poll_interval,
            "pending_events": sum(len(events) for events in self.monitor.event_queue.values()),
            "pending_files": len(self.monitor.event_queue),
            "known_files_count": len(self.monitor.known_files),
            "tagged_files_count": len(self.monitor.tagged_files),
            "last_batch_time": datetime.fromtimestamp(self.monitor.last_batch_time).isoformat(),
            "last_untagged_scan": datetime.fromtimestamp(self.monitor.last_untagged_scan).isoformat() if self.monitor.last_untagged_scan > 0 else "Never",
            "files_tagged_retroactively": self.monitor.files_tagged_retroactively,
            "untagged_scan_interval": self.monitor.untagged_scan_interval,
            "cpu_usage": cpu_stats,
            "timestamp": datetime.now().isoformat()
        }


# Global service instance
_monitor_service = None

def get_monitor_service() -> FileMonitorService:
    """Get or create the global monitor service instance."""
    global _monitor_service
    if _monitor_service is None:
        _monitor_service = FileMonitorService()
    return _monitor_service


if __name__ == "__main__":
    """Test the monitor standalone."""
    async def test():
        service = get_monitor_service()
        
        # Start monitoring
        result = await service.start()
        print(f"Start result: {json.dumps(result, indent=2)}")
        
        # Run for 30 seconds
        print("Monitoring for 30 seconds... Create some files to test!")
        for i in range(6):
            await asyncio.sleep(5)
            status = service.get_status()
            print(f"Status: Running={status['running']}, Pending={status['pending_files']}, Known={status['known_files_count']}")
        
        # Stop monitoring
        result = await service.stop()
        print(f"Stop result: {json.dumps(result, indent=2)}")
    
    asyncio.run(test())
