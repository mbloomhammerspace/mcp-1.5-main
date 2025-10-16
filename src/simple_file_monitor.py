#!/usr/bin/env python3
"""
Simple File Monitor - Basic version to test file processing
"""

import os
import time
import subprocess
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/mcp-1.5-main/logs/simple_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def tag_file(file_path):
    """Tag a file with basic metadata."""
    try:
        # Calculate MD5 hash
        import hashlib
        with open(file_path, 'rb') as f:
            md5_hash = hashlib.md5(f.read()).hexdigest()
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Get MIME type
        import magic
        mime_type = magic.from_file(file_path, mime=True)
        
        # Tag the file
        cmd = ['/home/ubuntu/.local/bin/hs', 'tag', 'set', f'md5={md5_hash}', file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(file_path))
        
        if result.returncode == 0:
            logger.info(f"✅ TAGGED: {os.path.basename(file_path)} (md5={md5_hash[:8]}..., size={file_size}, mime={mime_type})")
            return True
        else:
            logger.error(f"❌ FAILED TO TAG: {os.path.basename(file_path)} - {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR TAGGING {file_path}: {e}")
        return False

def scan_and_process_files():
    """Scan hub directory and process new files."""
    hub_path = "/mnt/anvil/hub"
    known_files = set()
    
    logger.info(f"🔍 Scanning {hub_path} for new files...")
    
    try:
        items = os.listdir(hub_path)
        logger.info(f"📝 Found {len(items)} items in {hub_path}")
        
        for item in items:
            if item.startswith('.'):
                continue
                
            item_path = os.path.join(hub_path, item)
            
            if os.path.isfile(item_path) and item_path not in known_files:
                logger.info(f"🔔 NEW FILE: {item}")
                
                # Check if file already has tags
                cmd = ['/home/ubuntu/.local/bin/hs', 'tag', 'list', item_path]
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=hub_path)
                
                if "TAGS_TABLE{}" in result.stdout:
                    # File has no tags, process it
                    logger.info(f"📄 Processing untagged file: {item}")
                    tag_file(item_path)
                else:
                    logger.info(f"⏭️ File already tagged: {item}")
                
                known_files.add(item_path)
                
    except Exception as e:
        logger.error(f"❌ Error scanning {hub_path}: {e}")

def main():
    """Main monitoring loop."""
    logger.info("🚀 Starting Simple File Monitor")
    
    try:
        while True:
            scan_and_process_files()
            time.sleep(2)  # Poll every 2 seconds
            
    except KeyboardInterrupt:
        logger.info("🛑 Simple File Monitor stopped by user")
    except Exception as e:
        logger.error(f"❌ Simple File Monitor error: {e}")
        raise

if __name__ == "__main__":
    main()
