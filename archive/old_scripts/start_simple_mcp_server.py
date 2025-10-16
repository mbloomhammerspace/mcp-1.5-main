#!/usr/bin/env python3
"""
Start the Simple Volume Canvas MCP Server
This script starts the MCP server using the basic MCP library.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simple_mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('simple_mcp_server')

def main():
    """Main entry point for starting the simple MCP server."""
    try:
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)
        
        # Check for NVIDIA API key
        nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        if not nvidia_api_key:
            logger.warning("NVIDIA_API_KEY environment variable not set - server will run without NVIDIA integration")
        else:
            logger.info(f"🔑 NVIDIA API Key found: {'*' * (len(nvidia_api_key) - 8) + nvidia_api_key[-8:]}")
        
        logger.info("🚀 Starting Simple Volume Canvas MCP Server...")
        logger.info("📡 Server will communicate via stdio")
        
        # Import and run the simple MCP server
        from src.simple_volume_canvas_mcp_server import main as server_main
        
        # Run the server
        asyncio.run(server_main())
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start simple MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

