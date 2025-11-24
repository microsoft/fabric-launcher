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
    create_accelerated_shortcut_in_kql_db,
    create_or_update_fabric_item,
    create_shortcut,
    exec_kql_command,
    exec_sql_query,
    get_folder_id_by_name,
    get_item_definition_from_repo,
    get_kusto_query_uri,
    get_sql_endpoint,
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


class TestGetKustoQueryUri:
    """Tests for get_kusto_query_uri function."""

    def test_get_kusto_query_uri_success(self, mock_client, workspace_id):
        """Test successfully retrieving Kusto query URI."""
        # Mock list items response
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {
            "value": [
                {"displayName": "TestEventhouse", "type": "Eventhouse", "id": "eventhouse-id-123"},
                {"displayName": "OtherItem", "type": "Lakehouse", "id": "other-id-456"},
            ]
        }

        # Mock eventhouse properties response
        eventhouse_response = Mock()
        eventhouse_response.status_code = 200
        eventhouse_response.json.return_value = {
            "properties": {"queryServiceUri": "https://test.kusto.fabric.microsoft.com"}
        }

        mock_client.get.side_effect = [list_response, eventhouse_response]

        result = get_kusto_query_uri(workspace_id, "TestEventhouse", mock_client)

        assert result == "https://test.kusto.fabric.microsoft.com"
        assert mock_client.get.call_count == 2

    def test_get_kusto_query_uri_eventhouse_not_found(self, mock_client, workspace_id):
        """Test when Eventhouse is not found."""
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {"value": []}

        mock_client.get.return_value = list_response

        with pytest.raises(ValueError, match="Eventhouse 'NonExistent' not found"):
            get_kusto_query_uri(workspace_id, "NonExistent", mock_client)

    def test_get_kusto_query_uri_missing_property(self, mock_client, workspace_id):
        """Test when queryServiceUri is missing from properties."""
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {
            "value": [{"displayName": "TestEventhouse", "type": "Eventhouse", "id": "eventhouse-id-123"}]
        }

        eventhouse_response = Mock()
        eventhouse_response.status_code = 200
        eventhouse_response.json.return_value = {"properties": {}}

        mock_client.get.side_effect = [list_response, eventhouse_response]

        with pytest.raises(ValueError, match="queryServiceUri not found"):
            get_kusto_query_uri(workspace_id, "TestEventhouse", mock_client)

    def test_get_kusto_query_uri_api_error(self, mock_client, workspace_id):
        """Test handling of API errors."""
        mock_client.get.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            get_kusto_query_uri(workspace_id, "TestEventhouse", mock_client)


class TestExecKqlCommand:
    """Tests for exec_kql_command function."""

    @pytest.fixture
    def mock_notebookutils(self):
        """Create a mock notebookutils object."""
        mock_nb = Mock()
        mock_nb.credentials.getToken.return_value = "test-token-123"
        return mock_nb

    def test_exec_kql_command_success(self, mock_notebookutils):
        """Test successfully executing a KQL command."""
        from unittest.mock import patch

        kusto_uri = "https://test.kusto.fabric.microsoft.com"
        kql_db_name = "TestDatabase"
        kql_command = ".show tables"

        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"Tables": [{"TableName": "Table1"}, {"TableName": "Table2"}]}

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = exec_kql_command(kusto_uri, kql_db_name, kql_command, mock_notebookutils)

            assert result is not None
            assert "Tables" in result
            mock_post.assert_called_once()

            # Verify the call arguments
            call_args = mock_post.call_args
            assert kusto_uri in call_args[0][0]
            assert call_args[1]["json"]["csl"] == kql_command
            assert call_args[1]["json"]["db"] == kql_db_name

    def test_exec_kql_command_failure(self, mock_notebookutils):
        """Test handling of KQL command failure."""
        from unittest.mock import patch

        kusto_uri = "https://test.kusto.fabric.microsoft.com"
        kql_db_name = "TestDatabase"
        kql_command = ".show tables"

        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "Bad request"

        with patch("requests.post", return_value=mock_response):
            result = exec_kql_command(kusto_uri, kql_db_name, kql_command, mock_notebookutils)

            assert result is None

    def test_exec_kql_command_network_error(self, mock_notebookutils):
        """Test handling of network errors."""
        from unittest.mock import patch

        import requests

        kusto_uri = "https://test.kusto.fabric.microsoft.com"
        kql_db_name = "TestDatabase"
        kql_command = ".show tables"

        with patch("requests.post", side_effect=requests.RequestException("Network error")):
            result = exec_kql_command(kusto_uri, kql_db_name, kql_command, mock_notebookutils)

            assert result is None


class TestCreateShortcut:
    """Tests for create_shortcut function."""

    @pytest.fixture
    def mock_notebookutils(self):
        """Create a mock notebookutils object."""
        mock_nb = Mock()
        mock_nb.credentials.getToken.return_value = "test-token-123"
        return mock_nb

    def test_create_shortcut_success(self, mock_client, workspace_id, mock_notebookutils):
        """Test successfully creating a shortcut."""
        from unittest.mock import patch

        # Mock list items response
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {
            "value": [{"displayName": "TargetLakehouse", "type": "Lakehouse", "id": "target-id-123"}]
        }

        mock_client.get.return_value = list_response
        mock_client.default_base_url = "https://api.fabric.microsoft.com"

        # Mock shortcut creation response
        shortcut_response = Mock()
        shortcut_response.ok = True
        shortcut_response.status_code = 201
        shortcut_response.json.return_value = {"name": "TestShortcut", "path": "Tables"}

        with patch("requests.post", return_value=shortcut_response) as mock_post:
            result = create_shortcut(
                target_workspace_id=workspace_id,
                target_item_name="TargetLakehouse",
                target_item_type="Lakehouse",
                target_path="Tables",
                target_shortcut_name="TestShortcut",
                source_workspace_id=workspace_id,
                source_item_id="source-id-456",
                source_path="Tables/SourceTable",
                client=mock_client,
                notebookutils=mock_notebookutils,
            )

            assert result is not None
            assert result["name"] == "TestShortcut"
            mock_post.assert_called_once()

    def test_create_shortcut_target_not_found(self, mock_client, workspace_id, mock_notebookutils):
        """Test creating shortcut when target item not found."""
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {"value": []}

        mock_client.get.return_value = list_response

        result = create_shortcut(
            target_workspace_id=workspace_id,
            target_item_name="NonExistent",
            target_item_type="Lakehouse",
            target_path="Tables",
            target_shortcut_name="TestShortcut",
            source_workspace_id=workspace_id,
            source_item_id="source-id-456",
            source_path="Tables/SourceTable",
            client=mock_client,
            notebookutils=mock_notebookutils,
        )

        assert result is None

    def test_create_shortcut_api_error(self, mock_client, workspace_id, mock_notebookutils):
        """Test handling of API errors."""
        from unittest.mock import patch

        import requests

        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {
            "value": [{"displayName": "TargetLakehouse", "type": "Lakehouse", "id": "target-id-123"}]
        }

        mock_client.get.return_value = list_response
        mock_client.default_base_url = "https://api.fabric.microsoft.com"

        with patch("requests.post", side_effect=requests.RequestException("Network error")):
            result = create_shortcut(
                target_workspace_id=workspace_id,
                target_item_name="TargetLakehouse",
                target_item_type="Lakehouse",
                target_path="Tables",
                target_shortcut_name="TestShortcut",
                source_workspace_id=workspace_id,
                source_item_id="source-id-456",
                source_path="Tables/SourceTable",
                client=mock_client,
                notebookutils=mock_notebookutils,
            )

            assert result is None


class TestCreateAcceleratedShortcutInKqlDb:
    """Tests for create_accelerated_shortcut_in_kql_db function."""

    @pytest.fixture
    def mock_notebookutils(self):
        """Create a mock notebookutils object."""
        mock_nb = Mock()
        mock_nb.credentials.getToken.return_value = "test-token-123"

        # Mock lakehouse properties
        mock_properties = Mock()
        mock_properties.properties = {
            "oneLakeTablesPath": "abfss://workspace@onelake.dfs.fabric.microsoft.com/lakehouse-id/Tables"
        }
        mock_nb.lakehouse.getWithProperties.return_value = mock_properties

        return mock_nb

    def test_create_accelerated_shortcut_success(self, mock_client, workspace_id, mock_notebookutils):
        """Test successfully creating an accelerated shortcut."""
        from unittest.mock import patch

        # Mock item list responses (for multiple lookups)
        kql_db_list = Mock()
        kql_db_list.status_code = 200
        kql_db_list.json.return_value = {
            "value": [{"displayName": "TestKQLDB", "type": "KQLDatabase", "id": "kqldb-id-123"}]
        }

        eventhouse_list = Mock()
        eventhouse_list.status_code = 200
        eventhouse_list.json.return_value = {
            "value": [{"displayName": "TestEventhouse", "type": "Eventhouse", "id": "eventhouse-id-456"}]
        }

        eventhouse_props = Mock()
        eventhouse_props.status_code = 200
        eventhouse_props.json.return_value = {
            "properties": {"queryServiceUri": "https://test.kusto.fabric.microsoft.com"}
        }

        mock_client.get.side_effect = [kql_db_list, eventhouse_list, eventhouse_props, kql_db_list]
        mock_client.default_base_url = "https://api.fabric.microsoft.com"

        # Mock requests
        mock_shortcut_response = Mock()
        mock_shortcut_response.ok = True
        mock_shortcut_response.status_code = 201
        mock_shortcut_response.json.return_value = {"status": "success"}

        mock_kql_response = Mock()
        mock_kql_response.ok = True
        mock_kql_response.status_code = 200
        mock_kql_response.json.return_value = {"status": "success"}

        with patch("requests.post", side_effect=[mock_shortcut_response, mock_kql_response, mock_kql_response]):
            result = create_accelerated_shortcut_in_kql_db(
                target_workspace_id=workspace_id,
                target_kql_db_name="TestKQLDB",
                target_shortcut_name="TestShortcut",
                source_workspace_id=workspace_id,
                source_item_id="lakehouse-id-789",
                source_path="Tables/meters",
                target_eventhouse_name="TestEventhouse",
                source_lakehouse_name="TestLakehouse",
                client=mock_client,
                notebookutils=mock_notebookutils,
            )

            assert result is True

    def test_create_accelerated_shortcut_shortcut_failure(self, mock_client, workspace_id, mock_notebookutils):
        """Test when shortcut creation fails."""
        from unittest.mock import patch

        kql_db_list = Mock()
        kql_db_list.status_code = 200
        kql_db_list.json.return_value = {
            "value": [{"displayName": "TestKQLDB", "type": "KQLDatabase", "id": "kqldb-id-123"}]
        }

        mock_client.get.return_value = kql_db_list
        mock_client.default_base_url = "https://api.fabric.microsoft.com"

        mock_shortcut_response = Mock()
        mock_shortcut_response.ok = False
        mock_shortcut_response.status_code = 400

        with patch("requests.post", return_value=mock_shortcut_response):
            result = create_accelerated_shortcut_in_kql_db(
                target_workspace_id=workspace_id,
                target_kql_db_name="TestKQLDB",
                target_shortcut_name="TestShortcut",
                source_workspace_id=workspace_id,
                source_item_id="lakehouse-id-789",
                source_path="Tables/meters",
                target_eventhouse_name="TestEventhouse",
                source_lakehouse_name="TestLakehouse",
                client=mock_client,
                notebookutils=mock_notebookutils,
            )

            assert result is False


class TestGetSqlEndpoint:
    """Tests for get_sql_endpoint function."""

    def test_get_sql_endpoint_lakehouse_success(self, mock_client, workspace_id):
        """Test successfully retrieving SQL endpoint for Lakehouse."""
        # Mock list items response
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {
            "value": [{"displayName": "TestLakehouse", "type": "Lakehouse", "id": "lakehouse-id-123"}]
        }

        # Mock lakehouse properties response
        lakehouse_response = Mock()
        lakehouse_response.status_code = 200
        lakehouse_response.json.return_value = {
            "properties": {"connectionString": "test-lakehouse.datawarehouse.fabric.microsoft.com"}
        }

        mock_client.get.side_effect = [list_response, lakehouse_response]

        result = get_sql_endpoint(workspace_id, "TestLakehouse", "Lakehouse", mock_client)

        assert result == "test-lakehouse.datawarehouse.fabric.microsoft.com"

    def test_get_sql_endpoint_warehouse_success(self, mock_client, workspace_id):
        """Test successfully retrieving SQL endpoint for Warehouse."""
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {
            "value": [{"displayName": "TestWarehouse", "type": "Warehouse", "id": "warehouse-id-456"}]
        }

        warehouse_response = Mock()
        warehouse_response.status_code = 200
        warehouse_response.json.return_value = {
            "properties": {"connectionString": "test-warehouse.datawarehouse.fabric.microsoft.com"}
        }

        mock_client.get.side_effect = [list_response, warehouse_response]

        result = get_sql_endpoint(workspace_id, "TestWarehouse", "Warehouse", mock_client)

        assert result == "test-warehouse.datawarehouse.fabric.microsoft.com"

    def test_get_sql_endpoint_item_not_found(self, mock_client, workspace_id):
        """Test when item is not found."""
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {"value": []}

        mock_client.get.return_value = list_response

        result = get_sql_endpoint(workspace_id, "NonExistent", "Lakehouse", mock_client)

        assert result is None

    def test_get_sql_endpoint_unsupported_type(self, mock_client, workspace_id):
        """Test with unsupported item type."""
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {
            "value": [{"displayName": "TestNotebook", "type": "Notebook", "id": "notebook-id-123"}]
        }

        mock_client.get.return_value = list_response

        result = get_sql_endpoint(workspace_id, "TestNotebook", "Notebook", mock_client)

        assert result is None

    def test_get_sql_endpoint_missing_connection_string(self, mock_client, workspace_id):
        """Test when connectionString is missing from properties."""
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {
            "value": [{"displayName": "TestLakehouse", "type": "Lakehouse", "id": "lakehouse-id-123"}]
        }

        lakehouse_response = Mock()
        lakehouse_response.status_code = 200
        lakehouse_response.json.return_value = {"properties": {}}

        mock_client.get.side_effect = [list_response, lakehouse_response]

        result = get_sql_endpoint(workspace_id, "TestLakehouse", "Lakehouse", mock_client)

        assert result is None


class TestExecSqlQuery:
    """Tests for exec_sql_query function."""

    @pytest.fixture
    def mock_notebookutils(self):
        """Create a mock notebookutils object."""
        mock_nb = Mock()
        mock_nb.credentials.getToken.return_value = "test-token-123"
        return mock_nb

    def test_exec_sql_query_success(self, mock_notebookutils):
        """Test successfully executing a SQL query."""
        from unittest.mock import patch

        sql_endpoint = "test.datawarehouse.fabric.microsoft.com"
        database_name = "TestDatabase"
        sql_query = "SELECT * FROM meters"

        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "columns": ["meter_id", "meter_type", "max_amps"],
            "rows": [["MTR001", "residential", 200], ["MTR002", "commercial", 400]],
        }

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = exec_sql_query(sql_endpoint, database_name, sql_query, mock_notebookutils)

            assert result is not None
            assert len(result) == 2
            assert result[0]["meter_id"] == "MTR001"
            assert result[0]["meter_type"] == "residential"
            assert result[1]["meter_id"] == "MTR002"
            mock_post.assert_called_once()

    def test_exec_sql_query_no_columns(self, mock_notebookutils):
        """Test executing query that returns rows without column metadata."""
        from unittest.mock import patch

        sql_endpoint = "test.datawarehouse.fabric.microsoft.com"
        database_name = "TestDatabase"
        sql_query = "DELETE FROM temp_table"

        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"rows": []}

        with patch("requests.post", return_value=mock_response):
            result = exec_sql_query(sql_endpoint, database_name, sql_query, mock_notebookutils)

            assert result == []

    def test_exec_sql_query_failure(self, mock_notebookutils):
        """Test handling of SQL query failure."""
        from unittest.mock import patch

        sql_endpoint = "test.datawarehouse.fabric.microsoft.com"
        database_name = "TestDatabase"
        sql_query = "SELECT * FROM invalid_table"

        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "Invalid object name 'invalid_table'"

        with patch("requests.post", return_value=mock_response):
            result = exec_sql_query(sql_endpoint, database_name, sql_query, mock_notebookutils)

            assert result is None

    def test_exec_sql_query_network_error(self, mock_notebookutils):
        """Test handling of network errors."""
        from unittest.mock import patch

        import requests

        sql_endpoint = "test.datawarehouse.fabric.microsoft.com"
        database_name = "TestDatabase"
        sql_query = "SELECT * FROM meters"

        with patch("requests.post", side_effect=requests.RequestException("Network error")):
            result = exec_sql_query(sql_endpoint, database_name, sql_query, mock_notebookutils)

            assert result is None

    def test_exec_sql_query_custom_timeout(self, mock_notebookutils):
        """Test executing query with custom timeout."""
        from unittest.mock import patch

        sql_endpoint = "test.datawarehouse.fabric.microsoft.com"
        database_name = "TestDatabase"
        sql_query = "SELECT * FROM large_table"

        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"columns": ["id"], "rows": [[1]]}

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = exec_sql_query(sql_endpoint, database_name, sql_query, mock_notebookutils, timeout=120)

            assert result is not None
            # Verify timeout was passed
            assert mock_post.call_args[1]["timeout"] == 120


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
