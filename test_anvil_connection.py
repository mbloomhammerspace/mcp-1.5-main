#!/usr/bin/env python3
"""
Test script to connect to the new Anvil API using the existing Hammerspace client.
"""

import sys
import asyncio
import json
from datetime import datetime

# Add the src directory to the path
sys.path.append('src')

from config import get_config
from hammerspace_client import HammerspaceClient

async def test_anvil_connection():
    """Test connection to the new Anvil API."""
    print("=" * 60)
    print("Testing Anvil API Connection")
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
        print(f"Timeout: {hammerspace_config.timeout}")
        print()
        
        # Test connection
        async with HammerspaceClient(hammerspace_config) as client:
            print("Testing connection...")
            
            try:
                # Try to get shares
                print("Attempting to get shares...")
                shares = await client.get_shares()
                print(f"✅ Successfully retrieved {len(shares)} shares")
                
                if shares:
                    print("\nShares found:")
                    for i, share in enumerate(shares, 1):
                        print(f"  {i}. {share.name} - {share.path}")
                        if hasattr(share, 'uuid'):
                            print(f"     UUID: {share.uuid}")
                        if hasattr(share, 'smb_aliases') and share.smb_aliases:
                            print(f"     SMB Aliases: {', '.join(share.smb_aliases)}")
                        print()
                else:
                    print("No shares found")
                
                # Save results
                results = {
                    "timestamp": datetime.now().isoformat(),
                    "anvil_host": "150.136.225.57",
                    "anvil_port": "8443",
                    "connection_successful": True,
                    "shares_count": len(shares),
                    "shares": [share.to_dict() if hasattr(share, 'to_dict') else str(share) for share in shares]
                }
                
                with open("anvil_connection_test_results.json", "w") as f:
                    json.dump(results, f, indent=2)
                
                print("✅ Results saved to anvil_connection_test_results.json")
                
            except Exception as e:
                print(f"❌ Error getting shares: {e}")
                
                # Try alternative endpoints
                print("\nTrying alternative approaches...")
                
                # Try to get system info or other endpoints
                try:
                    # This would need to be implemented in the client
                    print("Checking if client has other methods...")
                    print(f"Available methods: {[method for method in dir(client) if not method.startswith('_')]}")
                except Exception as e2:
                    print(f"Error in alternative approach: {e2}")
                
    except Exception as e:
        print(f"❌ Configuration or connection error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_anvil_connection())
        if success:
            print("\n✅ Connection test completed")
        else:
            print("\n❌ Connection test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
