#!/bin/bash
# Test the inotify MCP tools via Web UI

echo "Testing inotify MCP tools via Web UI..."
echo "========================================"
echo ""

# Test 1: Start monitor
echo "Test 1: Start inotify monitor"
curl -s -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Start inotify monitor"}' | python3 -m json.tool
echo ""

sleep 2

# Test 2: Get status
echo "Test 2: Get monitor status"
curl -s -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Get inotify monitor status"}' | python3 -m json.tool
echo ""

sleep 2

# Test 3: Create a test file
echo "Test 3: Creating test file..."
TEST_FILE="/mnt/se-lab/upload/inotify-api-test-$(date +%s).txt"
echo "Test file created at $(date)" > "$TEST_FILE"
echo "Created: $TEST_FILE"
echo ""

# Wait for detection and processing
echo "Waiting 10 seconds for file detection and processing..."
sleep 10

# Test 4: Check if file was tagged
echo "Test 4: Verify tags were applied"
/home/mike/hs-mcp-1.0/.venv/bin/hs tag list "$TEST_FILE" | grep -E "ingestid|mimeid"
echo ""

# Test 5: Stop monitor
echo "Test 5: Stop inotify monitor"
curl -s -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Stop inotify monitor"}' | python3 -m json.tool
echo ""

echo "========================================"
echo "Testing complete!"

