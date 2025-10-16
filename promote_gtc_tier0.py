#!/usr/bin/env python3
"""
Script to promote all GTC-tagged files to tier0 using the MCP server
"""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def promote_gtc_to_tier0():
    """Use MCP server to promote GTC-tagged files to tier0"""
    
    # Server parameters - run the MCP server via stdio
    server_params = StdioServerParameters(
        command="python",
        args=["/home/mike/mcp-1.5/src/aiq_hstk_mcp_server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            print("✅ Connected to MCP server")
            
            # Step 1: Apply "Place-on-tier0" objective to GTC-tagged directory
            print("\n📋 Step 1: Applying 'Place-on-tier0' objective to GTC-tagged files...")
            
            # The GTC files are in /mnt/se-lab/modelstore/gtc-demo-models/
            path = "/mnt/se-lab/modelstore/gtc-demo-models/"
            objective_name = "Place-on-tier0"
            
            result = await session.call_tool(
                "apply_objective_to_path",
                arguments={
                    "objective_name": objective_name,
                    "path": path
                }
            )
            
            print(f"Result: {json.dumps(result.content[0].text if result.content else {}, indent=2)}")
            
            # Step 2: Check alignment status
            print("\n📋 Step 2: Checking alignment status of GTC-tagged files...")
            
            check_result = await session.call_tool(
                "check_tagged_files_alignment",
                arguments={
                    "path": path,
                    "tag_name": "user.modelsetid",
                    "tag_value": "hs-GTC-0002"
                }
            )
            
            print(f"Alignment check: {json.dumps(check_result.content[0].text if check_result.content else {}, indent=2)}")
            
            print("\n✅ Promotion to tier0 complete!")

if __name__ == "__main__":
    asyncio.run(promote_gtc_to_tier0())

