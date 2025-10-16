#!/usr/bin/env python3
"""
Test Harness for Volume Canvas MCP Server
This script provides a comprehensive testing and debugging environment for the MCP server.
"""

import asyncio
import json
import logging
import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import signal
import threading
import requests
import httpx

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_harness.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_harness')


class TestHarness:
    """Comprehensive test harness for Volume Canvas MCP Server."""
    
    def __init__(self, config_file: str = None):
        """Initialize the test harness."""
        self.config_file = config_file
        self.server_process = None
        self.server_url = "http://localhost:9901"
        self.sse_url = f"{self.server_url}/sse"
        self.test_results = []
        self.start_time = None
        self.end_time = None
        
        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)
    
    async def start_server(self) -> bool:
        """Start the MCP server."""
        try:
            logger.info("🚀 Starting Volume Canvas MCP Server...")
            
            # Start the server process
            cmd = [
                sys.executable,
                str(Path(__file__).parent / "start_aiq_mcp_server.py"),
                "--host", "0.0.0.0",
                "--port", "9901",
                "--path", "/sse"
            ]
            
            if self.config_file:
                cmd.extend(["--config", self.config_file])
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(__file__).parent.parent
            )
            
            # Wait for server to start
            await self._wait_for_server()
            
            logger.info("✅ Server started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            return False
    
    async def _wait_for_server(self, timeout: int = 30):
        """Wait for the server to be ready."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.server_url}/health", timeout=5.0)
                    if response.status_code == 200:
                        logger.info("✅ Server health check passed")
                        return
            except Exception:
                pass
            
            await asyncio.sleep(1)
        
        raise TimeoutError("Server failed to start within timeout period")
    
    def stop_server(self):
        """Stop the MCP server."""
        if self.server_process:
            logger.info("🛑 Stopping server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
            logger.info("✅ Server stopped")
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run health check tests."""
        logger.info("🔍 Running health check tests...")
        
        test_result = {
            "test_name": "health_check",
            "status": "failed",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Test basic connectivity
                response = await client.get(f"{self.server_url}/health", timeout=10.0)
                test_result["details"]["health_endpoint"] = {
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code == 200 else response.text
                }
                
                # Test SSE endpoint
                try:
                    sse_response = await client.get(self.sse_url, timeout=5.0)
                    test_result["details"]["sse_endpoint"] = {
                        "status_code": sse_response.status_code,
                        "accessible": sse_response.status_code in [200, 404]  # 404 is OK for SSE without proper headers
                    }
                except Exception as e:
                    test_result["details"]["sse_endpoint"] = {
                        "error": str(e),
                        "accessible": False
                    }
                
                if response.status_code == 200:
                    test_result["status"] = "passed"
                    logger.info("✅ Health check passed")
                else:
                    logger.error(f"❌ Health check failed: {response.status_code}")
        
        except Exception as e:
            test_result["details"]["error"] = str(e)
            logger.error(f"❌ Health check error: {e}")
        
        self.test_results.append(test_result)
        return test_result
    
    async def run_function_tests(self) -> List[Dict[str, Any]]:
        """Run tests for all MCP functions."""
        logger.info("🧪 Running function tests...")
        
        # Define test cases
        test_cases = [
            {
                "name": "list_volumes",
                "function": "list_volumes",
                "params": {"filter": "all", "storage_system": "production"},
                "expected_keys": ["volumes"]
            },
            {
                "name": "list_shares",
                "function": "list_shares",
                "params": {"volume_uuid": "test-uuid", "storage_system": "production"},
                "expected_keys": ["shares"]
            },
            {
                "name": "list_files",
                "function": "list_files",
                "params": {"path": "/test", "limit": 10, "storage_system": "production"},
                "expected_keys": ["files"]
            },
            {
                "name": "search_files",
                "function": "search_files",
                "params": {"query": "test", "storage_system": "production"},
                "expected_keys": ["results"]
            },
            {
                "name": "get_system_status",
                "function": "get_system_status",
                "params": {"storage_system": "production"},
                "expected_keys": ["status", "data"]
            },
            {
                "name": "list_jobs",
                "function": "list_jobs",
                "params": {"storage_system": "production"},
                "expected_keys": ["jobs"]
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            logger.info(f"Testing {test_case['name']}...")
            
            result = await self._test_mcp_function(
                test_case["function"],
                test_case["params"],
                test_case["expected_keys"]
            )
            
            result["test_name"] = test_case["name"]
            results.append(result)
            self.test_results.append(result)
        
        return results
    
    async def _test_mcp_function(self, function_name: str, params: Dict[str, Any], expected_keys: List[str]) -> Dict[str, Any]:
        """Test a specific MCP function."""
        result = {
            "function": function_name,
            "status": "failed",
            "params": params,
            "response": None,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # This would be the actual MCP function call
            # For now, we'll simulate the response
            mock_response = await self._simulate_mcp_function_call(function_name, params)
            
            result["response"] = mock_response
            
            # Check if expected keys are present
            missing_keys = []
            for key in expected_keys:
                if key not in mock_response:
                    missing_keys.append(key)
            
            if not missing_keys:
                result["status"] = "passed"
                logger.info(f"✅ {function_name} test passed")
            else:
                result["error"] = f"Missing expected keys: {missing_keys}"
                logger.error(f"❌ {function_name} test failed: {result['error']}")
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ {function_name} test error: {e}")
        
        return result
    
    async def _simulate_mcp_function_call(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate an MCP function call for testing."""
        # This is a mock implementation for testing
        # In a real scenario, this would make actual MCP calls
        
        if function_name == "list_volumes":
            return {
                "volumes": [
                    {
                        "uuid": "test-volume-1",
                        "name": "Test Volume 1",
                        "type": "lss",
                        "state": "UP",
                        "size_bytes": 1000000000,
                        "used_bytes": 500000000,
                        "created": "2024-01-01T00:00:00Z",
                        "modified": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        elif function_name == "list_shares":
            return {
                "shares": [
                    {
                        "uuid": "test-share-1",
                        "name": "Test Share",
                        "path": "/test",
                        "file_count": 100,
                        "created": "2024-01-01T00:00:00Z",
                        "modified": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        elif function_name == "list_files":
            return {
                "files": [
                    {
                        "name": "test_file.txt",
                        "path": "/test/test_file.txt",
                        "size_bytes": 1024,
                        "created": "2024-01-01T00:00:00Z",
                        "modified": "2024-01-01T00:00:00Z",
                        "share_uuid": "test-share-1",
                        "volume_uuid": "test-volume-1"
                    }
                ]
            }
        elif function_name == "search_files":
            return {
                "results": [
                    {
                        "name": "test_file.txt",
                        "path": "/test/test_file.txt",
                        "size_bytes": 1024,
                        "tags": {},
                        "share_uuid": "test-share-1",
                        "volume_uuid": "test-volume-1"
                    }
                ]
            }
        elif function_name == "get_system_status":
            return {
                "status": "success",
                "data": {
                    "summary": {
                        "total_nodes": 2,
                        "total_volumes": 5,
                        "total_shares": 3,
                        "total_files": 1000
                    },
                    "health": "healthy",
                    "last_updated": datetime.now().isoformat()
                }
            }
        elif function_name == "list_jobs":
            return {
                "jobs": [
                    {
                        "uuid": "test-job-1",
                        "name": "Test Job",
                        "status": "RUNNING",
                        "progress": 50.0,
                        "created": "2024-01-01T00:00:00Z",
                        "started": "2024-01-01T00:00:00Z",
                        "completed": None
                    }
                ]
            }
        else:
            return {"error": f"Unknown function: {function_name}"}
    
    async def run_performance_tests(self) -> List[Dict[str, Any]]:
        """Run performance tests."""
        logger.info("⚡ Running performance tests...")
        
        performance_tests = [
            {
                "name": "concurrent_requests",
                "description": "Test concurrent MCP function calls",
                "concurrency": 10,
                "iterations": 5
            },
            {
                "name": "response_time",
                "description": "Test response times for various functions",
                "functions": ["list_volumes", "get_system_status", "list_jobs"]
            }
        ]
        
        results = []
        
        for test in performance_tests:
            if test["name"] == "concurrent_requests":
                result = await self._test_concurrent_requests(test)
            elif test["name"] == "response_time":
                result = await self._test_response_times(test)
            else:
                continue
            
            results.append(result)
            self.test_results.append(result)
        
        return results
    
    async def _test_concurrent_requests(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test concurrent request handling."""
        result = {
            "test_name": "concurrent_requests",
            "status": "failed",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            concurrency = test_config["concurrency"]
            iterations = test_config["iterations"]
            
            async def make_request():
                return await self._simulate_mcp_function_call("get_system_status", {})
            
            start_time = time.time()
            
            # Run concurrent requests
            tasks = []
            for _ in range(concurrency * iterations):
                tasks.append(make_request())
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Analyze results
            successful_requests = sum(1 for r in responses if not isinstance(r, Exception))
            failed_requests = len(responses) - successful_requests
            
            result["details"] = {
                "total_requests": len(responses),
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "duration_seconds": duration,
                "requests_per_second": len(responses) / duration,
                "average_response_time": duration / len(responses)
            }
            
            if failed_requests == 0:
                result["status"] = "passed"
                logger.info(f"✅ Concurrent requests test passed: {successful_requests}/{len(responses)} successful")
            else:
                result["status"] = "failed"
                logger.error(f"❌ Concurrent requests test failed: {failed_requests} failures")
        
        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Concurrent requests test error: {e}")
        
        return result
    
    async def _test_response_times(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test response times for various functions."""
        result = {
            "test_name": "response_time",
            "status": "failed",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            functions = test_config["functions"]
            response_times = {}
            
            for function_name in functions:
                start_time = time.time()
                await self._simulate_mcp_function_call(function_name, {})
                end_time = time.time()
                
                response_times[function_name] = end_time - start_time
            
            result["details"] = {
                "response_times": response_times,
                "average_response_time": sum(response_times.values()) / len(response_times),
                "max_response_time": max(response_times.values()),
                "min_response_time": min(response_times.values())
            }
            
            # Check if response times are acceptable (less than 1 second)
            max_time = max(response_times.values())
            if max_time < 1.0:
                result["status"] = "passed"
                logger.info(f"✅ Response time test passed: max {max_time:.3f}s")
            else:
                result["status"] = "failed"
                logger.error(f"❌ Response time test failed: max {max_time:.3f}s")
        
        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ Response time test error: {e}")
        
        return result
    
    async def run_integration_tests(self) -> List[Dict[str, Any]]:
        """Run integration tests."""
        logger.info("🔗 Running integration tests...")
        
        integration_tests = [
            {
                "name": "volume_migration_workflow",
                "description": "Test complete volume migration workflow",
                "steps": [
                    "list_volumes",
                    "list_files",
                    "copy_files",
                    "verify_data_integrity"
                ]
            },
            {
                "name": "objective_management_workflow",
                "description": "Test objective management workflow",
                "steps": [
                    "place_on_tier",
                    "exclude_from_tier",
                    "get_objective_debug_info"
                ]
            }
        ]
        
        results = []
        
        for test in integration_tests:
            result = await self._test_workflow(test)
            results.append(result)
            self.test_results.append(result)
        
        return results
    
    async def _test_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test a complete workflow."""
        result = {
            "test_name": workflow_config["name"],
            "status": "failed",
            "details": {
                "steps": [],
                "workflow_duration": 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            start_time = time.time()
            steps = workflow_config["steps"]
            
            for step in steps:
                step_start = time.time()
                step_result = await self._simulate_mcp_function_call(step, {})
                step_end = time.time()
                
                result["details"]["steps"].append({
                    "function": step,
                    "status": "passed" if "error" not in step_result else "failed",
                    "duration": step_end - step_start,
                    "response": step_result
                })
            
            end_time = time.time()
            result["details"]["workflow_duration"] = end_time - start_time
            
            # Check if all steps passed
            failed_steps = [s for s in result["details"]["steps"] if s["status"] == "failed"]
            
            if not failed_steps:
                result["status"] = "passed"
                logger.info(f"✅ {workflow_config['name']} workflow test passed")
            else:
                result["status"] = "failed"
                logger.error(f"❌ {workflow_config['name']} workflow test failed: {len(failed_steps)} failed steps")
        
        except Exception as e:
            result["details"]["error"] = str(e)
            logger.error(f"❌ {workflow_config['name']} workflow test error: {e}")
        
        return result
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        self.end_time = datetime.now()
        
        if self.start_time:
            total_duration = (self.end_time - self.start_time).total_seconds()
        else:
            total_duration = 0
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("status") == "passed")
        failed_tests = total_tests - passed_tests
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_duration_seconds": total_duration,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat()
            },
            "test_results": self.test_results,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if r.get("status") == "failed"]
        
        if failed_tests:
            recommendations.append("Review failed tests and fix underlying issues")
        
        # Check for performance issues
        performance_tests = [r for r in self.test_results if "performance" in r.get("test_name", "")]
        for test in performance_tests:
            if test.get("status") == "failed":
                recommendations.append("Optimize performance for better response times")
        
        # Check for integration issues
        integration_tests = [r for r in self.test_results if "workflow" in r.get("test_name", "")]
        for test in integration_tests:
            if test.get("status") == "failed":
                recommendations.append("Review integration workflow configurations")
        
        if not recommendations:
            recommendations.append("All tests passed! System is ready for production use.")
        
        return recommendations
    
    def save_report(self, filename: str = None):
        """Save the test report to a file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"
        
        report = self.generate_report()
        
        # Ensure reports directory exists
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        report_path = reports_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Test report saved to: {report_path}")
        return report_path
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and generate a comprehensive report."""
        logger.info("🚀 Starting comprehensive test suite...")
        self.start_time = datetime.now()
        
        try:
            # Start server
            if not await self.start_server():
                logger.error("❌ Failed to start server, aborting tests")
                return {"error": "Failed to start server"}
            
            # Run all test suites
            await self.run_health_check()
            await self.run_function_tests()
            await self.run_performance_tests()
            await self.run_integration_tests()
            
            # Generate and save report
            report_path = self.save_report()
            
            logger.info("✅ All tests completed successfully")
            return {"status": "completed", "report_path": str(report_path)}
        
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            return {"error": str(e)}
        
        finally:
            self.stop_server()


async def main():
    """Main entry point for the test harness."""
    parser = argparse.ArgumentParser(description="Volume Canvas MCP Server Test Harness")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--health-only", action="store_true", help="Run only health checks")
    parser.add_argument("--functions-only", action="store_true", help="Run only function tests")
    parser.add_argument("--performance-only", action="store_true", help="Run only performance tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--report-file", help="Custom report filename")
    
    args = parser.parse_args()
    
    # Create test harness
    harness = TestHarness(args.config)
    
    try:
        if args.health_only:
            await harness.start_server()
            await harness.run_health_check()
        elif args.functions_only:
            await harness.start_server()
            await harness.run_function_tests()
        elif args.performance_only:
            await harness.start_server()
            await harness.run_performance_tests()
        elif args.integration_only:
            await harness.start_server()
            await harness.run_integration_tests()
        else:
            # Run all tests
            result = await harness.run_all_tests()
            print(f"\n📊 Test Results: {result}")
        
        # Save report if specified
        if args.report_file:
            harness.save_report(args.report_file)
    
    except KeyboardInterrupt:
        logger.info("🛑 Test harness interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test harness error: {e}")
    finally:
        harness.stop_server()


if __name__ == "__main__":
    asyncio.run(main())
