#!/bin/bash
# Mount script for Anvil Hammerspace system only
# Target: 10.0.0.165 (private IP for 150.136.225.57:8443)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Anvil Hammerspace Mount Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Target: ${YELLOW}10.0.0.165${NC} (private IP for 150.136.225.57:8443)"
echo -e "Timestamp: $(date)${NC}"
echo

# Anvil server details
ANVIL_SERVER="10.0.0.165"
NFS_OPTIONS="vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys"

# Function to create mount point
create_mount_point() {
    local mount_point=$1
    if [ ! -d "$mount_point" ]; then
        echo -e "${YELLOW}Creating mount point: $mount_point${NC}"
        sudo mkdir -p "$mount_point"
    else
        echo -e "${GREEN}Mount point exists: $mount_point${NC}"
    fi
}

# Function to mount a share
mount_share() {
    local share_path=$1
    local mount_point=$2
    local description=$3
    
    echo -e "${BLUE}Mounting: $description${NC}"
    echo -e "  Share: ${YELLOW}$share_path${NC}"
    echo -e "  Mount Point: ${YELLOW}$mount_point${NC}"
    
    create_mount_point "$mount_point"
    
    # Check if already mounted
    if mountpoint -q "$mount_point" 2>/dev/null; then
        echo -e "  ${YELLOW}Already mounted, unmounting first...${NC}"
        sudo umount -l "$mount_point" 2>/dev/null || true
        sleep 1
    fi
    
    # Attempt to mount
    if sudo mount -t nfs4 -o "$NFS_OPTIONS" "${ANVIL_SERVER}:${share_path}" "$mount_point"; then
        echo -e "  ${GREEN}✅ Successfully mounted${NC}"
        return 0
    else
        echo -e "  ${RED}❌ Failed to mount${NC}"
        return 1
    fi
}

# Main mounting logic
main() {
    echo -e "${BLUE}Starting Anvil Hammerspace mounts...${NC}"
    echo
    
    # Create base mount directory
    create_mount_point "/mnt/anvil"
    
    # Mount all discovered Anvil shares
    echo -e "${BLUE}Mounting discovered Anvil shares...${NC}"
    echo
    
    # Discovered shares
    mount_share "/" "/mnt/anvil/root" "Root share"
    mount_share "/hub" "/mnt/anvil/hub" "Hub share"
    mount_share "/modelstore" "/mnt/anvil/modelstore" "Modelstore share"
    mount_share "/audio" "/mnt/anvil/audio" "Audio share"
    mount_share "/blueprint" "/mnt/anvil/blueprint" "Blueprint share"
    mount_share "/k8s-tier0" "/mnt/anvil/k8s-tier0" "K8s-tier0 share"
    mount_share "/milvus" "/mnt/anvil/milvus" "Milvus share"
    mount_share "/upload" "/mnt/anvil/upload" "Upload share"
    mount_share "/video" "/mnt/anvil/video" "Video share"
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Mount Status Check${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Check current NFS mounts
    echo -e "${GREEN}Current Anvil NFS mounts:${NC}"
    mount | grep -E "(anvil|10\.0\.0\.165)" | grep nfs4 || echo "No Anvil NFS mounts found"
    
    echo
    echo -e "${GREEN}✅ Anvil mount script completed!${NC}"
}

# Run main function
main
