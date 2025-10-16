#!/bin/bash
# Refresh NFS mounts for Anvil Hammerspace only
# This script handles stale file handles by remounting Anvil NFS shares

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="/home/ubuntu/mcp-1.5-main/logs/mount_refresh.log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to refresh a single mount
refresh_mount() {
    local mount_point=$1
    local nfs_server=$2
    local nfs_share=$3
    local mount_options=$4
    
    log_message "Refreshing mount: $mount_point"
    
    # Check if mount point exists
    if [ ! -d "$mount_point" ]; then
        log_message "  Creating mount point: $mount_point"
        sudo mkdir -p "$mount_point"
    fi
    
    # Check if already mounted
    if mountpoint -q "$mount_point" 2>/dev/null; then
        log_message "  Unmounting existing mount..."
        sudo umount -l "$mount_point" 2>/dev/null || true
        sleep 1
    fi
    
    # Mount with provided options
    log_message "  Mounting ${nfs_server}:${nfs_share} to $mount_point"
    if sudo mount -t nfs4 -o "$mount_options" "${nfs_server}:${nfs_share}" "$mount_point"; then
        log_message "  ✅ Successfully mounted $mount_point"
        return 0
    else
        log_message "  ❌ Failed to mount $mount_point"
        return 1
    fi
}

# Main refresh function
main() {
    log_message "=========================================="
    log_message "Starting Anvil Hammerspace NFS mount refresh"
    log_message "=========================================="
    
    # Anvil Hammerspace mounts (10.0.0.165 - private IP for 150.136.225.57:8443)
    ANVIL_SERVER="10.0.0.165"
    ANVIL_OPTIONS="vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys"
    
    log_message "Refreshing Anvil Hammerspace mounts..."
    
    # ✅ DISCOVERED SHARES: Root, Hub, Modelstore, Audio, Blueprint, K8s-tier0, Milvus, Upload, Video
    refresh_mount "/mnt/anvil/root" "$ANVIL_SERVER" "/" "$ANVIL_OPTIONS"
    refresh_mount "/mnt/anvil/hub" "$ANVIL_SERVER" "/hub" "$ANVIL_OPTIONS"
    refresh_mount "/mnt/anvil/modelstore" "$ANVIL_SERVER" "/modelstore" "$ANVIL_OPTIONS"
    refresh_mount "/mnt/anvil/audio" "$ANVIL_SERVER" "/audio" "$ANVIL_OPTIONS"
    refresh_mount "/mnt/anvil/blueprint" "$ANVIL_SERVER" "/blueprint" "$ANVIL_OPTIONS"
    refresh_mount "/mnt/anvil/k8s-tier0" "$ANVIL_SERVER" "/k8s-tier0" "$ANVIL_OPTIONS"
    refresh_mount "/mnt/anvil/milvus" "$ANVIL_SERVER" "/milvus" "$ANVIL_OPTIONS"
    refresh_mount "/mnt/anvil/upload" "$ANVIL_SERVER" "/upload" "$ANVIL_OPTIONS"
    refresh_mount "/mnt/anvil/video" "$ANVIL_SERVER" "/video" "$ANVIL_OPTIONS"
    
    log_message "✅ Anvil mounts refreshed successfully"
    
    log_message "=========================================="
    log_message "Mount refresh completed"
    log_message "=========================================="
    
    # Verify mounts
    echo -e "\n${GREEN}Current Anvil NFS mounts:${NC}"
    mount | grep -E "(anvil|10.0.0.165)" | grep nfs4
    
    echo -e "\n${GREEN}✅ Anvil mount refresh complete!${NC}"
}

# Run main function
main "$@"

