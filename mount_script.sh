#!/bin/bash
# Manual mount script for Hammerspace NFS shares
# Use this if you prefer manual mounting over fstab

# Create mount points
sudo mkdir -p /mnt/hammerspace
sudo mkdir -p /mnt/production/{root,MLPerf,smbnfs_example,nfs4_2,opmtesting}
sudo mkdir -p /mnt/se-lab/{root,Milvuss3,modelstore,upload,audio,hub,tier0}
sudo mkdir -p /mnt/anvil/{root,hub,modelstore,audio,blueprint,k8s-tier0,milvus,upload,video}

# Mount Production Hammerspace (10.200.10.120)
sudo mount -t nfs4 -o vers=4.2,rsize=1048576,wsize=1048576,namlen=255,hard,proto=tcp,timeo=600,retrans=2,sec=sys 10.200.10.120:/bloom /mnt/hammerspace
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.200.10.120:/ /mnt/production/root
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.200.10.120:/MLPerf /mnt/production/MLPerf
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.200.10.120:/smbnfs_example /mnt/production/smbnfs_example
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.200.10.120:/nfs4_2 /mnt/production/nfs4_2
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.200.10.120:/opmtesting /mnt/production/opmtesting

# Mount SE Lab Hammerspace (10.200.120.90) - Primary target for MCP operations
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.200.120.90:/ /mnt/se-lab/root
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.200.120.90:/Milvuss3 /mnt/se-lab/Milvuss3
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.200.120.90:/modelstore /mnt/se-lab/modelstore
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.200.120.90:/upload /mnt/se-lab/upload
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.200.120.90:/audio /mnt/se-lab/audio
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.200.120.90:/hub /mnt/se-lab/hub
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.200.120.90:/tier0 /mnt/se-lab/tier0

# Mount Anvil Hammerspace (10.0.0.165 - private IP for 150.136.225.57:8443)
# ✅ DISCOVERED SHARES: Root, Hub, Modelstore, Audio, Blueprint, K8s-tier0, Milvus, Upload, Video
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.0.0.165:/ /mnt/anvil/root
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.0.0.165:/hub /mnt/anvil/hub
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.0.0.165:/modelstore /mnt/anvil/modelstore
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.0.0.165:/audio /mnt/anvil/audio
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.0.0.165:/blueprint /mnt/anvil/blueprint
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.0.0.165:/k8s-tier0 /mnt/anvil/k8s-tier0
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.0.0.165:/milvus /mnt/anvil/milvus
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.0.0.165:/upload /mnt/anvil/upload
sudo mount -t nfs4 -o vers=4.2,rsize=8192,wsize=8192,namlen=255,hard,proto=tcp,timeo=14,retrans=2,sec=sys 10.0.0.165:/video /mnt/anvil/video

echo "All Hammerspace NFS mounts completed!"
echo "Checking mount status..."
mount | grep -E "(se-lab|hammerspace|anvil|nfs)" | grep -v nfsd
