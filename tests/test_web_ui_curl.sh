#!/bin/bash
# Test Web UI using pure curl commands
# This provides a simple, dependency-free way to test the Web UI

set -e

WEB_UI_URL="http://localhost:5000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}WEB UI CURL TEST SUITE${NC}"
echo -e "${BLUE}======================================${NC}\n"

# Test 1: Server health
echo -e "${YELLOW}Test 1: Server Health Check${NC}"
if curl -s -o /dev/null -w "%{http_code}" "$WEB_UI_URL" | grep -q "200"; then
    echo -e "${GREEN}✅ Server is running${NC}\n"
else
    echo -e "${RED}❌ Server is not running${NC}\n"
    exit 1
fi

# Test 2: Tools endpoint
echo -e "${YELLOW}Test 2: MCP Tools Endpoint${NC}"
TOOLS_RESPONSE=$(curl -s "$WEB_UI_URL/api/tools")
TOOLS_COUNT=$(echo "$TOOLS_RESPONSE" | grep -o '"name"' | wc -l)
if [ "$TOOLS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Tools endpoint working - $TOOLS_COUNT tools available${NC}\n"
else
    echo -e "${RED}❌ Tools endpoint failed${NC}\n"
    exit 1
fi

# Clear chat
echo -e "${YELLOW}Clearing chat history...${NC}"
curl -s -X POST "$WEB_UI_URL/api/clear" > /dev/null
echo -e "${GREEN}✅ Chat cleared${NC}\n"

# Test questions
declare -a questions=(
    "Promote all GTC tagged objects to tier0"
    "Check alignment status of files tagged with modelsetid=hs-GTC-0002"
    "Tag all files in /mnt/se-lab/modelstore/new-models/ as modelsetid=hs-GTC-0003"
    "Apply placeonvolumes objective to /mnt/se-lab/modelstore/gtc-demo-models/"
    "List all objectives for /mnt/se-lab/modelstore/gtc-demo-models/"
    "Refresh Hammerspace mounts"
)

test_num=3
passed=0
failed=0

for question in "${questions[@]}"; do
    echo -e "${YELLOW}Test $test_num: '$question'${NC}"
    
    # Send question to API
    RESPONSE=$(curl -s -X POST "$WEB_UI_URL/api/chat" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$question\"}" \
        -w "\nHTTP_STATUS:%{http_code}")
    
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d':' -f2)
    RESPONSE_BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')
    
    if [ "$HTTP_STATUS" = "200" ]; then
        # Check if response contains actual API errors (not Claude mentioning errors)
        if echo "$RESPONSE_BODY" | jq -r '.error' 2>/dev/null | grep -q "API\|Exception\|TaskGroup"; then
            echo -e "${RED}❌ Response contains errors${NC}"
            echo "$RESPONSE_BODY" | jq -r '.error' 2>/dev/null
            ((failed++))
        else
            echo -e "${GREEN}✅ Question processed successfully${NC}"
            echo "$RESPONSE_BODY" | jq -r '.response' 2>/dev/null | head -5 || echo "$RESPONSE_BODY" | head -3
            ((passed++))
        fi
    else
        echo -e "${RED}❌ HTTP status code: $HTTP_STATUS${NC}"
        echo "$RESPONSE_BODY" | head -3
        ((failed++))
    fi
    
    echo ""
    ((test_num++))
    
    # Wait between requests
    sleep 2
done

# Summary
total=$((passed + failed))
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "Total Tests: $total"
echo -e "${GREEN}Passed: $passed${NC}"
echo -e "${RED}Failed: $failed${NC}"
echo -e "Success Rate: $(awk "BEGIN {printf \"%.1f\", ($passed/$total)*100}")%\n"

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi

