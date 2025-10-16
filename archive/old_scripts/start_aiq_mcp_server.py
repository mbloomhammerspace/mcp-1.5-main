#!/usr/bin/env python3
"""
Startup script for the NVIDIA AI Q Toolkit MCP Server
This script starts the Volume Canvas MCP server using NVIDIA's AIQ Toolkit patterns.
"""

import asyncio
import argparse
import logging
import signal
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/aiq_mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('aiq_mcp_server')


class AIQMCPServerManager:
    """Manager for running the AIQ MCP Server."""
    
    def __init__(self):
        """Initialize the server manager."""
        self.server = None
        self.running = False
        
    async def start_server(self, config_file: str = None):
        """Start the AIQ MCP server."""
        try:
            from volume_canvas_mcp_server_clean import main as server_main
            
            logger.info("🚀 Starting Volume Canvas MCP Server with NVIDIA Integration...")
            
            # Start the server
            await server_main()
                
        except Exception as e:
            logger.error(f"Failed to start AIQ MCP server: {e}")
            raise
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Volume Canvas AIQ MCP Server")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9901, help="Port to bind to")
    parser.add_argument("--path", default="/sse", help="Path for the MCP endpoint")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Setup signal handlers
    manager = AIQMCPServerManager()
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    logger.info("Starting Volume Canvas AIQ MCP Server")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Path: {args.path}")
    logger.info(f"Debug: {args.debug}")
    
    try:
        asyncio.run(manager.start_server(args.config))
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
