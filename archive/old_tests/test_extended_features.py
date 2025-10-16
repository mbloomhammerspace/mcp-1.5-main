#!/usr/bin/env python3
"""
Unit tests for the Extended Volume Canvas MCP Server Features
Tests the new tagging and objectives functionality.
"""

import asyncio
import json
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the MCP server
from volume_canvas_mcp_server_clean import handle_call_tool


class TestTagSearchFeatures:
    """Test tag search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_files_by_tag_success(self):
        """Test successful tag-based file search."""
        result = await handle_call_tool("search_files_by_tag", {
            "tag_name": "user.priority",
            "tag_value": "high"
        })
        
        # Parse the result
        result_data = json.loads(result[0].text)
        
        assert "tag_name" in result_data
        assert "tag_value" in result_data
        assert "matching_files" in result_data
        assert "total_count" in result_data
        assert "timestamp" in result_data
        
        assert result_data["tag_name"] == "user.priority"
        assert result_data["tag_value"] == "high"
        assert result_data["total_count"] >= 0
    
    @pytest.mark.asyncio
    async def test_search_files_by_tag_no_value(self):
        """Test tag search without specific value."""
        result = await handle_call_tool("search_files_by_tag", {
            "tag_name": "user.project"
        })
        
        result_data = json.loads(result[0].text)
        
        assert result_data["tag_name"] == "user.project"
        assert result_data["tag_value"] == ""
        assert "matching_files" in result_data
    
    @pytest.mark.asyncio
    async def test_search_files_by_tag_with_path(self):
        """Test tag search with path scoping."""
        result = await handle_call_tool("search_files_by_tag", {
            "tag_name": "user.tier",
            "tag_value": "hot",
            "path": "/models"
        })
        
        result_data = json.loads(result[0].text)
        
        assert result_data["tag_name"] == "user.tier"
        assert result_data["tag_value"] == "hot"
        assert result_data["search_path"] == "/models"
    
    @pytest.mark.asyncio
    async def test_list_files_with_tags_success(self):
        """Test listing files with their tags."""
        result = await handle_call_tool("list_files_with_tags", {
            "path": "/",
            "limit": 5
        })
        
        result_data = json.loads(result[0].text)
        
        assert "path" in result_data
        assert "files" in result_data
        assert "total_count" in result_data
        assert "timestamp" in result_data
        
        assert result_data["path"] == "/"
        assert result_data["total_count"] >= 0
        
        # Check that files have tags
        for file_info in result_data["files"]:
            assert "tags" in file_info
            assert isinstance(file_info["tags"], list)


class TestTagManagementFeatures:
    """Test tag management functionality."""
    
    @pytest.mark.asyncio
    async def test_set_file_tag_success(self):
        """Test setting a tag on a file."""
        result = await handle_call_tool("set_file_tag", {
            "file_path": "/test/new-file.txt",
            "tag_name": "user.test",
            "tag_value": "mcp-demo"
        })
        
        result_data = json.loads(result[0].text)
        
        assert result_data["success"] is True
        assert result_data["file_path"] == "/test/new-file.txt"
        assert "tag" in result_data
        assert result_data["tag"]["name"] == "user.test"
        assert result_data["tag"]["value"] == "mcp-demo"
        assert "all_tags" in result_data
        assert "timestamp" in result_data
    
    @pytest.mark.asyncio
    async def test_set_file_tag_update_existing(self):
        """Test updating an existing tag."""
        # Set initial tag
        await handle_call_tool("set_file_tag", {
            "file_path": "/test/update-test.txt",
            "tag_name": "user.priority",
            "tag_value": "low"
        })
        
        # Update the tag
        result = await handle_call_tool("set_file_tag", {
            "file_path": "/test/update-test.txt",
            "tag_name": "user.priority",
            "tag_value": "high"
        })
        
        result_data = json.loads(result[0].text)
        
        assert result_data["success"] is True
        assert result_data["tag"]["value"] == "high"
        
        # Check that only one tag with this name exists
        all_tags = result_data["all_tags"]
        priority_tags = [tag for tag in all_tags if tag["name"] == "user.priority"]
        assert len(priority_tags) == 1
        assert priority_tags[0]["value"] == "high"


class TestObjectiveFeatures:
    """Test objective management functionality."""
    
    @pytest.mark.asyncio
    async def test_place_on_tier_success(self):
        """Test creating a place-on-tier objective."""
        result = await handle_call_tool("place_on_tier", {
            "path": "/models/test-model.pt",
            "tier_name": "tier0"
        })
        
        result_data = json.loads(result[0].text)
        
        assert result_data["success"] is True
        assert "objective" in result_data
        assert result_data["objective"]["type"] == "place_on_tier"
        assert result_data["objective"]["path"] == "/models/test-model.pt"
        assert result_data["objective"]["tier_name"] == "tier0"
        assert result_data["objective"]["status"] == "active"
        assert "uuid" in result_data["objective"]
        assert "created" in result_data["objective"]
    
    @pytest.mark.asyncio
    async def test_exclude_from_tier_success(self):
        """Test creating an exclude-from-tier objective."""
        result = await handle_call_tool("exclude_from_tier", {
            "path": "/backups/old-backup.tar.gz",
            "tier_name": "tier0"
        })
        
        result_data = json.loads(result[0].text)
        
        assert result_data["success"] is True
        assert "objective" in result_data
        assert result_data["objective"]["type"] == "exclude_from_tier"
        assert result_data["objective"]["path"] == "/backups/old-backup.tar.gz"
        assert result_data["objective"]["tier_name"] == "tier0"
        assert result_data["objective"]["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_apply_objective_to_files_success(self):
        """Test applying objectives to multiple files."""
        result = await handle_call_tool("apply_objective_to_files", {
            "file_paths": [
                "/models/model1.pt",
                "/models/model2.pt",
                "/models/model3.pt"
            ],
            "objective_type": "place_on_tier",
            "tier_name": "tier0"
        })
        
        result_data = json.loads(result[0].text)
        
        assert result_data["success"] is True
        assert result_data["objective_type"] == "place_on_tier"
        assert result_data["tier_name"] == "tier0"
        assert result_data["file_count"] == 3
        assert "created_objectives" in result_data
        assert len(result_data["created_objectives"]) == 3
        
        # Check each created objective
        for objective in result_data["created_objectives"]:
            assert objective["type"] == "place_on_tier"
            assert objective["tier_name"] == "tier0"
            assert objective["status"] == "active"
            assert "uuid" in objective
            assert "created" in objective
    
    @pytest.mark.asyncio
    async def test_apply_objective_to_files_exclude(self):
        """Test applying exclude-from-tier objectives to multiple files."""
        result = await handle_call_tool("apply_objective_to_files", {
            "file_paths": [
                "/old/file1.txt",
                "/old/file2.txt"
            ],
            "objective_type": "exclude_from_tier",
            "tier_name": "tier0"
        })
        
        result_data = json.loads(result[0].text)
        
        assert result_data["success"] is True
        assert result_data["objective_type"] == "exclude_from_tier"
        assert result_data["tier_name"] == "tier0"
        assert result_data["file_count"] == 2
        assert len(result_data["created_objectives"]) == 2
        
        for objective in result_data["created_objectives"]:
            assert objective["type"] == "exclude_from_tier"
            assert objective["tier_name"] == "tier0"


class TestJobManagementFeatures:
    """Test job management functionality."""
    
    @pytest.mark.asyncio
    async def test_list_jobs_all(self):
        """Test listing all jobs."""
        result = await handle_call_tool("list_jobs", {
            "status_filter": "all"
        })
        
        result_data = json.loads(result[0].text)
        
        assert "jobs" in result_data
        assert "total_count" in result_data
        assert "timestamp" in result_data
        assert result_data["total_count"] >= 0
        
        # Check job structure
        for job in result_data["jobs"]:
            assert "uuid" in job
            assert "name" in job
            assert "status" in job
            assert "progress" in job
    
    @pytest.mark.asyncio
    async def test_list_jobs_running(self):
        """Test listing only running jobs."""
        result = await handle_call_tool("list_jobs", {
            "status_filter": "running"
        })
        
        result_data = json.loads(result[0].text)
        
        assert "jobs" in result_data
        assert "total_count" in result_data
        
        # All returned jobs should be running
        for job in result_data["jobs"]:
            assert job["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_list_jobs_completed(self):
        """Test listing only completed jobs."""
        result = await handle_call_tool("list_jobs", {
            "status_filter": "completed"
        })
        
        result_data = json.loads(result[0].text)
        
        assert "jobs" in result_data
        assert "total_count" in result_data
        
        # All returned jobs should be completed
        for job in result_data["jobs"]:
            assert job["status"] == "completed"


class TestSystemStatusFeatures:
    """Test system status functionality."""
    
    @pytest.mark.asyncio
    async def test_get_system_status_success(self):
        """Test getting system status."""
        result = await handle_call_tool("get_system_status", {})
        
        result_data = json.loads(result[0].text)
        
        assert result_data["status"] == "healthy"
        assert "summary" in result_data
        assert "timestamp" in result_data
        
        summary = result_data["summary"]
        assert "total_volumes" in summary
        assert "total_files" in summary
        assert "total_jobs" in summary
        assert "running_jobs" in summary
        
        # Check that values are reasonable
        assert summary["total_volumes"] >= 0
        assert summary["total_files"] >= 0
        assert summary["total_jobs"] >= 0
        assert summary["running_jobs"] >= 0


class TestTagToObjectivesWorkflow:
    """Test complete tag-to-objectives workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_tag_to_objectives_workflow(self):
        """Test complete workflow: search by tag -> apply objectives."""
        # Step 1: Search for files by tag
        search_result = await handle_call_tool("search_files_by_tag", {
            "tag_name": "user.priority",
            "tag_value": "high"
        })
        
        search_data = json.loads(search_result[0].text)
        assert "matching_files" in search_data
        
        # Extract file paths
        file_paths = [file["path"] for file in search_data["matching_files"]]
        
        # Step 2: Apply objectives to found files
        if file_paths:
            objective_result = await handle_call_tool("apply_objective_to_files", {
                "file_paths": file_paths,
                "objective_type": "place_on_tier",
                "tier_name": "tier0"
            })
            
            objective_data = json.loads(objective_result[0].text)
            assert objective_data["success"] is True
            assert objective_data["file_count"] == len(file_paths)
            assert len(objective_data["created_objectives"]) == len(file_paths)
        
        # Step 3: Monitor jobs
        jobs_result = await handle_call_tool("list_jobs", {
            "status_filter": "all"
        })
        
        jobs_data = json.loads(jobs_result[0].text)
        assert "jobs" in jobs_data
        assert "total_count" in jobs_data
    
    @pytest.mark.asyncio
    async def test_archive_workflow(self):
        """Test archive workflow: exclude from tier0 -> place on archive."""
        # Step 1: Search for backup files
        search_result = await handle_call_tool("search_files_by_tag", {
            "tag_name": "user.project",
            "tag_value": "backup"
        })
        
        search_data = json.loads(search_result[0].text)
        file_paths = [file["path"] for file in search_data["matching_files"]]
        
        if file_paths:
            # Step 2: Exclude from tier0
            exclude_result = await handle_call_tool("apply_objective_to_files", {
                "file_paths": file_paths,
                "objective_type": "exclude_from_tier",
                "tier_name": "tier0"
            })
            
            exclude_data = json.loads(exclude_result[0].text)
            assert exclude_data["success"] is True
            
            # Step 3: Place on archive
            archive_result = await handle_call_tool("apply_objective_to_files", {
                "file_paths": file_paths,
                "objective_type": "place_on_tier",
                "tier_name": "archive"
            })
            
            archive_data = json.loads(archive_result[0].text)
            assert archive_data["success"] is True


class TestErrorHandling:
    """Test error handling for extended features."""
    
    @pytest.mark.asyncio
    async def test_unknown_tool_error(self):
        """Test error handling for unknown tools."""
        result = await handle_call_tool("unknown_tool", {
            "param1": "value1"
        })
        
        result_data = json.loads(result[0].text)
        
        assert "error" in result_data
        assert "Unknown tool: unknown_tool" in result_data["error"]
        assert "timestamp" in result_data
    
    @pytest.mark.asyncio
    async def test_missing_required_parameters(self):
        """Test error handling for missing required parameters."""
        # This should work with default values
        result = await handle_call_tool("search_files_by_tag", {
            "tag_name": "user.test"
        })
        
        result_data = json.loads(result[0].text)
        assert "tag_name" in result_data
        assert result_data["tag_name"] == "user.test"
        assert result_data["tag_value"] == ""  # Default value


class TestDataConsistency:
    """Test data consistency across operations."""
    
    @pytest.mark.asyncio
    async def test_tag_consistency(self):
        """Test that tags are consistent across operations."""
        # Set a tag
        set_result = await handle_call_tool("set_file_tag", {
            "file_path": "/test/consistency.txt",
            "tag_name": "user.consistency",
            "tag_value": "test"
        })
        
        set_data = json.loads(set_result[0].text)
        assert set_data["success"] is True
        
        # Search for the tag
        search_result = await handle_call_tool("search_files_by_tag", {
            "tag_name": "user.consistency",
            "tag_value": "test"
        })
        
        search_data = json.loads(search_result[0].text)
        assert search_data["total_count"] >= 1
        
        # Verify the file is in the results
        found_file = False
        for file_info in search_data["matching_files"]:
            if file_info["path"] == "/test/consistency.txt":
                found_file = True
                assert file_info["matching_tag"]["name"] == "user.consistency"
                assert file_info["matching_tag"]["value"] == "test"
                break
        
        assert found_file, "File with tag not found in search results"
    
    @pytest.mark.asyncio
    async def test_objective_consistency(self):
        """Test that objectives are created consistently."""
        # Create an objective
        objective_result = await handle_call_tool("place_on_tier", {
            "path": "/test/objective-consistency.txt",
            "tier_name": "tier1"
        })
        
        objective_data = json.loads(objective_result[0].text)
        assert objective_data["success"] is True
        
        # Verify objective details
        objective = objective_data["objective"]
        assert objective["type"] == "place_on_tier"
        assert objective["path"] == "/test/objective-consistency.txt"
        assert objective["tier_name"] == "tier1"
        assert objective["status"] == "active"
        assert "uuid" in objective
        assert "created" in objective


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
