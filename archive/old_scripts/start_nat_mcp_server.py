#!/usr/bin/env python3
"""
Start the NVIDIA NeMo Agent Toolkit MCP Server for Volume Canvas
This script starts the MCP server using the NAT toolkit configuration.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/nat_mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('nat_mcp_server')

def main():
    """Main entry point for starting the NAT MCP server."""
    try:
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)
        
        # Get configuration file path
        config_file = Path(__file__).parent.parent / "config" / "volume_canvas_nat_config.yml"
        
        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_file}")
            sys.exit(1)
        
        # Get server parameters
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "9901"))
        debug = os.getenv("MCP_DEBUG", "false").lower() == "true"
        
        # Check for NVIDIA API key
        nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        if not nvidia_api_key:
            logger.error("NVIDIA_API_KEY environment variable not set")
            sys.exit(1)
        
        logger.info("🚀 Starting Volume Canvas NAT MCP Server...")
        logger.info(f"📁 Configuration file: {config_file}")
        logger.info(f"🌐 Server will be available at: http://{host}:{port}")
        logger.info(f"🔑 NVIDIA API Key: {'*' * (len(nvidia_api_key) - 8) + nvidia_api_key[-8:]}")
        logger.info(f"🐛 Debug mode: {debug}")
        
        # Import and run the NAT MCP server
        import subprocess
        
        # Build the command
        cmd = [
            "nat", "mcp",
            "--config_file", str(config_file),
            "--host", host,
            "--port", str(port),
            "--debug", str(debug).lower(),
            "--log_level", "INFO"
        ]
        
        logger.info(f"🔧 Running command: {' '.join(cmd)}")
        
        # Run the NAT MCP server
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ NAT MCP server failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        logger.error(f"❌ Failed to start NAT MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
