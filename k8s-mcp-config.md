# Kubernetes MCP Server Configuration Guide

## Current Setup
- **Kubernetes MCP Server**: Running on port 5002
- **Kubernetes Cluster**: Minikube (v1.34.0)
- **Status**: ✅ Ready to manage jobs

## How to Use the Kubernetes MCP Server

### 1. Direct Job Management via kubectl
The MCP server can manage jobs through standard Kubernetes API calls:

```bash
# Create a job
kubectl apply -f k8s-mcp-job-example.yaml

# Check job status
kubectl get jobs

# View job logs
kubectl logs job/mcp-managed-job

# Delete a job
kubectl delete job mcp-managed-job
```

### 2. MCP Server Integration
The Kubernetes MCP server provides tools for:
- Creating and managing Kubernetes jobs
- Monitoring job status
- Viewing job logs
- Managing deployments, services, and other resources

### 3. Example Job Types You Can Run

#### Simple Batch Job
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: simple-job
spec:
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ["echo", "Hello World"]
      restartPolicy: Never
```

#### Data Processing Job
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-processor
spec:
  template:
    spec:
      containers:
      - name: processor
        image: python:3.9
        command: ["python", "-c"]
        args: ["print('Processing data...')"]
      restartPolicy: Never
```

#### ML Training Job
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: ml-training
spec:
  template:
    spec:
      containers:
      - name: trainer
        image: tensorflow/tensorflow:latest
        command: ["python", "-c"]
        args: ["print('Training ML model...')"]
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      restartPolicy: Never
```

## Next Steps
1. Test the MCP server with the example job
2. Configure authentication if needed
3. Set up monitoring and logging
4. Create custom job templates for your use cases
