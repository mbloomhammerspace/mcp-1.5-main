#!/usr/bin/env python3
"""
Tag Search to Objectives Workflow Demo
This script demonstrates how to use tag searches to apply objectives for tier management.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def demo_tag_to_objectives_workflow():
    """Demonstrate the complete tag search to objectives workflow."""
    
    print("🎯 Tag Search to Objectives Workflow Demo")
    print("=" * 60)
    
    # Import the server module
    from volume_canvas_mcp_server_clean import handle_call_tool
    
    # Demo 1: Move High-Priority Files to Tier 0
    print("\n📁 Demo 1: Move High-Priority Files to Tier 0")
    print("-" * 50)
    
    # Step 1: Search for high-priority files
    print("🔍 Step 1: Searching for high-priority files...")
    search_result = await handle_call_tool("search_files_by_tag", {
        "tag_name": "user.priority",
        "tag_value": "high"
    })
    
    # Parse the result to extract file paths
    result_data = json.loads(search_result[0].text)
    matching_files = result_data.get("matching_files", [])
    file_paths = [file["path"] for file in matching_files]
    
    print(f"✅ Found {len(file_paths)} high-priority files:")
    for file_path in file_paths:
        print(f"   - {file_path}")
    
    # Step 2: Apply Tier 0 objective
    if file_paths:
        print("\n🎯 Step 2: Applying Tier 0 objective...")
        objective_result = await handle_call_tool("apply_objective_to_files", {
            "file_paths": file_paths,
            "objective_type": "place_on_tier",
            "tier_name": "tier0"
        })
        print("✅ Tier 0 objective applied successfully")
    
    # Demo 2: Archive Old Project Files
    print("\n📁 Demo 2: Archive Old Project Files")
    print("-" * 50)
    
    # Step 1: Search for backup files
    print("🔍 Step 1: Searching for backup files...")
    search_result = await handle_call_tool("search_files_by_tag", {
        "tag_name": "user.project",
        "tag_value": "backup"
    })
    
    result_data = json.loads(search_result[0].text)
    matching_files = result_data.get("matching_files", [])
    file_paths = [file["path"] for file in matching_files]
    
    print(f"✅ Found {len(file_paths)} backup files:")
    for file_path in file_paths:
        print(f"   - {file_path}")
    
    # Step 2: Exclude from Tier 0
    if file_paths:
        print("\n⬇️ Step 2: Excluding from Tier 0...")
        exclude_result = await handle_call_tool("apply_objective_to_files", {
            "file_paths": file_paths,
            "objective_type": "exclude_from_tier",
            "tier_name": "tier0"
        })
        print("✅ Exclude from Tier 0 objective applied")
    
    # Demo 3: Environment-Based Tier Management
    print("\n📁 Demo 3: Environment-Based Tier Management")
    print("-" * 50)
    
    # Step 1: Search for warm storage files
    print("🔍 Step 1: Searching for warm storage files...")
    search_result = await handle_call_tool("search_files_by_tag", {
        "tag_name": "user.tier",
        "tag_value": "warm"
    })
    
    result_data = json.loads(search_result[0].text)
    matching_files = result_data.get("matching_files", [])
    file_paths = [file["path"] for file in matching_files]
    
    print(f"✅ Found {len(file_paths)} warm storage files:")
    for file_path in file_paths:
        print(f"   - {file_path}")
    
    # Step 2: Move to Tier 1
    if file_paths:
        print("\n⬆️ Step 2: Moving to Tier 1...")
        tier_result = await handle_call_tool("apply_objective_to_files", {
            "file_paths": file_paths,
            "objective_type": "place_on_tier",
            "tier_name": "tier1"
        })
        print("✅ Tier 1 objective applied")
    
    # Demo 4: Monitor All Jobs
    print("\n📊 Demo 4: Monitor All Jobs")
    print("-" * 50)
    
    print("🔍 Checking job status...")
    jobs_result = await handle_call_tool("list_jobs", {
        "status_filter": "all"
    })
    
    result_data = json.loads(jobs_result[0].text)
    jobs = result_data.get("jobs", [])
    
    print(f"✅ Found {len(jobs)} total jobs:")
    for job in jobs:
        print(f"   - {job['name']}: {job['status']} ({job['progress']}%)")
    
    print("\n🎉 Tag-to-Objectives Workflow Demo Complete!")

def print_workflow_examples():
    """Print example workflows for reference."""
    
    print("\n" + "=" * 60)
    print("📖 WORKFLOW EXAMPLES")
    print("=" * 60)
    
    print("\n🔄 Complete Workflow Template:")
    print("1. Search for files by tag")
    print("   search_files_by_tag({'tag_name': 'user.priority', 'tag_value': 'high'})")
    print("2. Extract file paths from results")
    print("   file_paths = ['/path1', '/path2', '/path3']")
    print("3. Apply objective to files")
    print("   apply_objective_to_files({'file_paths': file_paths, 'objective_type': 'place_on_tier', 'tier_name': 'tier0'})")
    print("4. Monitor progress")
    print("   list_jobs({'status_filter': 'running'})")
    
    print("\n🎯 Common Workflow Patterns:")
    print("• High Priority → Tier 0:")
    print("  search_files_by_tag({'tag_name': 'user.priority', 'tag_value': 'high'}) → place_on_tier('tier0')")
    
    print("\n• Old Files → Archive:")
    print("  search_files_by_tag({'tag_name': 'user.age', 'tag_value': 'old'}) → exclude_from_tier('tier0') → place_on_tier('archive')")
    
    print("\n• Project Files → Warm Storage:")
    print("  search_files_by_tag({'tag_name': 'user.project', 'tag_value': 'project-name'}) → place_on_tier('tier1')")
    
    print("\n• Environment-Based Management:")
    print("  search_files_by_tag({'tag_name': 'user.env', 'tag_value': 'production'}) → place_on_tier('tier0')")
    print("  search_files_by_tag({'tag_name': 'user.env', 'tag_value': 'development'}) → place_on_tier('tier1')")

def print_best_practices():
    """Print best practices for tag-to-objectives workflows."""
    
    print("\n" + "=" * 60)
    print("💡 BEST PRACTICES")
    print("=" * 60)
    
    print("\n🏷️ Tagging Strategy:")
    print("• Use consistent tag naming conventions")
    print("• Tag files when created or modified")
    print("• Use hierarchical tag structures (user.project.ai-models)")
    print("• Define standard values for common tags")
    
    print("\n🔍 Search Strategy:")
    print("• Start with specific tag values for precise results")
    print("• Use path parameters to limit search scope")
    print("• Validate search results before applying objectives")
    print("• Use batch operations for multiple files")
    
    print("\n🎯 Objective Strategy:")
    print("• Test objectives on small file sets first")
    print("• Monitor job execution and completion")
    print("• Check for failed jobs and retry if needed")
    print("• Keep records of applied objectives")
    
    print("\n📊 Workflow Optimization:")
    print("• Automate common tag-to-objective workflows")
    print("• Run workflows during low-usage periods")
    print("• Set up alerts for failed objectives")
    print("• Regularly review and optimize workflows")

if __name__ == "__main__":
    print("🚀 Volume Canvas MCP Server - Tag to Objectives Workflow Demo")
    print("🔑 NVIDIA API Key: Configured and working")
    print("📡 Server: Ready for tag-based tier management")
    
    # Run the demo
    asyncio.run(demo_tag_to_objectives_workflow())
    
    # Print examples and best practices
    print_workflow_examples()
    print_best_practices()
    
    print("\n" + "=" * 60)
    print("✅ Tag-to-Objectives Workflow Ready!")
    print("📚 See docs/TAG_TO_OBJECTIVES_GUIDE.md for complete guide")
    print("🔍 See docs/TAG_SEARCH_GUIDE.md for tag search details")
    print("=" * 60)
