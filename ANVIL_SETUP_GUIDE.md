# Anvil Hammerspace Setup Guide

## Overview

This document provides information about setting up and configuring the new Anvil Hammerspace system at `150.136.225.57:8443`.

## System Information

- **Host**: 150.136.225.57
- **Port**: 8443
- **Protocol**: HTTPS (self-signed certificate)
- **Username**: admin
- **Password**: Passw0rd1
- **Web Interface**: https://150.136.225.57:8443

## Current Status

### ✅ What's Working
- **Connection**: Successfully connects to the Anvil system
- **Authentication**: Basic authentication works with provided credentials
- **Web Interface**: Accessible at https://150.136.225.57:8443
- **SSL**: Self-signed certificate (SSL verification disabled for API calls)

### ❌ What's Not Working
- **REST API Endpoints**: All standard Hammerspace API endpoints return 404
  - `/api/shares` - 404 Not Found
  - `/api/nodes` - 404 Not Found
  - `/api/storage-volumes` - 404 Not Found
  - `/api/objectives` - 404 Not Found
  - `/api/tasks` - 404 Not Found
- **HSTK CLI**: Not installed on the system
- **Share Discovery**: Unable to discover available shares

## Possible Reasons for API Issues

1. **New Installation**: The system might be freshly installed and not fully configured
2. **Different API Version**: The API structure might be different from the expected format
3. **API Not Enabled**: The REST API might not be enabled or configured
4. **Different Endpoint Structure**: The API might use different paths or versions

## Next Steps

### 1. Install HSTK CLI

The HSTK CLI is the recommended way to interact with Hammerspace systems, but it's **not available through standard package managers**:

```bash
# HSTK CLI is NOT available via apt - this was incorrect
# sudo apt install hstk-cli  # ❌ This will NOT work

# Correct methods:
# 1. Download from Hammerspace support portal
# 2. Contact Hammerspace support for the installer
# 3. Check if it's already installed on the system
```

### 2. Understanding HSTK CLI

**Important**: The HSTK CLI (`hs` command) is designed to work with **mounted Hammerspace filesystems**, not to connect to remote API endpoints. It operates on local NFS mounts.

```bash
# HSTK CLI works on mounted filesystems, not remote connections
# You need to mount the Anvil shares first, then use hs commands

# Example usage (after mounting):
cd /mnt/anvil/root  # Navigate to a mounted Hammerspace directory
hs dump volumes      # List volumes
hs tag list          # List tags
hs status collections # Check collections
```

### 3. Discover Shares

Since the HSTK CLI works on mounted filesystems, we need to discover shares through other means:

**Option A: Use the Web Interface**
1. Log into https://150.136.225.57:8443
2. Navigate to the shares/exports section
3. Note the available share paths

**Option B: Try Common Share Paths**
```bash
# Try mounting common share paths
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 150.136.225.57:/ /mnt/anvil/root
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 150.136.225.57:/data /mnt/anvil/data
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 150.136.225.57:/exports /mnt/anvil/exports
```

**Option C: Contact System Administrator**
- Ask for the available share paths
- Get documentation about the Anvil system configuration

### 4. Update Mount Script

Once shares are discovered, update the `mount_anvil_script.sh` file with the actual share paths:

```bash
# Edit the mount script
nano mount_anvil_script.sh

# Uncomment and update the mount_share lines with actual paths
# Example:
# mount_share "/actual-share-path" "/mnt/anvil/actual-share" "Actual Share Description"
```

### 5. Test Mounts

```bash
# Run the updated mount script
./mount_anvil_script.sh

# Verify mounts
mount | grep anvil
```

## Configuration Files Created

### 1. Anvil Configuration
- **File**: `config/anvil_config.yaml`
- **Purpose**: Stores Anvil API configuration
- **Status**: ✅ Created

### 2. Active Configuration
- **File**: `config/active_hammerspace.txt`
- **Purpose**: Points to the active Hammerspace configuration
- **Status**: ✅ Created

### 3. Main Configuration
- **File**: `config/config.yaml`
- **Purpose**: Main configuration file with Anvil settings
- **Status**: ✅ Created

### 4. Mount Script
- **File**: `mount_anvil_script.sh`
- **Purpose**: Script to mount Anvil shares
- **Status**: ✅ Created (needs share paths)

## API Discovery Results

The following endpoints were tested and all returned 404:

- `GET /api/shares`
- `GET /api/nodes`
- `GET /api/storage-volumes`
- `GET /api/object-storage-volumes`
- `GET /api/objectives`
- `GET /api/objective-templates`
- `GET /api/tasks`
- `GET /api/data-movement/jobs`

## Troubleshooting

### If HSTK CLI Installation Fails

1. **Check if HSTK CLI is already installed**:
   ```bash
   # Check for existing installation
   which hs
   which hstk
   which hstk-cli
   
   # Check system info
   cat /etc/os-release
   uname -m
   ```

2. **Contact Hammerspace Support**:
   - Request HSTK CLI installer for your specific system
   - Ask for API documentation for your Anvil version
   - Get access to the Hammerspace support portal

### If API Endpoints Still Don't Work

1. **Check API Version**:
   ```bash
   # Try different API versions
   curl -k -u admin:Passw0rd1 https://150.136.225.57:8443/api/v2/shares
   curl -k -u admin:Passw0rd1 https://150.136.225.57:8443/rest/api/shares
   ```

2. **Check Web Interface**:
   - Log into https://150.136.225.57:8443
   - Look for API documentation or endpoint information
   - Check if there's a different API structure

### If Mounts Fail

1. **Check NFS Service**:
   ```bash
   # Check if NFS client is installed
   which mount.nfs4
   
   # Install if missing
   sudo apt install nfs-common
   ```

2. **Check Network Connectivity**:
   ```bash
   # Test NFS connectivity
   telnet 150.136.225.57 2049
   ```

## Files Created

1. `query_anvil_shares.py` - Python script to query Anvil API
2. `test_anvil_connection.py` - Test script for Anvil connection
3. `discover_anvil_api.py` - Comprehensive API discovery script
4. `mount_anvil_script.sh` - Mount script for Anvil shares
5. `config/anvil_config.yaml` - Anvil configuration
6. `config/active_hammerspace.txt` - Active configuration pointer
7. `config/config.yaml` - Main configuration file
8. `ANVIL_SETUP_GUIDE.md` - This documentation

## Summary

The Anvil system is accessible and authenticates successfully, but the REST API endpoints are not responding as expected. This is likely due to:

1. The system being a new installation
2. Different API structure than expected
3. Need for HSTK CLI instead of direct API access

The next step is to install and configure the HSTK CLI to discover the actual shares and update the mount script accordingly.

## Contact Information

For additional support:
- Hammerspace Support Portal
- System Administrator
- Documentation: Check the web interface at https://150.136.225.57:8443
