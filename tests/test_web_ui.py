#!/usr/bin/env python3
"""
Test suite for Web UI - Tests all example questions via curl/HTTP requests
"""
import requests
import json
import time
import sys
from datetime import datetime

# Web UI endpoint
WEB_UI_URL = "http://localhost:5000"

# Test questions from the UI examples
TEST_QUESTIONS = [
    "Promote all GTC tagged objects to tier0",
    "Check alignment status of files tagged with modelsetid=hs-GTC-0002",
    "Tag all files in /mnt/se-lab/modelstore/new-models/ as modelsetid=hs-GTC-0003",
    "Apply placeonvolumes objective to /mnt/se-lab/modelstore/gtc-demo-models/",
    "List all objectives for /mnt/se-lab/modelstore/gtc-demo-models/",
    "Refresh Hammerspace mounts"
]

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")

def test_server_health():
    """Test if the web UI server is running"""
    print_header("Test 1: Server Health Check")
    try:
        response = requests.get(f"{WEB_UI_URL}/", timeout=5)
        if response.status_code == 200:
            print_success(f"Web UI server is running at {WEB_UI_URL}")
            return True
        else:
            print_error(f"Web UI returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Cannot connect to Web UI: {e}")
        return False

def test_tools_endpoint():
    """Test if the tools endpoint is working"""
    print_header("Test 2: MCP Tools Endpoint")
    try:
        response = requests.get(f"{WEB_UI_URL}/api/tools", timeout=10)
        if response.status_code == 200:
            data = response.json()
            tools = data.get('tools', [])
            print_success(f"Tools endpoint working - {len(tools)} tools available")
            print_info("Available tools:")
            for tool in tools[:5]:  # Show first 5 tools
                print(f"  - {tool['name']}: {tool['description'][:60]}...")
            if len(tools) > 5:
                print(f"  ... and {len(tools) - 5} more tools")
            return True
        else:
            print_error(f"Tools endpoint returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Error connecting to tools endpoint: {e}")
        return False
    except Exception as e:
        print_error(f"Error parsing tools response: {e}")
        return False

def test_chat_question(question, test_num):
    """Test a single chat question"""
    print_header(f"Test {test_num}: '{question}'")
    
    try:
        print_info(f"Sending question to Web UI...")
        start_time = time.time()
        
        response = requests.post(
            f"{WEB_UI_URL}/api/chat",
            json={"message": question},
            timeout=60  # Allow up to 60 seconds for Claude + MCP execution
        )
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            
            # Check if response contains error indicators
            error_indicators = [
                'Error:',
                'Exception',
                'TaskGroup',
                'Connection closed',
                'failed'
            ]
            
            has_error = any(indicator.lower() in response_text.lower() for indicator in error_indicators)
            
            if has_error:
                print_error(f"Response contains error indicators")
                print(f"\n{Colors.WARNING}Response:{Colors.ENDC}")
                print(response_text[:500])
                return False
            else:
                print_success(f"Question processed successfully in {elapsed_time:.2f}s")
                print(f"\n{Colors.OKCYAN}Response:{Colors.ENDC}")
                print(response_text[:300])
                if len(response_text) > 300:
                    print(f"... ({len(response_text) - 300} more characters)")
                return True
        else:
            print_error(f"HTTP status code {response.status_code}")
            error_data = response.json() if response.text else {}
            print(f"Error: {error_data.get('error', 'Unknown error')}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Request timed out after 60 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_clear_chat():
    """Test clearing the chat history"""
    print_header("Test: Clear Chat History")
    try:
        response = requests.post(f"{WEB_UI_URL}/api/clear", timeout=5)
        if response.status_code == 200:
            print_success("Chat history cleared successfully")
            return True
        else:
            print_error(f"Clear chat returned status code {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error clearing chat: {e}")
        return False

def run_all_tests():
    """Run all tests and generate a report"""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}WEB UI TEST SUITE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    results = []
    
    # Test 1: Server health
    results.append(("Server Health", test_server_health()))
    
    if not results[-1][1]:
        print_error("\n❌ Server is not running. Please start the Web UI first.")
        return False
    
    # Test 2: Tools endpoint
    results.append(("Tools Endpoint", test_tools_endpoint()))
    
    # Clear chat before starting question tests
    test_clear_chat()
    
    # Test 3+: All example questions
    for i, question in enumerate(TEST_QUESTIONS, start=3):
        result = test_chat_question(question, i)
        results.append((question, result))
        
        # Wait a bit between questions to avoid overwhelming the system
        if i < len(TEST_QUESTIONS) + 2:
            time.sleep(2)
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal Tests: {total}")
    print(f"{Colors.OKGREEN}Passed: {passed}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {total - passed}{Colors.ENDC}")
    print(f"Success Rate: {(passed/total)*100:.1f}%\n")
    
    print("Detailed Results:")
    for i, (test_name, result) in enumerate(results, start=1):
        status = f"{Colors.OKGREEN}PASS{Colors.ENDC}" if result else f"{Colors.FAIL}FAIL{Colors.ENDC}"
        print(f"  {i}. [{status}] {test_name[:60]}")
    
    print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

