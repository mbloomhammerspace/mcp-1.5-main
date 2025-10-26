#!/usr/bin/env python3
"""
Web UI for MCP Server with Anthropic Claude Integration
Allows natural language interaction with Hammerspace MCP services
"""
import os
import asyncio
import json
import logging
import warnings
from datetime import datetime
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response
from anthropic import Anthropic
# Use MCP bridge instead of direct MCP communication
from mcp_bridge import call_mcp_tool_via_cli, get_available_tools
from dotenv import load_dotenv

# Suppress deprecation warnings from Anthropic
warnings.filterwarnings("ignore", category=DeprecationWarning, module="anthropic")
warnings.filterwarnings("ignore", message=".*deprecated.*")

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Suppress httpx debug logs
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info(f"Loaded .env from: {env_path}")

# Initialize Anthropic client
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
if not anthropic_api_key:
    logger.error("ANTHROPIC_API_KEY not found in environment!")
    anthropic_client = None
else:
    try:
        anthropic_client = Anthropic(api_key=anthropic_api_key)
        logger.info(f"Anthropic client initialized with key: {anthropic_api_key[:20]}...")
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {e}")
        anthropic_client = None

# MCP Server configuration
MCP_SERVER_PATH = "/home/ubuntu/mcp-1.5-main/src/aiq_hstk_mcp_server.py"
MCP_SERVER_ENV = {"PYTHONPATH": "/home/ubuntu/mcp-1.5-main"}

# Import MCP Control Center
import sys
sys.path.append('/home/ubuntu/mcp-1.5-main/src')
from mcp_control_center import mcp_control_center

# Store conversation history
conversation_history = []

def get_mcp_tools():
    """Get list of available MCP tools from all MCP servers"""
    # Get Hammerspace MCP tools
    hammerspace_tools = get_available_tools()
    
    # Get Milvus MCP tools
    milvus_tools = []
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        milvus_tools = loop.run_until_complete(mcp_control_center.discover_tools("milvus"))
        loop.close()
        
        # Convert MCPTool objects to dict format
        milvus_tools_dict = []
        for tool in milvus_tools:
            milvus_tools_dict.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            })
        milvus_tools = milvus_tools_dict
    except Exception as e:
        logger.warning(f"Could not discover Milvus tools: {e}")
    
    # Get Kubernetes MCP tools
    k8s_tools = []
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        k8s_tools = loop.run_until_complete(mcp_control_center.discover_tools("kubernetes"))
        loop.close()
        
        # Convert MCPTool objects to dict format
        k8s_tools_dict = []
        for tool in k8s_tools:
            k8s_tools_dict.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            })
        k8s_tools = k8s_tools_dict
    except Exception as e:
        logger.warning(f"Could not discover Kubernetes tools: {e}")
    
    # Combine all tools
    all_tools = hammerspace_tools + milvus_tools + k8s_tools
    logger.info(f"Total tools discovered: {len(all_tools)} (Hammerspace: {len(hammerspace_tools)}, Milvus: {len(milvus_tools)}, K8s: {len(k8s_tools)})")
    return all_tools

def call_mcp_tool(tool_name: str, arguments: dict):
    """Call an MCP tool and return the result"""
    # First try Hammerspace MCP (existing functionality)
    try:
        result = call_mcp_tool_via_cli(tool_name, arguments)
        
        # Convert result to string format
        if isinstance(result, dict):
            if result.get("error"):
                return f"Error: {result['error']}"
            elif result.get("success"):
                return f"Success: {result.get('message', 'Operation completed successfully')}"
            else:
                return json.dumps(result, indent=2)
        else:
            return str(result)
    except Exception as e:
        # If Hammerspace MCP fails, try other MCP servers
        logger.warning(f"Hammerspace MCP tool {tool_name} failed: {e}")
        
        # Try Milvus MCP
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(mcp_control_center.call_tool("milvus", tool_name, arguments))
            loop.close()
            
            if isinstance(result, dict):
                if result.get("error"):
                    return f"Milvus Error: {result['error']}"
                else:
                    return json.dumps(result, indent=2)
            else:
                return str(result)
        except Exception as e2:
            logger.warning(f"Milvus MCP tool {tool_name} failed: {e2}")
            
            # Try Kubernetes MCP
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(mcp_control_center.call_tool("kubernetes", tool_name, arguments))
                loop.close()
                
                if isinstance(result, dict):
                    if result.get("error"):
                        return f"Kubernetes Error: {result['error']}"
                    else:
                        return json.dumps(result, indent=2)
                else:
                    return str(result)
            except Exception as e3:
                logger.error(f"All MCP servers failed for tool {tool_name}: {e3}")
                return f"Error: Tool {tool_name} not found in any MCP server"

def convert_mcp_tools_to_anthropic_format(mcp_tools):
    """Convert MCP tool definitions to Anthropic tool format"""
    anthropic_tools = []
    
    for tool in mcp_tools:
        anthropic_tool = {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["inputSchema"]
        }
        anthropic_tools.append(anthropic_tool)
    
    return anthropic_tools

@app.route('/')
def index():
    """Render the main UI"""
    return render_template('index.html')

@app.route('/mcp')
def mcp_control():
    """Render the MCP control center"""
    return render_template('mcp_control.html')

@app.route('/debug')
def debug():
    """Render the debug log viewer"""
    return render_template('debug.html')

@app.route('/monitor')
def monitor():
    """File ingest monitor page"""
    return render_template('monitor.html')

@app.route('/api/debug', methods=['GET'])
def api_debug():
    """JSON list of recent scanned file events.
    Combines:
    - Structured JSON events from inotify.log (NEW_FILES/FILE_CREATED/FILE_TAGGED)
    - Text 'Found supported file:' lines from file monitor logs as FILE_SCANNED entries
    """
    try:
        base_logs = Path(__file__).parent.parent / 'logs'
        events = []
        lines_out = []

        # Mirror the primary debug source verbatim (no filtering): file_monitor_daemon.log
        daemon_log = base_logs / 'file_monitor_daemon.log'
        if daemon_log.exists():
            try:
                with open(daemon_log, 'r', encoding='utf-8', errors='replace') as f:
                    # Take a large recent slice to capture bursts
                    raw = f.readlines()[-10000:]
                # Prefix with filename to match /debug context
                lines_out.extend([f"[file_monitor_daemon.log] " + l.rstrip('\n') for l in raw])
            except Exception:
                pass

        # 2) Parse JSON events from inotify.log
        inotify_path = base_logs / 'inotify.log'
        if inotify_path.exists():
            with open(inotify_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()[-2000:]
            for line in lines:
                s = line.strip()
                if not s or not s.startswith('{'):
                    continue
                try:
                    evt = json.loads(s)
                except Exception:
                    continue
                et = evt.get('event_type')
                if et in ('NEW_FILES', 'FILE_CREATED', 'FILE_TAGGED'):
                    file_path = evt.get('file_path') or evt.get('path') or ''
                    parts = file_path.split('/') if file_path else []
                    try:
                        collection = parts[parts.index('hub') + 1] if 'hub' in parts else (parts[-2] if len(parts) >= 2 else None)
                    except Exception:
                        collection = parts[-1] if parts else None
                    events.append({
                        'event_type': 'NEW_FILES',
                        'file_name': evt.get('file_name') or (file_path.rsplit('/',1)[-1] if file_path else ''),
                        'file_path': file_path,
                        'collection_name': collection,
                        'timestamp': evt.get('timestamp') or evt.get('ingest_time')
                    })

        # 3) Parse text lines from file monitor log for granular per-file discoveries
        # Attempt primary monitor log; fallback to web_ui.log if needed
        # Parse granular per-file discoveries from daemon log specifically
        if daemon_log.exists():
            try:
                with open(daemon_log, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()[-10000:]
            except Exception:
                lines = []
            for line in lines:
                # Example: 2025-10-25 19:19:11,931 - file_monitor - INFO - 📁 Found supported file: /mnt/anvil/hub/case-10027/Library/Cookies/file.txt
                if 'Found supported file:' not in line and 'file_monitor' not in line:
                    continue
                # Extract timestamp and path
                ts = line[:23].strip()
                file_path = None
                if 'Found supported file: ' in line:
                    try:
                        file_path = line.split('Found supported file: ', 1)[1].strip()
                    except Exception:
                        pass
                if not file_path:
                    # Try to extract a path-like token after INFO - 📁
                    m = re.search(r"(/mnt/[^\s]+)", line)
                    if m:
                        file_path = m.group(1)
                    else:
                        continue
                parts = file_path.split('/') if file_path else []
                try:
                    collection = parts[parts.index('hub') + 1] if 'hub' in parts else (parts[-2] if len(parts) >= 2 else None)
                except Exception:
                    collection = parts[-1] if parts else None
                events.append({
                    'event_type': 'FILE_SCANNED',
                    'file_name': file_path.rsplit('/',1)[-1] if file_path else '',
                    'file_path': file_path,
                    'collection_name': collection,
                    'timestamp': ts
                })

        # Sort newest first by timestamp string when present
        events.sort(key=lambda e: e.get('timestamp') or '', reverse=True)
        # Trim raw lines to last N overall
        if len(lines_out) > 1000:
            lines_out = lines_out[-1000:]
        resp = jsonify({ 'count': len(events), 'events': events, 'lines': lines_out, 'lines_count': len(lines_out) })
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        resp.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return resp
    except Exception as e:
        return jsonify({ 'count': 0, 'events': [], 'error': str(e) }), 500

@app.route('/api/debug/stream', methods=['GET'])
def api_debug_stream():
    """SSE stream of scanned file events (NEW_FILES + FILE_SCANNED)."""
    base_logs = Path(__file__).parent.parent / 'logs'
    inotify_path = base_logs / 'inotify.log'
    monitor_paths = [
        base_logs / 'file_monitor_daemon.log',  # primary granular source
        base_logs / 'file_monitor.log',
        base_logs / 'retroactive_fully_disabled.log',
        base_logs / 'web_ui.log'
    ]

    def snapshot_events():
        payloads = []
        # Only consider logs updated within the last 30 minutes
        import time
        now = time.time()
        freshness_s = 30 * 60

        # Snapshot from inotify (JSON)
        if inotify_path.exists() and (now - inotify_path.stat().st_mtime <= freshness_s):
            try:
                with open(inotify_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()[-200:]
                for line in lines:
                    s = line.strip()
                    if not s or not s.startswith('{'):
                        continue
                    try:
                        evt = json.loads(s)
                    except Exception:
                        continue
                    et = evt.get('event_type')
                    if et in ('NEW_FILES', 'FILE_CREATED', 'FILE_TAGGED'):
                        file_path = evt.get('file_path') or evt.get('path') or ''
                        parts = file_path.split('/') if file_path else []
                        try:
                            collection = parts[parts.index('hub') + 1] if 'hub' in parts else (parts[-2] if len(parts) >= 2 else None)
                        except Exception:
                            collection = parts[-1] if parts else None
                        payloads.append({
                            'event_type': 'NEW_FILES',
                            'file_name': evt.get('file_name') or (file_path.rsplit('/',1)[-1] if file_path else ''),
                            'file_path': file_path,
                            'collection_name': collection,
                            'timestamp': evt.get('timestamp') or evt.get('ingest_time')
                        })
            except Exception:
                pass
        # Snapshot from monitor logs (text)
        for mp in monitor_paths:
            if not mp.exists():
                continue
            try:
                # Do not freshness-filter daemon log; it's our primary granular feed
                if mp.name != 'file_monitor_daemon.log' and (now - mp.stat().st_mtime > freshness_s):
                    continue
            except Exception:
                pass
            try:
                with open(mp, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()[-500:]
            except Exception:
                continue
            for line in lines:
                if 'Found supported file:' not in line and 'file_monitor' not in line:
                    continue
                ts = line[:23].strip()
                file_path = None
                if 'Found supported file: ' in line:
                    try:
                        file_path = line.split('Found supported file: ', 1)[1].strip()
                    except Exception:
                        pass
                if not file_path:
                    m = re.search(r"(/mnt/[^\s]+)", line)
                    if m:
                        file_path = m.group(1)
                    else:
                        continue
                parts = file_path.split('/') if file_path else []
                try:
                    collection = parts[parts.index('hub') + 1] if 'hub' in parts else (parts[-2] if len(parts) >= 2 else None)
                except Exception:
                    collection = parts[-1] if parts else None
                payloads.append({
                    'event_type': 'FILE_SCANNED',
                    'file_name': file_path.rsplit('/',1)[-1] if file_path else '',
                    'file_path': file_path,
                    'collection_name': collection,
                    'timestamp': ts
                })
        return payloads

    def generate():
        # Initial burst
        initial = snapshot_events()
        yield f"data: {json.dumps({'count': len(initial), 'events': initial})}\n\n"

        # Tail inotify and monitor logs for new lines
        try:
            import time
            # Keep simple polling to avoid blocking tails
            while True:
                payloads = snapshot_events()
                if payloads:
                    yield f"data: {json.dumps({'count': len(payloads), 'events': payloads})}\n\n"
                time.sleep(2)
        except GeneratorExit:
            return
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    resp = Response(generate(), mimetype='text/event-stream')
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Connection'] = 'keep-alive'
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

    """File ingest monitor page"""
    return render_template('monitor.html')

@app.route('/events')
def events():
    """Event emission console page"""
    return render_template('events.html')

@app.route('/api/logs/stream')
def stream_logs():
    """Stream logs in real-time"""
    def generate():
        import subprocess
        import time
        
        # Read from actual log files
        log_files = [
            '/home/ubuntu/mcp-1.5-main/logs/retroactive_fully_disabled.log',
            '/home/ubuntu/mcp-1.5-main/logs/web_ui.log',
            '/home/ubuntu/mcp-1.5-main/logs/file_monitor.log'
        ]
        
        # Start with recent history from the file monitor log (which contains the tagging activity)
        try:
            result = subprocess.run(['tail', '-50', '/home/ubuntu/mcp-1.5-main/logs/retroactive_fully_disabled.log'], 
                                  capture_output=True, text=True, timeout=2)
            if result.stdout:
                yield f"data: {result.stdout}\n\n"
        except:
            pass
        
        # Now tail -f for real-time updates from all key logs
        follow_files = [
            '/home/ubuntu/mcp-1.5-main/logs/inotify.log',
            '/home/ubuntu/mcp-1.5-main/logs/file_monitor.log'
        ]
        proc = subprocess.Popen(
            ['tail', '-f'] + follow_files,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            for line in proc.stdout:
                yield f"data: {line}\n\n"
        finally:
            proc.kill()
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with Claude + MCP integration"""
    global conversation_history
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # For now, start each conversation fresh to avoid tool_result issues
        # In production, you'd want to maintain proper conversation state
        conversation_history = []
        
        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Get MCP tools
        mcp_tools = get_mcp_tools()
        anthropic_tools = convert_mcp_tools_to_anthropic_format(mcp_tools)
        
        # Check if LLM client is available
        if not anthropic_client:
            return jsonify({'error': 'LLM API client not initialized. Check configuration.'}), 500
        
        # Call Claude with tool use and system prompt for action-oriented responses
        system_prompt = """You are a comprehensive MCP management assistant with access to Hammerspace, Milvus, and Kubernetes MCP tools.

CRITICAL INSTRUCTIONS:
- EXECUTE what the user asks - don't suggest alternatives or workarounds
- Report what you DID and the actual RESULTS (success or failure)
- If something fails, report the specific error and what files/paths were affected
- If files are misaligned, list them specifically
- NO fallback suggestions - just execute and report facts
- Be direct: "✓ Done" or "✗ Failed: [specific error]"

MCP SERVER CAPABILITIES:
- HAMMERSPACE MCP: File tagging, tier management, objectives, alignment checks
- MILVUS MCP: Vector database operations, collections, embeddings, search
- KUBERNETES MCP: Cluster management, job deployment, pod monitoring, resource management

For Milvus operations, you can ask about:
- "List all collections in Milvus"
- "Show Milvus database status"
- "Check Milvus server health"
- "Get collection statistics"

For Kubernetes operations, you can ask about:
- "Show Kubernetes cluster status"
- "List running pods"
- "Check job status"
- "Get cluster resources"

KEY TOOLS FOR COMMON OPERATIONS:
- To tag files: use tag_directory_recursive with the full directory path
- To list files with a tag: use check_tagged_files_alignment (it shows files with the tag) - DO NOT use list_files_by_tag
- To check alignment: use check_tagged_files_alignment - MUST ALWAYS include share_path parameter or it will fail
- To promote files to tier0: use apply_objective_to_path with objective_name="Place-on-tier0" and the EXACT SAME directory path you just tagged
- To remove tier0 promotion: use remove_objective_from_path with objective_name="Place-on-tier0"
- To list objectives: use list_objectives_for_path

SMART share_path USAGE:
- If you DON'T know where files with a tag are located: DO NOT pass share_path parameter (tool will search all of /mnt/anvil/)
- If you DO know the specific directory: pass share_path="/mnt/anvil/modelstore/specific-dir"
- Let the tool find files automatically by their tag - don't guess the directory

CRITICAL PATH TRACKING:
- Remember the EXACT path you tagged (e.g., /mnt/anvil/modelstore/nvidia-test-thurs)
- When checking alignment, use check_tagged_files_alignment with share_path="/mnt/anvil/modelstore/nvidia-test-thurs" (the EXACT same path!)
- When promoting to tier0, use apply_objective_to_path with path="/mnt/anvil/modelstore/nvidia-test-thurs" (the EXACT same path!)
- NEVER use a different directory than what the user asked for
- NEVER search globally unless the user specifically mentions that directory

FINDING FILES BY TAG - CRITICAL:
- ALWAYS pass share_path parameter to check_tagged_files_alignment
- Start with a reasonable scope like share_path="/mnt/anvil/modelstore/" (NOT the entire /mnt/anvil/)
- If you just tagged a directory (e.g., /mnt/anvil/modelstore/nvidia-test-thurs), use that EXACT path as share_path
- The result will show the file path (e.g., /mnt/anvil/modelstore/some-dir/file.safetensors)
- Extract the directory from the file path (e.g., /mnt/anvil/modelstore/some-dir)
- Use that extracted directory for apply_objective_to_path or remove_objective_from_path
- NEVER search /mnt/anvil/ without a more specific subdirectory

WORKFLOW EXAMPLE:
User: "Tag files in /modelstore/nvidia-test-thurs as modelsetid=test123"
1. Tag: tag_directory_recursive(path="/mnt/anvil/modelstore/nvidia-test-thurs", tag_name="user.modelsetid", tag_value="test123")
2. Check: check_tagged_files_alignment(tag_name="user.modelsetid", tag_value="test123", share_path="/mnt/anvil/modelstore/nvidia-test-thurs")

User: "Promote those files to tier0"
3. Promote: apply_objective_to_path(objective_name="Place-on-tier0", path="/mnt/anvil/modelstore/nvidia-test-thurs")
4. Check: check_tagged_files_alignment(tag_name="user.modelsetid", tag_value="test123", share_path="/mnt/anvil/modelstore/nvidia-test-thurs")

IMPORTANT PATH HANDLING:
- Users may provide share-relative paths like "/modelstore/dir" or "/hub/data"
- Convert these to full mount paths: "/modelstore/*" → "/mnt/anvil/modelstore/*", "/hub/*" → "/mnt/anvil/hub/*"
- Common mappings: /modelstore → /mnt/anvil/modelstore, /hub → /mnt/anvil/hub, /audio → /mnt/anvil/audio
- If path doesn't start with /mnt, prepend /mnt/anvil to the share name
- For tier operations, use DIRECTORY paths (not individual files)

ERROR REPORTING:
- If alignment check fails: report which files are misaligned and their current status
- If objective fails: report the exact error from the tool
- If files not found: report that specifically
- ALWAYS show the FULL PATH of files in results - users need to verify correct location
- If files are in unexpected directories, report that as a potential issue
- If error contains "Stale file handle": Tell user "Error: Stale file handle detected. Run: Refresh Hammerspace mounts"
- For other errors: Report the error without suggestions

Example good response: "✓ Applied 'Place-on-tier0' objective to /mnt/anvil/modelstore/nvidia-test-thurs/. Files will be promoted."

Example bad response: "The operation encountered an issue. You may want to try checking the alignment first or contact your administrator."
"""
        
        try:
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=system_prompt,
                tools=anthropic_tools,
                messages=conversation_history
            )
        except Exception as api_error:
            logger.error(f"LLM API error: {api_error}")
            return jsonify({'error': f'LLM API error: {str(api_error)}'}), 500
        
        # Process response and handle tool calls
        # Keep iterating until we get a response without tool calls
        max_iterations = 5
        iteration = 0
        final_response = ""
        
        while iteration < max_iterations:
            iteration += 1
            
            # Check if response contains tool uses
            has_tool_use = any(block.type == "tool_use" for block in response.content)
            
            if not has_tool_use:
                # No more tool calls, extract final text response
                for content_block in response.content:
                    if content_block.type == "text":
                        final_response += content_block.text
                break
            
            # Build assistant message with all content blocks
            assistant_content = []
            tool_results = []
            
            for content_block in response.content:
                if content_block.type == "text":
                    assistant_content.append({
                        "type": "text",
                        "text": content_block.text
                    })
                    final_response += content_block.text
                elif content_block.type == "tool_use":
                    # Execute the MCP tool
                    tool_name = content_block.name
                    tool_args = content_block.input
                    tool_id = content_block.id
                    
                    logger.info(f"Executing MCP tool: {tool_name} with args: {tool_args}")
                    
                    # Add tool use to assistant message
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tool_id,
                        "name": tool_name,
                        "input": tool_args
                    })
                    
                    # Call the MCP tool
                    try:
                        tool_result = call_mcp_tool(tool_name, tool_args)
                    except Exception as tool_error:
                        logger.error(f"MCP tool error: {tool_error}")
                        tool_result = f"Error executing tool: {str(tool_error)}"
                    
                    # Collect tool result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": tool_result
                    })
            
            # Add assistant message to conversation
            conversation_history.append({
                "role": "assistant",
                "content": assistant_content
            })
            
            # Add tool results to conversation
            conversation_history.append({
                "role": "user",
                "content": tool_results
            })
            
            # Get Claude's next response (might use more tools or give final answer)
            try:
                response = anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    system=system_prompt,
                    tools=anthropic_tools,
                    messages=conversation_history
                )
            except Exception as api_error:
                logger.error(f"LLM API error in iteration {iteration}: {api_error}")
                return jsonify({'error': f'LLM API error: {str(api_error)}'}), 500
        
        
        return jsonify({
            'response': final_response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools', methods=['GET'])
def get_tools():
    """Get list of available MCP tools"""
    try:
        mcp_tools = get_mcp_tools()
        
        tools_list = [
            {
                "name": tool["name"],
                "description": tool["description"]
            }
            for tool in mcp_tools
        ]
        
        return jsonify({'tools': tools_list})
        
    except Exception as e:
        logger.error(f"Error getting tools: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []
    return jsonify({'status': 'success'})

@app.route('/api/monitor/status', methods=['GET'])
def get_monitor_status():
    """Get current monitor status"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
        from file_monitor import get_monitor_service
        
        monitor_service = get_monitor_service()
        status = monitor_service.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting monitor status: {str(e)}")
        return jsonify({
            'error': str(e),
            'running': False
        }), 500

@app.route('/api/monitor/events', methods=['GET'])
def get_ingest_events():
    """Get recent file ingest events"""
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 100))
        event_type = request.args.get('event_type', '').strip()
        file_pattern = request.args.get('file_pattern', '').strip().lower()
        since_timestamp = request.args.get('since_timestamp', '').strip()
        
        # Read and parse the inotify log file
        log_file = Path(__file__).parent.parent / 'logs' / 'inotify.log'
        
        if not log_file.exists():
            return jsonify({
                'success': False,
                'error': 'Log file not found',
                'events': [],
                'count': 0
            })
        
        events = []
        
        # Read file in reverse order to get most recent events first
        try:
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # Fallback to latin-1 encoding if utf-8 fails
            with open(log_file, 'r', encoding='latin-1', errors='replace') as f:
                lines = f.readlines()
        
        # Parse events from newest to oldest
        for line in reversed(lines):
            line = line.strip()
            if not line or not line.startswith('{'):
                continue
            
            try:
                event = json.loads(line)
                
                # Apply filters
                if event_type and event.get("event_type") != event_type:
                    continue
                
                if file_pattern and file_pattern not in event.get("file_name", "").lower():
                    continue
                
                if since_timestamp and event.get("timestamp", "") < since_timestamp:
                    continue
                
                events.append(event)
                
                if len(events) >= limit:
                    break
                    
            except json.JSONDecodeError:
                continue
        
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events),
            'limit': limit,
            'filters': {
                'event_type': event_type or 'all',
                'file_pattern': file_pattern or 'all',
                'since_timestamp': since_timestamp or 'all_time'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting ingest events: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'events': [],
            'count': 0
        }), 500

@app.route('/api/monitor/events/stream', methods=['GET'])
def stream_ingest_events():
    """Stream ingest events using Server-Sent Events"""
    def generate_events():
        log_file = Path(__file__).parent.parent / 'logs' / 'inotify.log'
        last_position = 0
        
        # Seek to end of file
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    f.seek(0, 2)  # Seek to end
                    last_position = f.tell()
            except UnicodeDecodeError:
                with open(log_file, 'r', encoding='latin-1', errors='replace') as f:
                    f.seek(0, 2)  # Seek to end
                    last_position = f.tell()
        
        while True:
            try:
                if log_file.exists():
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                            f.seek(last_position)
                            new_lines = f.readlines()
                            last_position = f.tell()
                    except UnicodeDecodeError:
                        with open(log_file, 'r', encoding='latin-1', errors='replace') as f:
                            f.seek(last_position)
                            new_lines = f.readlines()
                            last_position = f.tell()
                        
                        for line in new_lines:
                            line = line.strip()
                            if line and line.startswith('{'):
                                try:
                                    event = json.loads(line)
                                    yield f"data: {json.dumps(event)}\n\n"
                                except json.JSONDecodeError:
                                    pass
                
                import time
                time.sleep(1)  # Poll every second
                
            except Exception as e:
                logger.error(f"Error streaming events: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return Response(generate_events(), mimetype='text/event-stream')

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all events from the MCP server for the Event Console"""
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 1000))
        event_type = request.args.get('event_type', '').strip()
        file_pattern = request.args.get('file_pattern', '').strip().lower()
        
        # Read and parse the inotify log file
        log_file = Path(__file__).parent.parent / 'logs' / 'inotify.log'
        
        if not log_file.exists():
            return jsonify({
                'success': False,
                'error': 'Log file not found',
                'events': []
            })
        
        events = []
        try:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                # Fallback to latin-1 encoding if utf-8 fails
                with open(log_file, 'r', encoding='latin-1', errors='replace') as f:
                    lines = f.readlines()
                
            # Parse JSON events from log file
            for line in lines[-limit:]:  # Get last N lines
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    event = json.loads(line)
                    
                    # Apply filters
                    if event_type and event.get('event_type') != event_type:
                        continue
                    if file_pattern and file_pattern not in event.get('file_path', '').lower():
                        continue
                    
                    events.append(event)
                except json.JSONDecodeError:
                    # Skip non-JSON lines (like log messages)
                    continue
                    
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            return jsonify({
                'success': False,
                'error': f'Error reading log file: {str(e)}',
                'events': []
            })
        
        # Sort events by timestamp (newest first)
        events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        response = jsonify({
            'success': True,
            'events': events,
            'count': len(events),
            'total_lines_processed': len(lines) if 'lines' in locals() else 0
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
        
    except Exception as e:
        logger.error(f"Error getting events: {str(e)}")
        response = jsonify({
            'success': False,
            'error': str(e),
            'events': []
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 500

@app.route('/api/mcp/status')
def api_mcp_status():
    """API endpoint to get MCP server status"""
    try:
        # Run async function in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        status = loop.run_until_complete(mcp_control_center.get_unified_status())
        loop.close()
        
        return jsonify({
            "success": True,
            "status": status
        })
    except Exception as e:
        logger.error(f"Error getting MCP status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/mcp/milvus')
def api_mcp_milvus():
    """API endpoint to get Milvus status"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        status = loop.run_until_complete(mcp_control_center.get_milvus_status())
        loop.close()
        
        return jsonify({
            "success": True,
            "milvus": status
        })
    except Exception as e:
        logger.error(f"Error getting Milvus status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/mcp/kubernetes')
def api_mcp_kubernetes():
    """API endpoint to get Kubernetes status"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        status = loop.run_until_complete(mcp_control_center.get_kubernetes_status())
        loop.close()
        
        return jsonify({
            "success": True,
            "kubernetes": status
        })
    except Exception as e:
        logger.error(f"Error getting Kubernetes status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/mcp/hammerspace')
def api_mcp_hammerspace():
    """API endpoint to get Hammerspace status"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        status = loop.run_until_complete(mcp_control_center.get_hammerspace_status())
        loop.close()
        
        return jsonify({
            "success": True,
            "hammerspace": status
        })
    except Exception as e:
        logger.error(f"Error getting Hammerspace status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/mcp/start/<server_id>')
def api_mcp_start_server(server_id):
    """API endpoint to start an MCP server"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(mcp_control_center.start_server(server_id))
        loop.close()
        
        return jsonify({
            "success": success,
            "message": f"Server {server_id} {'started' if success else 'failed to start'}"
        })
    except Exception as e:
        logger.error(f"Error starting server {server_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/mcp/stop/<server_id>')
def api_mcp_stop_server(server_id):
    """API endpoint to stop an MCP server"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(mcp_control_center.stop_server(server_id))
        loop.close()
        
        return jsonify({
            "success": success,
            "message": f"Server {server_id} {'stopped' if success else 'failed to stop'}"
        })
    except Exception as e:
        logger.error(f"Error stopping server {server_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/mcp/call/<server_id>/<tool_name>')
def api_mcp_call_tool(server_id, tool_name):
    """API endpoint to call a tool on an MCP server"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(mcp_control_center.call_tool(server_id, tool_name, {}))
        loop.close()
        
        return jsonify({
            "success": True,
            "result": result
        })
    except Exception as e:
        logger.error(f"Error calling tool {tool_name} on {server_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Check for Anthropic API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not found in environment")
        print("Please add it to your .env file")
        exit(1)
    
    print("🚀 Starting MCP Web UI with Claude Integration")
    print("📡 MCP Server: " + MCP_SERVER_PATH)
    print("🤖 AI Model: Claude 3.5 Sonnet")
    print("🌐 Web UI: http://localhost:5000")
    
    # Start the file monitor as a persistent background service
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
    try:
        from file_monitor import get_monitor_service
        monitor = get_monitor_service()
        
        # Start monitor in background thread
        import threading
        def start_monitor():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(monitor.start())
            if result.get('success'):
                print(f"✅ File monitor started - watching {len(result.get('watch_paths', []))} shares")
            else:
                print(f"⚠️ File monitor failed to start: {result.get('error', 'Unknown')}")
            # Keep loop running for monitor
            loop.run_forever()
        
        monitor_thread = threading.Thread(target=start_monitor, daemon=True)
        monitor_thread.start()
    except Exception as e:
        print(f"⚠️ File monitor not available: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)


@app.route('/json-events', methods=['GET'])
def stream_json_events():
    """Stream MCP events as Server-Sent Events (SSE)"""
    def generate_events():
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connection', 'message': 'Connected to MCP events stream', 'timestamp': datetime.now().isoformat()})}\n\n"
        
        # Read the inotify log file
        log_file = Path(__file__).parent.parent / 'logs' / 'inotify.log'
        
        if not log_file.exists():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Log file not found', 'timestamp': datetime.now().isoformat()})}\n\n"
            return
        
        last_position = 0
        while True:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    last_position = f.tell()
                    
                    for line in new_lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        try:
                            event = json.loads(line)
                            # Send the event as SSE
                            yield f"data: {json.dumps(event)}\n\n"
                        except json.JSONDecodeError:
                            # Skip non-JSON lines
                            continue
                            
            except Exception as e:
                logger.error(f"Error reading log file: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
                break
                
            # Wait before checking for new events
            import time
            time.sleep(2)
    
    return Response(generate_events(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Cache-Control'
    })

