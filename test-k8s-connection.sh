#!/bin/bash
# Test script for Kubernetes cluster connection

set -e

echo "🔍 Testing Kubernetes Cluster Connection..."
echo "=========================================="

# Check if kubectl is configured
echo "1. Checking kubectl configuration..."
if kubectl config current-context >/dev/null 2>&1; then
    echo "✅ Current context: $(kubectl config current-context)"
else
    echo "❌ No kubectl context configured"
    echo "   Please configure kubectl first using the instructions in connect-to-k8s-cluster.md"
    exit 1
fi

# Test cluster connectivity
echo ""
echo "2. Testing cluster connectivity..."
if kubectl cluster-info >/dev/null 2>&1; then
    echo "✅ Cluster is accessible"
    kubectl cluster-info
else
    echo "❌ Cannot connect to cluster"
    echo "   Check your network connection and cluster configuration"
    exit 1
fi

# List nodes
echo ""
echo "3. Listing cluster nodes..."
if kubectl get nodes >/dev/null 2>&1; then
    echo "✅ Nodes accessible:"
    kubectl get nodes
else
    echo "❌ Cannot list nodes"
    echo "   Check your RBAC permissions"
    exit 1
fi

# Check permissions
echo ""
echo "4. Checking permissions..."
echo "   Can create jobs: $(kubectl auth can-i create jobs 2>/dev/null || echo 'No')"
echo "   Can list jobs: $(kubectl auth can-i list jobs 2>/dev/null || echo 'No')"
echo "   Can get pods: $(kubectl auth can-i get pods 2>/dev/null || echo 'No')"

# Test MCP server connectivity
echo ""
echo "5. Testing MCP server..."
if curl -s http://localhost:5002/health >/dev/null 2>&1; then
    echo "✅ Kubernetes MCP server is running on port 5002"
else
    echo "⚠️  Kubernetes MCP server not responding on port 5002"
    echo "   Make sure it's running: mcp-server-kubernetes --port 5002"
fi

echo ""
echo "🎉 Kubernetes connection test completed!"
echo "   Your cluster is ready for job submission via the MCP server."
