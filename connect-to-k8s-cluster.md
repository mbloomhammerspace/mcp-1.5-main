# Connecting to Your Existing Kubernetes Cluster

## Prerequisites
- Your Kubernetes cluster is accessible from this machine
- You have the cluster's connection details (API server URL, certificates, etc.)

## Connection Methods

### Method 1: Using kubeconfig file (Recommended)
If you have a kubeconfig file from your cluster administrator:

```bash
# Copy your kubeconfig file to the standard location
cp /path/to/your/kubeconfig ~/.kube/config

# Or set the KUBECONFIG environment variable
export KUBECONFIG=/path/to/your/kubeconfig

# Verify connection
kubectl cluster-info
kubectl get nodes
```

### Method 2: Manual cluster configuration
If you need to configure the cluster manually:

```bash
# Set the cluster endpoint
kubectl config set-cluster my-cluster --server=https://YOUR_CLUSTER_IP:6443

# Set credentials (choose one method below)
# Option A: Using certificates
kubectl config set-credentials my-user --client-certificate=/path/to/client.crt --client-key=/path/to/client.key

# Option B: Using token
kubectl config set-credentials my-user --token=YOUR_TOKEN

# Option C: Using username/password
kubectl config set-credentials my-user --username=YOUR_USERNAME --password=YOUR_PASSWORD

# Create context
kubectl config set-context my-context --cluster=my-cluster --user=my-user

# Use the context
kubectl config use-context my-context
```

### Method 3: Using cloud provider CLI tools
If your cluster is on a cloud provider:

#### AWS EKS
```bash
# Install AWS CLI and eksctl
aws configure  # Set your AWS credentials
eksctl get cluster  # List clusters
aws eks update-kubeconfig --region REGION --name CLUSTER_NAME
```

#### Google GKE
```bash
# Install gcloud CLI
gcloud auth login
gcloud container clusters get-credentials CLUSTER_NAME --zone ZONE --project PROJECT_ID
```

#### Azure AKS
```bash
# Install Azure CLI
az login
az aks get-credentials --resource-group RESOURCE_GROUP --name CLUSTER_NAME
```

## Testing the Connection

Once connected, test with these commands:

```bash
# Check cluster info
kubectl cluster-info

# List nodes
kubectl get nodes

# List namespaces
kubectl get namespaces

# Check if you can create resources
kubectl auth can-i create jobs
kubectl auth can-i create deployments
```

## Configuring the Kubernetes MCP Server

After connecting to your cluster, the MCP server will automatically use the current kubectl context:

```bash
# Verify the MCP server can access your cluster
curl -s http://localhost:5002/health

# Test job creation (if you have permissions)
kubectl apply -f k8s-mcp-job-example.yaml
```

## Security Considerations

1. **RBAC Permissions**: Ensure your user/service account has the necessary permissions:
   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: ClusterRole
   metadata:
     name: mcp-server-role
   rules:
   - apiGroups: ["batch"]
     resources: ["jobs"]
     verbs: ["get", "list", "create", "delete", "watch"]
   - apiGroups: [""]
     resources: ["pods", "pods/log"]
     verbs: ["get", "list", "watch"]
   ```

2. **Network Security**: Ensure the cluster API server is accessible from this machine
3. **Certificate Validation**: Verify SSL certificates are properly configured

## Troubleshooting

### Common Issues:
1. **Connection refused**: Check if the API server is accessible
2. **Unauthorized**: Verify credentials and RBAC permissions
3. **Certificate errors**: Check SSL certificate configuration
4. **Context not found**: Ensure the correct context is set

### Debug Commands:
```bash
# Check current context
kubectl config current-context

# View full kubeconfig
kubectl config view

# Test API server connectivity
curl -k https://YOUR_CLUSTER_IP:6443/version

# Check authentication
kubectl auth can-i --list
```

## Next Steps
1. Connect to your cluster using one of the methods above
2. Test the connection with `kubectl get nodes`
3. Verify the MCP server can access the cluster
4. Start submitting jobs to your cluster!
