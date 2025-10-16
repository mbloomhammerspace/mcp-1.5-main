#!/usr/bin/env python3
"""
Unit tests for the Volume Canvas MCP Server
Tests all MCP endpoints and functionality using pytest and asyncio.
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
from volume_canvas_mcp_server import VolumeCanvasAIQMCPServer


class TestVolumeCanvasAIQMCPServer:
    """Test suite for Volume Canvas AIQ MCP Server."""
    
    @pytest_asyncio.fixture
    async def mock_server(self):
        """Create a mock server instance for testing."""
        with patch('volume_canvas_mcp_server.HAMMERSPACE_AVAILABLE', True):
            with patch('volume_canvas_mcp_server.HammerspaceClient') as mock_client:
                with patch('volume_canvas_mcp_server.VolumeMovementManager') as mock_manager:
                    # Create mock objects
                    mock_client_instance = AsyncMock()
                    mock_manager_instance = AsyncMock()
                    
                    # Configure mock manager
                    mock_manager_instance.volume_categories = {
                        'lss_volumes': [Mock(uuid='lss-1', name='LSS Volume 1', state=Mock(value='UP'), 
                                           size_bytes=1000000000, used_bytes=500000000, 
                                           created='2024-01-01T00:00:00Z', modified='2024-01-01T00:00:00Z')],
                        'tier0_volumes': [Mock(uuid='tier0-1', name='Tier0 Volume 1', state=Mock(value='UP'),
                                             size_bytes=2000000000, used_bytes=1000000000,
                                             created='2024-01-01T00:00:00Z', modified='2024-01-01T00:00:00Z')]
                    }
                    mock_manager_instance.shares = {
                        'share-1': Mock(uuid='share-1', name='Test Share', path='/test',
                                       total_number_of_files=100, created='2024-01-01T00:00:00Z',
                                       modified='2024-01-01T00:00:00Z', volume_uuid='lss-1')
                    }
                    mock_manager_instance.nodes = [Mock(), Mock()]
                    
                    mock_manager.return_value = mock_manager_instance
                    mock_client.return_value = mock_client_instance
                    
                    # Create server instance
                    server = VolumeCanvasAIQMCPServer()
                    server.manager = mock_manager_instance
                    server.client = mock_client_instance
                    
                    yield server
    
    @pytest_asyncio.fixture
    async def mock_server_no_manager(self):
        """Create a mock server instance without manager for error testing."""
        with patch('volume_canvas_mcp_server.HAMMERSPACE_AVAILABLE', False):
            server = VolumeCanvasAIQMCPServer()
            server.manager = None
            server.client = None
            yield server


class TestVolumeManagement:
    """Test volume management functions."""
    
    @pytest.mark.asyncio
    async def test_list_volumes_success(self, mock_server):
        """Test successful volume listing."""
        # Get the list_volumes function
        list_volumes_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'list_volumes':
                list_volumes_func = func
                break
        
        assert list_volumes_func is not None, "list_volumes function not found"
        
        # Test with default parameters
        result = await list_volumes_func(filter="all", storage_system="production")
        
        assert "volumes" in result
        assert len(result["volumes"]) == 2
        assert result["volumes"][0]["uuid"] == "lss-1"
        assert result["volumes"][0]["name"] == "LSS Volume 1"
        assert result["volumes"][0]["type"] == "lss"
        assert result["volumes"][1]["uuid"] == "tier0-1"
        assert result["volumes"][1]["name"] == "Tier0 Volume 1"
        assert result["volumes"][1]["type"] == "tier0"
    
    @pytest.mark.asyncio
    async def test_list_volumes_with_filter(self, mock_server):
        """Test volume listing with filter."""
        # Get the list_volumes function
        list_volumes_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'list_volumes':
                list_volumes_func = func
                break
        
        # Test with lss filter
        result = await list_volumes_func(filter="lss", storage_system="production")
        
        assert "volumes" in result
        assert len(result["volumes"]) == 1
        assert result["volumes"][0]["type"] == "lss"
    
    @pytest.mark.asyncio
    async def test_list_volumes_no_manager(self, mock_server_no_manager):
        """Test volume listing when manager is not available."""
        # Get the list_volumes function
        list_volumes_func = None
        for func in mock_server_no_manager.aiq._functions.values():
            if func.__name__ == 'list_volumes':
                list_volumes_func = func
                break
        
        result = await list_volumes_func(filter="all", storage_system="production")
        
        assert "error" in result
        assert "volumes" in result
        assert result["volumes"] == []
        assert result["error"] == "Manager not initialized"
    
    @pytest.mark.asyncio
    async def test_list_shares_success(self, mock_server):
        """Test successful share listing."""
        # Get the list_shares function
        list_shares_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'list_shares':
                list_shares_func = func
                break
        
        result = await list_shares_func(volume_uuid="lss-1", storage_system="production")
        
        assert "shares" in result
        assert len(result["shares"]) == 1
        assert result["shares"][0]["uuid"] == "share-1"
        assert result["shares"][0]["name"] == "Test Share"
        assert result["shares"][0]["path"] == "/test"
        assert result["shares"][0]["file_count"] == 100


class TestFileManagement:
    """Test file management functions."""
    
    @pytest.mark.asyncio
    async def test_list_files_success(self, mock_server):
        """Test successful file listing."""
        # Mock the search_files method
        mock_file = Mock(
            name="test_file.txt",
            path="/test/test_file.txt",
            size_bytes=1024,
            created="2024-01-01T00:00:00Z",
            modified="2024-01-01T00:00:00Z",
            share_uuid="share-1",
            volume_uuid="lss-1"
        )
        mock_server.manager.client.search_files = AsyncMock(return_value=[mock_file])
        
        # Get the list_files function
        list_files_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'list_files':
                list_files_func = func
                break
        
        result = await list_files_func(path="/test", limit=100, storage_system="production")
        
        assert "files" in result
        assert len(result["files"]) == 1
        assert result["files"][0]["name"] == "test_file.txt"
        assert result["files"][0]["path"] == "/test/test_file.txt"
        assert result["files"][0]["size_bytes"] == 1024
    
    @pytest.mark.asyncio
    async def test_search_files_success(self, mock_server):
        """Test successful file search."""
        # Mock the search_files method
        mock_file = Mock(
            name="test_file.txt",
            path="/test/test_file.txt",
            size_bytes=1024,
            share_uuid="share-1",
            volume_uuid="lss-1"
        )
        mock_server.manager.client.search_files = AsyncMock(return_value=[mock_file])
        
        # Get the search_files function
        search_files_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'search_files':
                search_files_func = func
                break
        
        result = await search_files_func(
            query="test",
            search_by_tags=True,
            search_by_path=True,
            case_sensitive=False,
            storage_system="production"
        )
        
        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["name"] == "test_file.txt"
    
    @pytest.mark.asyncio
    async def test_search_files_case_sensitive(self, mock_server):
        """Test case-sensitive file search."""
        # Mock the search_files method
        mock_file = Mock(
            name="Test_File.txt",
            path="/test/Test_File.txt",
            size_bytes=1024,
            share_uuid="share-1",
            volume_uuid="lss-1"
        )
        mock_server.manager.client.search_files = AsyncMock(return_value=[mock_file])
        
        # Get the search_files function
        search_files_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'search_files':
                search_files_func = func
                break
        
        # Test case-sensitive search
        result = await search_files_func(
            query="test",
            search_by_tags=True,
            search_by_path=True,
            case_sensitive=True,
            storage_system="production"
        )
        
        # Should not find "Test_File.txt" when searching for "test" case-sensitively
        assert "results" in result
        assert len(result["results"]) == 0


class TestDataMovement:
    """Test data movement functions."""
    
    @pytest.mark.asyncio
    async def test_copy_files_success(self, mock_server):
        """Test successful file copy operation."""
        # Mock the copy_files method
        mock_job = Mock(
            uuid="job-1",
            name="Copy Job",
            status=Mock(value="RUNNING"),
            progress=50.0,
            created="2024-01-01T00:00:00Z"
        )
        mock_server.manager.copy_files = AsyncMock(return_value=mock_job)
        
        # Get the copy_files function
        copy_files_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'copy_files':
                copy_files_func = func
                break
        
        result = await copy_files_func(
            source_type="lss",
            target_type="tier0",
            path="/test",
            recursive=True,
            storage_system="production"
        )
        
        assert result["success"] is True
        assert "job" in result
        assert result["job"]["uuid"] == "job-1"
        assert result["job"]["name"] == "Copy Job"
        assert result["job"]["status"] == "RUNNING"
        assert result["job"]["progress"] == 50.0
    
    @pytest.mark.asyncio
    async def test_clone_files_success(self, mock_server):
        """Test successful file clone operation."""
        # Mock the clone_files method
        mock_job = Mock(
            uuid="job-2",
            name="Clone Job",
            status=Mock(value="RUNNING"),
            progress=25.0,
            created="2024-01-01T00:00:00Z"
        )
        mock_server.manager.clone_files = AsyncMock(return_value=mock_job)
        
        # Get the clone_files function
        clone_files_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'clone_files':
                clone_files_func = func
                break
        
        result = await clone_files_func(
            source_type="lss",
            target_type="tier1",
            path="/test",
            storage_system="production"
        )
        
        assert result["success"] is True
        assert "job" in result
        assert result["job"]["uuid"] == "job-2"
        assert result["job"]["name"] == "Clone Job"
    
    @pytest.mark.asyncio
    async def test_move_files_success(self, mock_server):
        """Test successful file move operation."""
        # Mock the move_files method
        mock_job = Mock(
            uuid="job-3",
            name="Move Job",
            status=Mock(value="RUNNING"),
            progress=75.0,
            created="2024-01-01T00:00:00Z"
        )
        mock_server.manager.move_files = AsyncMock(return_value=mock_job)
        
        # Get the move_files function
        move_files_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'move_files':
                move_files_func = func
                break
        
        result = await move_files_func(
            source_type="tier0",
            target_type="tier1",
            path="/test",
            storage_system="production"
        )
        
        assert result["success"] is True
        assert "job" in result
        assert result["job"]["uuid"] == "job-3"
        assert result["job"]["name"] == "Move Job"


class TestObjectiveManagement:
    """Test objective management functions."""
    
    @pytest.mark.asyncio
    async def test_place_on_tier_success(self, mock_server):
        """Test successful place-on-tier objective creation."""
        # Mock the place_on_tier method
        mock_objective = Mock(
            uuid="obj-1",
            name="Place on Tier Objective",
            objective_type=Mock(value="PLACE_ON_TIER"),
            state=Mock(value="ACTIVE"),
            created="2024-01-01T00:00:00Z"
        )
        mock_server.manager.place_on_tier = AsyncMock(return_value=mock_objective)
        
        # Get the place_on_tier function
        place_on_tier_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'place_on_tier':
                place_on_tier_func = func
                break
        
        result = await place_on_tier_func(
            volume_type="lss",
            path="/test",
            tier_name="tier1",
            storage_system="production"
        )
        
        assert result["success"] is True
        assert "objective" in result
        assert result["objective"]["uuid"] == "obj-1"
        assert result["objective"]["name"] == "Place on Tier Objective"
        assert result["objective"]["objective_type"] == "PLACE_ON_TIER"
        assert result["objective"]["state"] == "ACTIVE"
    
    @pytest.mark.asyncio
    async def test_exclude_from_tier_success(self, mock_server):
        """Test successful exclude-from-tier objective creation."""
        # Mock the exclude_from_tier method
        mock_objective = Mock(
            uuid="obj-2",
            name="Exclude from Tier Objective",
            objective_type=Mock(value="EXCLUDE_FROM_TIER"),
            state=Mock(value="ACTIVE"),
            created="2024-01-01T00:00:00Z"
        )
        mock_server.manager.exclude_from_tier = AsyncMock(return_value=mock_objective)
        
        # Get the exclude_from_tier function
        exclude_from_tier_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'exclude_from_tier':
                exclude_from_tier_func = func
                break
        
        result = await exclude_from_tier_func(
            volume_type="tier0",
            path="/test",
            tier_name="tier0",
            storage_system="production"
        )
        
        assert result["success"] is True
        assert "objective" in result
        assert result["objective"]["uuid"] == "obj-2"
        assert result["objective"]["name"] == "Exclude from Tier Objective"
        assert result["objective"]["objective_type"] == "EXCLUDE_FROM_TIER"


class TestJobManagement:
    """Test job management functions."""
    
    @pytest.mark.asyncio
    async def test_list_jobs_success(self, mock_server):
        """Test successful job listing."""
        # Mock the list_active_jobs method
        mock_job = Mock(
            uuid="job-1",
            name="Test Job",
            status=Mock(value="RUNNING"),
            progress=50.0,
            created="2024-01-01T00:00:00Z",
            started="2024-01-01T00:00:00Z",
            completed=None
        )
        mock_server.manager.list_active_jobs = AsyncMock(return_value=[mock_job])
        
        # Get the list_jobs function
        list_jobs_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'list_jobs':
                list_jobs_func = func
                break
        
        result = await list_jobs_func(storage_system="production", status_filter="all")
        
        assert "jobs" in result
        assert len(result["jobs"]) == 1
        assert result["jobs"][0]["uuid"] == "job-1"
        assert result["jobs"][0]["name"] == "Test Job"
        assert result["jobs"][0]["status"] == "RUNNING"
        assert result["jobs"][0]["progress"] == 50.0
    
    @pytest.mark.asyncio
    async def test_get_job_status_success(self, mock_server):
        """Test successful job status retrieval."""
        # Mock the get_data_movement_job method
        mock_job = Mock(
            uuid="job-1",
            name="Test Job",
            status=Mock(value="COMPLETED"),
            progress=100.0,
            created="2024-01-01T00:00:00Z",
            started="2024-01-01T00:00:00Z",
            completed="2024-01-01T01:00:00Z",
            error_message=None
        )
        mock_server.manager.client.get_data_movement_job = AsyncMock(return_value=mock_job)
        
        # Get the get_job_status function
        get_job_status_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'get_job_status':
                get_job_status_func = func
                break
        
        result = await get_job_status_func(job_uuid="job-1", storage_system="production")
        
        assert result["uuid"] == "job-1"
        assert result["name"] == "Test Job"
        assert result["status"] == "COMPLETED"
        assert result["progress"] == 100.0
        assert result["completed"] == "2024-01-01T01:00:00Z"


class TestTagManagement:
    """Test tag management functions."""
    
    @pytest.mark.asyncio
    async def test_get_tags_success(self, mock_server):
        """Test successful tag retrieval."""
        # Get the get_tags function
        get_tags_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'get_tags':
                get_tags_func = func
                break
        
        result = await get_tags_func(path="/test", storage_system="production")
        
        assert "tags" in result
        assert "path" in result
        assert result["path"] == "/test"
    
    @pytest.mark.asyncio
    async def test_set_tag_success(self, mock_server):
        """Test successful tag setting."""
        # Get the set_tag function
        set_tag_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'set_tag':
                set_tag_func = func
                break
        
        result = await set_tag_func(
            path="/test",
            tag_name="environment",
            tag_value="production",
            storage_system="production"
        )
        
        assert result["success"] is True
        assert "message" in result
        assert "environment" in result["message"]
        assert "production" in result["message"]
    
    @pytest.mark.asyncio
    async def test_clear_all_tags_success(self, mock_server):
        """Test successful tag clearing."""
        # Get the clear_all_tags function
        clear_all_tags_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'clear_all_tags':
                clear_all_tags_func = func
                break
        
        result = await clear_all_tags_func(path="/test", storage_system="production")
        
        assert result["success"] is True
        assert "message" in result
        assert "cleared" in result["message"]


class TestSystemAnalysis:
    """Test system analysis functions."""
    
    @pytest.mark.asyncio
    async def test_get_system_status_success(self, mock_server):
        """Test successful system status retrieval."""
        # Get the get_system_status function
        get_system_status_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'get_system_status':
                get_system_status_func = func
                break
        
        result = await get_system_status_func(storage_system="production")
        
        assert result["status"] == "success"
        assert "data" in result
        assert "summary" in result["data"]
        assert "health" in result["data"]
        assert "last_updated" in result["data"]
        assert result["data"]["summary"]["total_nodes"] == 2
        assert result["data"]["summary"]["total_volumes"] == 2
        assert result["data"]["summary"]["total_shares"] == 1
    
    @pytest.mark.asyncio
    async def test_analyze_volume_constraints_success(self, mock_server):
        """Test successful volume constraint analysis."""
        # Get the analyze_volume_constraints function
        analyze_volume_constraints_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'analyze_volume_constraints':
                analyze_volume_constraints_func = func
                break
        
        result = await analyze_volume_constraints_func(
            volume_type="lss",
            storage_system="production"
        )
        
        assert "analysis" in result
        assert "capacity" in result["analysis"]
        assert "durability" in result["analysis"]
        assert "performance" in result["analysis"]
        assert "constraints" in result["analysis"]


class TestDebugAndDiagnostic:
    """Test debug and diagnostic functions."""
    
    @pytest.mark.asyncio
    async def test_get_objective_debug_info_success(self, mock_server):
        """Test successful objective debug info retrieval."""
        # Get the get_objective_debug_info function
        get_objective_debug_info_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'get_objective_debug_info':
                get_objective_debug_info_func = func
                break
        
        result = await get_objective_debug_info_func(
            objective_name="test-objective",
            storage_system="production"
        )
        
        assert "debug_info" in result
        assert "total_objectives" in result["debug_info"]
        assert "successful" in result["debug_info"]
        assert "failed" in result["debug_info"]
        assert "in_progress" in result["debug_info"]
        assert "failed_objectives" in result["debug_info"]
    
    @pytest.mark.asyncio
    async def test_verify_data_integrity_success(self, mock_server):
        """Test successful data integrity verification."""
        # Mock the verify_data_integrity method
        mock_result = {"integrity": "verified", "files_checked": 100}
        mock_server.manager.verify_data_integrity = AsyncMock(return_value=mock_result)
        
        # Get the verify_data_integrity function
        verify_data_integrity_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'verify_data_integrity':
                verify_data_integrity_func = func
                break
        
        result = await verify_data_integrity_func(
            volume_type="lss",
            path="/test",
            storage_system="production"
        )
        
        assert result["success"] is True
        assert "result" in result
        assert "integrity_status" in result
        assert result["integrity_status"] == "verified"


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_function_with_exception(self, mock_server):
        """Test function behavior when an exception occurs."""
        # Mock an exception in the manager
        mock_server.manager.volume_categories = {}
        mock_server.manager.volume_categories.items.side_effect = Exception("Test exception")
        
        # Get the list_volumes function
        list_volumes_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'list_volumes':
                list_volumes_func = func
                break
        
        result = await list_volumes_func(filter="all", storage_system="production")
        
        assert "error" in result
        assert "volumes" in result
        assert result["volumes"] == []
        assert "Test exception" in result["error"]
    
    @pytest.mark.asyncio
    async def test_no_manager_error(self, mock_server_no_manager):
        """Test error handling when manager is not available."""
        # Get the list_volumes function
        list_volumes_func = None
        for func in mock_server_no_manager.aiq._functions.values():
            if func.__name__ == 'list_volumes':
                list_volumes_func = func
                break
        
        result = await list_volumes_func(filter="all", storage_system="production")
        
        assert "error" in result
        assert result["error"] == "Manager not initialized"
        assert "volumes" in result
        assert result["volumes"] == []


class TestStorageSystemSwitching:
    """Test storage system switching functionality."""
    
    @pytest.mark.asyncio
    async def test_storage_system_switching(self, mock_server):
        """Test switching between storage systems."""
        # Get the list_volumes function
        list_volumes_func = None
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'list_volumes':
                list_volumes_func = func
                break
        
        # Test with different storage system
        result = await list_volumes_func(filter="all", storage_system="se-lab")
        
        assert "volumes" in result
        # The _switch_storage_system method should be called
        assert mock_server.current_storage_system == "se-lab"


# Integration tests
class TestIntegration:
    """Integration tests for the complete workflow."""
    
    @pytest.mark.asyncio
    async def test_volume_migration_workflow(self, mock_server):
        """Test complete volume migration workflow."""
        # Mock all required methods
        mock_server.manager.client.search_files = AsyncMock(return_value=[])
        mock_job = Mock(
            uuid="job-1",
            name="Migration Job",
            status=Mock(value="RUNNING"),
            progress=0.0,
            created="2024-01-01T00:00:00Z"
        )
        mock_server.manager.copy_files = AsyncMock(return_value=mock_job)
        mock_server.manager.verify_data_integrity = AsyncMock(return_value={"integrity": "verified"})
        
        # Get functions
        list_volumes_func = None
        list_files_func = None
        copy_files_func = None
        verify_data_integrity_func = None
        
        for func in mock_server.aiq._functions.values():
            if func.__name__ == 'list_volumes':
                list_volumes_func = func
            elif func.__name__ == 'list_files':
                list_files_func = func
            elif func.__name__ == 'copy_files':
                copy_files_func = func
            elif func.__name__ == 'verify_data_integrity':
                verify_data_integrity_func = func
        
        # Execute workflow
        volumes = await list_volumes_func(filter="all", storage_system="production")
        files = await list_files_func(path="/test", storage_system="production")
        copy_result = await copy_files_func(
            source_type="lss",
            target_type="tier0",
            path="/test",
            storage_system="production"
        )
        verify_result = await verify_data_integrity_func(
            volume_type="tier0",
            path="/test",
            storage_system="production"
        )
        
        # Verify workflow results
        assert "volumes" in volumes
        assert "files" in files
        assert copy_result["success"] is True
        assert verify_result["success"] is True


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
