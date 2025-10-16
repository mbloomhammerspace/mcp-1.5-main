#!/bin/bash
# Test a single question to the Web UI

echo "Testing: List all objectives for /mnt/se-lab/modelstore/gtc-demo-models/"

curl -s -X POST http://localhost:5000/api/clear

response=$(curl -s -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List all objectives for /mnt/se-lab/modelstore/gtc-demo-models/"}')

echo "$response" | jq -r '.response // .error'

