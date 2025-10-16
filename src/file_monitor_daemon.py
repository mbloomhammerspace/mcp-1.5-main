#!/usr/bin/env python3
"""
Standalone File Monitor Daemon
Runs the Hammerspace file monitoring service as a standalone daemon.
This is separate from the MCP server and focuses only on file monitoring and tagging.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from file_monitor import FileMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/mcp-1.5-main/logs/file_monitor_daemon.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the file monitor daemon."""
    print("🚀 Starting Hammerspace File Monitor Daemon")
    logger.info("🚀 Starting Hammerspace File Monitor Daemon")
    
    try:
        print("📋 Initializing file monitor...")
        logger.info("📋 Initializing file monitor...")
        
        # Initialize the file monitor with polling-only mode
        monitor = FileMonitor()
        print("✅ File monitor initialized")
        logger.info("✅ File monitor initialized")
        
        # Polling-only mode (no inotify)
        monitor.inotify_available = False
        print("🔧 Set to polling-only mode")
        logger.info("🔧 Set to polling-only mode")
        
        print("🚀 Starting monitoring...")
        logger.info("🚀 Starting monitoring...")
        
        # Start monitoring
        await monitor.monitor_shares()
        
    except KeyboardInterrupt:
        print("🛑 File monitor daemon stopped by user")
        logger.info("🛑 File monitor daemon stopped by user")
    except Exception as e:
        print(f"❌ File monitor daemon error: {e}")
        logger.error(f"❌ File monitor daemon error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if 'monitor' in locals():
            print("🛑 Stopping monitor...")
            monitor.stop()
        print("✅ File monitor daemon shutdown complete")
        logger.info("✅ File monitor daemon shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
