#!/usr/bin/env python3
"""
Comprehensive script to discover the Anvil API endpoints and structure.
"""

import sys
import asyncio
import json
from datetime import datetime

# Add the src directory to the path
sys.path.append('src')

from config import get_config
from hammerspace_client import HammerspaceClient

async def discover_anvil_api():
    """Discover the Anvil API structure and available endpoints."""
    print("=" * 60)
    print("Anvil API Discovery")
    print("=" * 60)
    
    try:
        # Load configuration
        config_manager = get_config()
        config_manager.load_config()
        
        # Get Hammerspace configuration
        hammerspace_config = config_manager.get_hammerspace_config()
        
        print(f"Base URL: {hammerspace_config.base_url}")
        print(f"Username: {hammerspace_config.username}")
        print(f"Verify SSL: {hammerspace_config.verify_ssl}")
        print()
        
        # Test connection with various endpoints
        async with HammerspaceClient(hammerspace_config) as client:
            print("Testing various API endpoints...")
            
            # List of methods to try
            methods_to_test = [
                ("get_nodes", "Get nodes"),
                ("get_storage_volumes", "Get storage volumes"),
                ("get_object_storage_volumes", "Get object storage volumes"),
                ("get_objectives", "Get objectives"),
                ("get_objective_templates", "Get objective templates"),
                ("get_tasks", "Get tasks"),
                ("get_data_movement_jobs", "Get data movement jobs"),
            ]
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "anvil_host": "150.136.225.57",
                "anvil_port": "8443",
                "base_url": hammerspace_config.base_url,
                "endpoints_tested": {},
                "successful_endpoints": [],
                "failed_endpoints": []
            }
            
            for method_name, description in methods_to_test:
                print(f"\nTesting {method_name}: {description}")
                try:
                    method = getattr(client, method_name)
                    result = await method()
                    
                    if result:
                        print(f"✅ {method_name}: Success - {len(result) if isinstance(result, list) else 'Data returned'}")
                        results["successful_endpoints"].append(method_name)
                        results["endpoints_tested"][method_name] = {
                            "success": True,
                            "result_type": type(result).__name__,
                            "result_count": len(result) if isinstance(result, list) else 1,
                            "sample_data": str(result[0]) if isinstance(result, list) and len(result) > 0 else str(result)
                        }
                        
                        # If we got nodes, try to get more details
                        if method_name == "get_nodes" and result:
                            print(f"  Found {len(result)} nodes")
                            for node in result[:3]:  # Show first 3 nodes
                                print(f"    - {node.name if hasattr(node, 'name') else node}")
                        
                        # If we got storage volumes, try to get more details
                        elif method_name == "get_storage_volumes" and result:
                            print(f"  Found {len(result)} storage volumes")
                            for volume in result[:3]:  # Show first 3 volumes
                                print(f"    - {volume.name if hasattr(volume, 'name') else volume}")
                        
                        # If we got objectives, try to get more details
                        elif method_name == "get_objectives" and result:
                            print(f"  Found {len(result)} objectives")
                            for objective in result[:3]:  # Show first 3 objectives
                                print(f"    - {objective.name if hasattr(objective, 'name') else objective}")
                    
                    else:
                        print(f"⚠️  {method_name}: No data returned")
                        results["endpoints_tested"][method_name] = {
                            "success": True,
                            "result_type": "empty",
                            "result_count": 0,
                            "sample_data": "No data returned"
                        }
                        
                except Exception as e:
                    print(f"❌ {method_name}: Failed - {e}")
                    results["failed_endpoints"].append(method_name)
                    results["endpoints_tested"][method_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Try to get shares using different approaches
            print(f"\nTrying alternative share discovery methods...")
            
            # Try to get a specific share if we know any share names
            try:
                # This might work if there are default shares
                share = await client.get_share("/")
                if share:
                    print(f"✅ Found root share: {share}")
                    results["root_share"] = str(share)
            except Exception as e:
                print(f"❌ Could not get root share: {e}")
            
            # Save results
            with open("anvil_api_discovery_results.json", "w") as f:
                json.dump(results, f, indent=2)
            
            print(f"\n✅ Discovery results saved to anvil_api_discovery_results.json")
            
            # Summary
            print(f"\n" + "=" * 60)
            print("DISCOVERY SUMMARY")
            print("=" * 60)
            print(f"Successful endpoints: {len(results['successful_endpoints'])}")
            print(f"Failed endpoints: {len(results['failed_endpoints'])}")
            
            if results["successful_endpoints"]:
                print(f"\nWorking endpoints:")
                for endpoint in results["successful_endpoints"]:
                    print(f"  ✅ {endpoint}")
            
            if results["failed_endpoints"]:
                print(f"\nFailed endpoints:")
                for endpoint in results["failed_endpoints"]:
                    print(f"  ❌ {endpoint}")
                
    except Exception as e:
        print(f"❌ Discovery error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(discover_anvil_api())
        if success:
            print("\n✅ API discovery completed")
        else:
            print("\n❌ API discovery failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
