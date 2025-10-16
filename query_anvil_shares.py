#!/usr/bin/env python3
"""
Script to query the new Anvil API endpoint and discover available shares.
This will help update the mounts script with the correct share information.
"""

import asyncio
import aiohttp
import base64
import json
import sys
from typing import List, Dict, Any
from datetime import datetime

# Anvil API credentials
ANVIL_HOST = "150.136.225.57"
ANVIL_PORT = "8443"
ANVIL_USERNAME = "admin"
ANVIL_PASSWORD = "Passw0rd1"
ANVIL_BASE_URL = f"https://{ANVIL_HOST}:{ANVIL_PORT}"

class AnvilAPIClient:
    """Client for querying the Anvil API."""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = None
        
        # Create authentication headers
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification for self-signed certs
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers=self.auth_headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def test_connection(self) -> bool:
        """Test connection to the Anvil API."""
        try:
            print(f"Testing connection to {self.base_url}...")
            async with self.session.get(f"{self.base_url}/api/health") as response:
                if response.status == 200:
                    print("✅ Connection successful!")
                    return True
                else:
                    print(f"❌ Connection failed with status: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def get_shares(self) -> List[Dict[str, Any]]:
        """Get all available shares from the Anvil API."""
        shares = []
        
        # Try different possible endpoints for shares
        possible_endpoints = [
            "/api/shares",
            "/api/v1/shares", 
            "/shares",
            "/api/exports",
            "/api/v1/exports",
            "/exports",
            "/api/volumes",
            "/api/v1/volumes",
            "/volumes"
        ]
        
        for endpoint in possible_endpoints:
            try:
                print(f"Trying endpoint: {endpoint}")
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Found shares at {endpoint}")
                        print(f"Response: {json.dumps(data, indent=2)}")
                        
                        # Handle different response formats
                        if isinstance(data, list):
                            shares.extend(data)
                        elif isinstance(data, dict):
                            if 'shares' in data:
                                shares.extend(data['shares'])
                            elif 'exports' in data:
                                shares.extend(data['exports'])
                            elif 'volumes' in data:
                                shares.extend(data['volumes'])
                            else:
                                shares.append(data)
                        
                        break
                    elif response.status == 404:
                        print(f"❌ Endpoint not found: {endpoint}")
                    else:
                        print(f"❌ Endpoint failed with status {response.status}: {endpoint}")
                        
            except Exception as e:
                print(f"❌ Error accessing {endpoint}: {e}")
        
        return shares
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information from the Anvil API."""
        system_info = {}
        
        # Try different possible endpoints for system info
        possible_endpoints = [
            "/api/system",
            "/api/v1/system",
            "/api/info",
            "/api/v1/info",
            "/system",
            "/info"
        ]
        
        for endpoint in possible_endpoints:
            try:
                print(f"Trying system info endpoint: {endpoint}")
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Found system info at {endpoint}")
                        system_info = data
                        break
                    elif response.status == 404:
                        print(f"❌ System info endpoint not found: {endpoint}")
                    else:
                        print(f"❌ System info endpoint failed with status {response.status}: {endpoint}")
                        
            except Exception as e:
                print(f"❌ Error accessing system info {endpoint}: {e}")
        
        return system_info

async def main():
    """Main function to query Anvil API and discover shares."""
    print("=" * 60)
    print("Anvil API Share Discovery")
    print("=" * 60)
    print(f"Target: {ANVIL_BASE_URL}")
    print(f"Username: {ANVIL_USERNAME}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    async with AnvilAPIClient(ANVIL_BASE_URL, ANVIL_USERNAME, ANVIL_PASSWORD) as client:
        # Test connection
        if not await client.test_connection():
            print("Failed to connect to Anvil API. Exiting.")
            return
        
        print()
        
        # Get system information
        print("Getting system information...")
        system_info = await client.get_system_info()
        if system_info:
            print("System Information:")
            print(json.dumps(system_info, indent=2))
        print()
        
        # Get shares
        print("Discovering shares...")
        shares = await client.get_shares()
        
        if shares:
            print(f"✅ Found {len(shares)} shares:")
            print()
            
            for i, share in enumerate(shares, 1):
                print(f"Share {i}:")
                print(json.dumps(share, indent=2))
                print()
            
            # Save shares to file for mount script generation
            output_file = "anvil_shares_discovered.json"
            with open(output_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "anvil_host": ANVIL_HOST,
                    "anvil_port": ANVIL_PORT,
                    "shares": shares,
                    "system_info": system_info
                }, f, indent=2)
            
            print(f"✅ Shares saved to {output_file}")
            
        else:
            print("❌ No shares found or unable to access shares endpoint")
            print("This might indicate:")
            print("- Different API structure than expected")
            print("- Authentication issues")
            print("- API endpoints have changed")
            print("- No shares configured on the system")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
