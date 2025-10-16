#!/usr/bin/env python3

import sys
sys.path.append('/home/ubuntu/mcp-1.5-main/web_ui')

from mcp_bridge import list_objectives_for_path

# Test the function directly
result = list_objectives_for_path({"path": "/mnt/anvil/hub"})
print("Result:", result)

