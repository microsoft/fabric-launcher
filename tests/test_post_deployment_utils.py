"""
Unit tests for post_deployment_utils module.

Tests the utility functions for post-deployment tasks including folder lookups,
item definition retrieval, logical ID scanning and replacement, and item operations.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from fabric_launcher.post_deployment_utils import (
    create_or_update_fabric_item,
    get_folder_id_by_name,
    get_item_definition_from_repo,
    move_item_to_folder,
    replace_logical_ids,
    scan_logical_ids,
)


@pytest.fixture
def mock_client():
    """Create a mock Fabric REST client."""
    return Mock()


@pytest.fixture
def workspace_id():
    """Return a test workspace ID."""
    return "test-workspace-123"


@pytest.fixture
def temp_repo_dir():
    """Create a temporary repository directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir) / "repo"
        repo_dir.mkdir()

        # Create a sample notebook item
        notebook_dir = repo_dir / "Notebooks" / "TestNotebook.Notebook"
        notebook_dir.mkdir(parents=True)

        # Create .platform file
        platform_data = {
            "metadata": {"displayName": "Test Notebook", "type": "Notebook", "description": "A test notebook"},
            "config": {"logicalId": "logical-id-123"},
        }

        with open(notebook_dir / ".platform", "w", encoding="utf-8") as f:
            json.dump(platform_data, f)

        # Create notebook content file
        with open(notebook_dir / "notebook-content.py", "w", encoding="utf-8") as f:
            f.write("# Notebook content\nprint('Hello World')")

        # Create a lakehouse item with logical ID reference
        lakehouse_dir = repo_dir / "Lakehouses" / "TestLakehouse.Lakehouse"
        lakehouse_dir.mkdir(parents=True)

        lakehouse_platform = {
            "metadata": {"displayName": "Test Lakehouse", "type": "Lakehouse"},
            "config": {"logicalId": "lakehouse-logical-456"},
        }

        with open(lakehouse_dir / ".platform", "w", encoding="utf-8") as f:
            json.dump(lakehouse_platform, f)

        yield str(repo_dir)


class TestGetFolderIdByName:
    """Tests for get_folder_id_by_name function."""

    def test_get_folder_id_success(self, mock_client, workspace_id):
        """Test successfully finding a folder by name."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {"displayName": "Folder1", "id": "folder-id-1"},
                {"displayName": "Folder2", "id": "folder-id-2"},
                {"displayName": "Target Folder", "id": "target-folder-id"},
            ]
        }
        mock_client.get.return_value = mock_response

        # Execute
        result = get_folder_id_by_name("Target Folder", workspace_id, mock_client)

        # Assert
        assert result == "target-folder-id"
        mock_client.get.assert_called_once_with(f"v1/workspaces/{workspace_id}/folders")

    def test_get_folder_id_not_found(self, mock_client, workspace_id):
        """Test when folder is not found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": [{"displayName": "Folder1", "id": "folder-id-1"}]}
        mock_client.get.return_value = mock_response

        result = get_folder_id_by_name("NonExistent", workspace_id, mock_client)

        assert result is None

    def test_get_folder_id_api_error(self, mock_client, workspace_id):
        """Test handling of API errors."""
        mock_client.get.side_effect = Exception("API Error")

        result = get_folder_id_by_name("Test", workspace_id, mock_client)

        assert result is None


class TestGetItemDefinitionFromRepo:
    """Tests for get_item_definition_from_repo function."""

    def test_get_item_definition_success(self, temp_repo_dir):
        """Test successfully loading item definition."""
        platform_data, item_path = get_item_definition_from_repo("Notebooks/TestNotebook.Notebook", temp_repo_dir)

        assert platform_data["metadata"]["displayName"] == "Test Notebook"
        assert platform_data["metadata"]["type"] == "Notebook"
        assert platform_data["config"]["logicalId"] == "logical-id-123"
        assert Path(item_path).exists()

    def test_get_item_definition_not_found(self, temp_repo_dir):
        """Test error when item doesn't exist."""
        with pytest.raises(FileNotFoundError):
            get_item_definition_from_repo("NonExistent/Item.Notebook", temp_repo_dir)


class TestScanLogicalIds:
    """Tests for scan_logical_ids function."""

    def test_scan_logical_ids_success(self, temp_repo_dir, mock_client, workspace_id):
        """Test successfully scanning logical IDs."""
        # Mock API response for listing items
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {"displayName": "Test Notebook", "type": "Notebook", "id": "actual-notebook-id-789"},
                {"displayName": "Test Lakehouse", "type": "Lakehouse", "id": "actual-lakehouse-id-012"},
            ]
        }
        mock_client.get.return_value = mock_response

        # Execute
        result = scan_logical_ids(temp_repo_dir, workspace_id, mock_client)

        # Assert
        assert "logical-id-123" in result
        assert "lakehouse-logical-456" in result
        assert result["logical-id-123"] == "actual-notebook-id-789"
        assert result["lakehouse-logical-456"] == "actual-lakehouse-id-012"

    def test_scan_logical_ids_no_matches(self, temp_repo_dir, mock_client, workspace_id):
        """Test scanning when no items match in workspace."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": []}
        mock_client.get.return_value = mock_response

        result = scan_logical_ids(temp_repo_dir, workspace_id, mock_client)

        assert len(result) == 0


class TestReplaceLogicalIds:
    """Tests for replace_logical_ids function."""

    def test_replace_logical_ids_success(self):
        """Test successfully replacing logical IDs."""
        definition = {
            "metadata": {"name": "Test"},
            "config": {"reference": "logical-id-123", "connectionString": "lakehouse://logical-id-456/tables"},
        }

        logical_id_map = {"logical-id-123": "actual-id-abc", "logical-id-456": "actual-id-def"}

        result = replace_logical_ids(definition, logical_id_map)

        assert result["config"]["reference"] == "actual-id-abc"
        assert "actual-id-def" in result["config"]["connectionString"]
        assert "logical-id-123" not in json.dumps(result)

    def test_replace_logical_ids_no_matches(self):
        """Test replacement when no logical IDs are found."""
        definition = {"metadata": {"name": "Test"}, "config": {"value": "no-logical-ids-here"}}

        logical_id_map = {"logical-id-123": "actual-id-abc"}

        result = replace_logical_ids(definition, logical_id_map)

        assert result == definition


class TestCreateOrUpdateFabricItem:
    """Tests for create_or_update_fabric_item function."""

    def test_create_new_item_success(self, temp_repo_dir, mock_client, workspace_id):
        """Test creating a new Fabric item."""
        # Mock create response
        create_response = Mock()
        create_response.status_code = 201
        create_response.json.return_value = {"id": "new-item-id-123"}

        # Mock update response
        update_response = Mock()
        update_response.status_code = 200

        mock_client.post.side_effect = [create_response, update_response]

        result = create_or_update_fabric_item(
            item_name="Test Notebook",
            item_type="Notebook",
            item_relative_path="Notebooks/TestNotebook.Notebook",
            repository_directory=temp_repo_dir,
            workspace_id=workspace_id,
            client=mock_client,
            endpoint="notebooks",
        )

        assert result == "new-item-id-123"
        assert mock_client.post.call_count == 2  # create + update

    def test_update_existing_item(self, temp_repo_dir, mock_client, workspace_id):
        """Test updating an existing item."""
        # Mock create response (409 conflict - already exists)
        create_response = Mock()
        create_response.status_code = 409

        # Mock list response to find existing item
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {
            "value": [{"displayName": "Test Notebook", "type": "Notebook", "id": "existing-item-id-456"}]
        }

        # Mock update response
        update_response = Mock()
        update_response.status_code = 200

        mock_client.post.side_effect = [create_response, update_response]
        mock_client.get.return_value = list_response

        result = create_or_update_fabric_item(
            item_name="Test Notebook",
            item_type="Notebook",
            item_relative_path="Notebooks/TestNotebook.Notebook",
            repository_directory=temp_repo_dir,
            workspace_id=workspace_id,
            client=mock_client,
            endpoint="notebooks",
        )

        assert result == "existing-item-id-456"


class TestMoveItemToFolder:
    """Tests for move_item_to_folder function."""

    def test_move_item_success(self, mock_client, workspace_id):
        """Test successfully moving an item to a folder."""
        # Mock list items response
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {
            "value": [{"displayName": "Test Notebook", "type": "Notebook", "id": "item-id-123"}]
        }

        # Mock folders response
        folders_response = Mock()
        folders_response.status_code = 200
        folders_response.json.return_value = {"value": [{"displayName": "Target Folder", "id": "folder-id-456"}]}

        # Mock move response
        move_response = Mock()
        move_response.status_code = 200

        mock_client.get.side_effect = [list_response, folders_response]
        mock_client.post.return_value = move_response

        result = move_item_to_folder(
            item_name="Test Notebook",
            item_type="Notebook",
            folder_name="Target Folder",
            workspace_id=workspace_id,
            client=mock_client,
        )

        assert result is True
        mock_client.post.assert_called_once()

    def test_move_item_not_found(self, mock_client, workspace_id):
        """Test moving an item that doesn't exist."""
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {"value": []}

        mock_client.get.return_value = list_response

        result = move_item_to_folder(
            item_name="NonExistent",
            item_type="Notebook",
            folder_name="Target",
            workspace_id=workspace_id,
            client=mock_client,
        )

        assert result is False

    def test_move_item_folder_not_found(self, mock_client, workspace_id):
        """Test moving to a folder that doesn't exist."""
        # Mock list items (item exists)
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {"value": [{"displayName": "Test", "type": "Notebook", "id": "item-123"}]}

        # Mock folders (folder doesn't exist)
        folders_response = Mock()
        folders_response.status_code = 200
        folders_response.json.return_value = {"value": []}

        mock_client.get.side_effect = [list_response, folders_response]

        result = move_item_to_folder(
            item_name="Test",
            item_type="Notebook",
            folder_name="NonExistent",
            workspace_id=workspace_id,
            client=mock_client,
        )

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
