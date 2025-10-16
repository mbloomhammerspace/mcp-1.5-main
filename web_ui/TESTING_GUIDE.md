# Web UI Testing Guide

## Quick Start

### Start the Web UI
```bash
cd /home/mike/mcp-1.5/web_ui
source ../venv/bin/activate
python app.py
```

### Access the UI
Open your browser: http://localhost:5000

## Running Tests

### Option 1: Curl Script (Fast, No Dependencies)
```bash
cd /home/mike/mcp-1.5
./tests/test_web_ui_curl.sh
```

### Option 2: Python Test Suite (More Detailed)
```bash
cd /home/mike/mcp-1.5
source venv/bin/activate
python tests/test_web_ui.py
```

### Option 3: Single Question Test
```bash
./tests/test_single_question.sh
```

## Important Notes

### Conversation State
The web UI currently starts each conversation fresh to avoid Claude API tool_result errors. This means:
- ✅ Each question is independent and works reliably
- ⚠️ No conversation context between questions
- 💡 Click "Clear Chat" in the UI between complex multi-step operations

### Test Results Summary

**Working Features:**
- ✅ Server health check
- ✅ MCP tools endpoint (19 tools)
- ✅ Single question processing
- ✅ Tool execution and results

**Expected Behavior:**
- Each question should be asked independently
- Click "Clear Chat" between questions for best results
- Responses appear in 5-15 seconds depending on complexity

## Example Test Flow

```bash
# 1. Clear chat
curl -X POST http://localhost:5000/api/clear

# 2. Ask a question
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List all objectives for /mnt/se-lab/modelstore/gtc-demo-models/"}'

# 3. Clear chat before next question
curl -X POST http://localhost:5000/api/clear

# 4. Ask another question
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Check alignment status of files tagged with modelsetid=hs-GTC-0002"}'
```

## Troubleshooting

### Server Won't Start
```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill existing processes
pkill -f "python.*app.py"

# Check logs
tail -f /home/mike/mcp-1.5/logs/web_ui.log
```

### API Errors
```bash
# Verify Anthropic API key
grep ANTHROPIC_API_KEY /home/mike/mcp-1.5/.env

# Test API connectivity
curl -I https://api.anthropic.com/v1/messages
```

### MCP Tools Not Working
```bash
# Test MCP server directly
cd /home/mike/mcp-1.5
source venv/bin/activate
python tmp/promote_gtc_to_tier0_mcp.py
```

## Performance Tips

1. **Response Time**: 5-15 seconds per question (includes Claude AI + MCP tool execution)
2. **Clear Chat**: Always clear between independent questions
3. **Complex Operations**: Break into smaller steps if needed
4. **Network**: Ensure stable connection to api.anthropic.com

## Known Limitations

1. **No Conversation Memory**: Each question is independent
2. **Model Deprecation Warning**: Claude 3.5 Sonnet 20241022 is deprecated (update to newer model)
3. **Single Tool Per Question**: Best results with one action per question

## Future Enhancements

- [ ] Proper conversation state management
- [ ] Session-based chat history
- [ ] Multi-step workflow support
- [ ] Upgrade to latest Claude model
- [ ] Add authentication
- [ ] Rate limiting
- [ ] WebSocket for real-time updates

