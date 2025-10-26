#!/usr/bin/env python3
"""
Purge case-101* directories from file monitor tracking
This script will clean up the in-memory tracking for deleted case-101* directories
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def get_all_case_101_directories():
    """Get all case-101* directories that might be tracked"""
    case_dirs = []
    
    # Check if any case-101* directories exist in the hub
    hub_path = "/mnt/anvil/hub"
    if os.path.exists(hub_path):
        try:
            items = os.listdir(hub_path)
            case_dirs = [item for item in items if item.startswith('case-101')]
        except Exception as e:
            print(f"❌ Error reading hub directory: {e}")
    
    return case_dirs

def check_hammerspace_tags():
    """Check if there are any Hammerspace tags for case-101* directories"""
    print("🔍 Checking for Hammerspace tags on case-101* directories...")
    
    # Get all case-101* directories that might have tags
    case_dirs = get_all_case_101_directories()
    
    if not case_dirs:
        print("✅ No case-101* directories found in hub - they've been deleted")
        return []
    
    tagged_dirs = []
    for case_dir in case_dirs:
        case_path = f"/mnt/anvil/hub/{case_dir}"
        try:
            # Check if directory has any tags
            cmd = ['/home/ubuntu/.local/bin/hs', 'tag', 'list', case_path]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd="/mnt/anvil/hub")
            
            if "TAGS_TABLE{}" not in result.stdout:
                print(f"📋 Found tags on {case_dir}:")
                print(f"   {result.stdout.strip()}")
                tagged_dirs.append(case_dir)
            else:
                print(f"✅ No tags on {case_dir}")
                
        except Exception as e:
            print(f"❌ Error checking tags for {case_dir}: {e}")
    
    return tagged_dirs

def remove_hammerspace_tags(case_dirs):
    """Remove all Hammerspace tags from case-101* directories"""
    if not case_dirs:
        print("✅ No tagged case-101* directories to clean up")
        return
    
    print(f"🧹 Removing tags from {len(case_dirs)} case-101* directories...")
    
    for case_dir in case_dirs:
        case_path = f"/mnt/anvil/hub/{case_dir}"
        try:
            # Remove all tags from the directory
            cmd = ['/home/ubuntu/.local/bin/hs', 'tag', 'remove', '-r', case_path]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd="/mnt/anvil/hub")
            
            if result.returncode == 0:
                print(f"✅ Removed tags from {case_dir}")
            else:
                print(f"❌ Failed to remove tags from {case_dir}: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error removing tags from {case_dir}: {e}")

def restart_file_monitor():
    """Restart the file monitor to clear in-memory tracking"""
    print("🔄 Restarting file monitor to clear in-memory tracking...")
    
    try:
        # Stop the file monitor
        print("🛑 Stopping file monitor...")
        subprocess.run(['./start_all_services.sh', 'stop'], check=True)
        time.sleep(2)
        
        # Start the file monitor
        print("🚀 Starting file monitor...")
        subprocess.run(['./start_all_services.sh', 'start'], check=True)
        time.sleep(5)
        
        print("✅ File monitor restarted successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error restarting file monitor: {e}")
        return False
    
    return True

def main():
    """Main cleanup function"""
    print("🧹 Purging case-101* directories from file monitor tracking")
    print("=" * 60)
    
    # Step 1: Check what case-101* directories exist
    print("\n📋 Step 1: Checking for case-101* directories...")
    case_dirs = get_all_case_101_directories()
    
    if case_dirs:
        print(f"Found {len(case_dirs)} case-101* directories:")
        for case_dir in case_dirs:
            print(f"  - {case_dir}")
    else:
        print("✅ No case-101* directories found in hub")
    
    # Step 2: Check for Hammerspace tags
    print("\n📋 Step 2: Checking for Hammerspace tags...")
    tagged_dirs = check_hammerspace_tags()
    
    # Step 3: Remove tags if any exist
    if tagged_dirs:
        print(f"\n🧹 Step 3: Removing tags from {len(tagged_dirs)} directories...")
        remove_hammerspace_tags(tagged_dirs)
    else:
        print("\n✅ Step 3: No tags to remove")
    
    # Step 4: Restart file monitor to clear memory
    print("\n🔄 Step 4: Restarting file monitor to clear in-memory tracking...")
    if restart_file_monitor():
        print("\n✅ Cleanup complete! File monitor has been restarted and should no longer try to promote deleted case-101* directories.")
    else:
        print("\n❌ Cleanup failed - please manually restart the file monitor")
    
    print("\n" + "=" * 60)
    print("🎉 Case-101* directory purge complete!")

if __name__ == "__main__":
    main()
