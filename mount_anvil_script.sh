#!/bin/bash
# Mount script for Anvil Hammerspace system
# Target: 150.136.225.57:8443
# Username: admin
# Password: Passw0rd1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Anvil Hammerspace Mount Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Target: ${YELLOW}150.136.225.57:8443${NC}"
echo -e "Username: ${YELLOW}admin${NC}"
echo -e "Timestamp: $(date)${NC}"
echo

# Anvil server details
ANVIL_SERVER="10.0.0.165"  # Private IP (public IP: 150.136.225.57:8443)
ANVIL_PORT="8443"

# Standard NFS mount options for Hammerspace
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
    
    # Try to discover shares by attempting to mount common paths
    echo -e "${BLUE}Attempting to discover Anvil shares...${NC}"
    echo
    
    # Common share paths to try
    common_paths=(
        "/"
        "/data"
        "/exports"
        "/shares"
        "/root"
        "/home"
        "/models"
        "/uploads"
        "/hub"
        "/modelstore"
        "/tier0"
        "/audio"
    )
    
    discovered_shares=()
    
    for share_path in "${common_paths[@]}"; do
        mount_point="/mnt/anvil${share_path//\//_}"
        if [ "$share_path" = "/" ]; then
            mount_point="/mnt/anvil/root"
        fi
        
        echo -e "${BLUE}Trying to mount: $share_path${NC}"
        if mount_share "$share_path" "$mount_point" "Share at $share_path"; then
            discovered_shares+=("$share_path:$mount_point")
            echo -e "${GREEN}✅ Successfully discovered share: $share_path${NC}"
        else
            echo -e "${RED}❌ Failed to mount: $share_path${NC}"
        fi
        echo
    done
    
    if [ ${#discovered_shares[@]} -gt 0 ]; then
        echo -e "${GREEN}🎉 Discovered ${#discovered_shares[@]} shares:${NC}"
        for share in "${discovered_shares[@]}"; do
            echo -e "  ${GREEN}✅ $share${NC}"
        done
    else
        echo -e "${YELLOW}⚠️  No shares discovered with common paths${NC}"
        echo -e "${YELLOW}   You may need to:${NC}"
        echo -e "${YELLOW}   1. Check the web interface at https://150.136.225.57:8443${NC}"
        echo -e "${YELLOW}   2. Contact the system administrator${NC}"
        echo -e "${YELLOW}   3. Try different share paths${NC}"
    fi
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Mount Status Check${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Check current NFS mounts
    echo -e "${GREEN}Current NFS mounts:${NC}"
    mount | grep -E "(anvil|nfs4)" | grep -v nfsd || echo "No NFS mounts found"
    
    echo
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Next Steps${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "1. Install HSTK CLI to discover actual shares:"
    echo -e "   ${YELLOW}sudo apt install hstk-cli${NC}"
    echo -e "2. Configure HSTK CLI with Anvil credentials:"
    echo -e "   ${YELLOW}hs config set anvil 150.136.225.57:8443 admin Passw0rd1${NC}"
    echo -e "3. List available shares:"
    echo -e "   ${YELLOW}hs share list${NC}"
    echo -e "4. Update this script with actual share paths"
    echo -e "5. Re-run this script to mount the shares"
    echo
}

# Run main function
main

echo -e "${GREEN}Anvil mount script completed!${NC}"
