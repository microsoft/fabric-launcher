"""
Tests for the FabricDeployer class in fabric_deployer module.
"""

import base64
import json
import sys
from unittest.mock import MagicMock, patch

import pytest

# Import the mock DataFrame from conftest (loaded via sys.modules)
pd = sys.modules["pandas"]

from fabric_launcher.fabric_deployer import (  # noqa: E402
    FabricDeployer,
    FabricNotebookTokenCredential,
)


class TestFabricNotebookTokenCredential:
    """Tests for FabricNotebookTokenCredential class."""

    def test_initialization(self):
        """Test credential initialization."""
        mock_notebookutils = MagicMock()
        credential = FabricNotebookTokenCredential(mock_notebookutils)
        assert credential.notebookutils == mock_notebookutils

    def test_get_token_success(self):
        """Test successful token retrieval."""
        mock_notebookutils = MagicMock()
        # Create a valid JWT with exp claim (header.payload.signature)
        # Payload: {"exp": 1700000000}
        payload = json.dumps({"exp": 1700000000})
        payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
        mock_token = f"header.{payload_b64}.signature"

        mock_notebookutils.credentials.getToken.return_value = mock_token

        credential = FabricNotebookTokenCredential(mock_notebookutils)
        token = credential.get_token("scope")

        assert token.token == mock_token
        assert token.expires_on == 1700000000
        mock_notebookutils.credentials.getToken.assert_called_once_with("pbi")

    def test_get_token_invalid_jwt(self):
        """Test handling of invalid JWT token."""
        mock_notebookutils = MagicMock()
        mock_notebookutils.credentials.getToken.return_value = "invalid-token"

        credential = FabricNotebookTokenCredential(mock_notebookutils)

        with pytest.raises(ValueError, match="Invalid JWT token format"):
            credential.get_token("scope")

    def test_get_token_missing_exp_claim(self):
        """Test handling of JWT without expiration claim."""
        mock_notebookutils = MagicMock()

        payload = json.dumps({"sub": "user"})  # No 'exp' claim
        payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
        mock_token = f"header.{payload_b64}.signature"

        mock_notebookutils.credentials.getToken.return_value = mock_token

        credential = FabricNotebookTokenCredential(mock_notebookutils)

        with pytest.raises(ValueError, match="JWT missing expiration claim"):
            credential.get_token("scope")


class TestFabricDeployerInit:
    """Tests for FabricDeployer initialization."""

    def test_initialization_default(self):
        """Test default initialization."""
        mock_notebookutils = MagicMock()

        with patch("fabric_launcher.fabric_deployer.FabricWorkspace"):
            deployer = FabricDeployer(
                workspace_id="test-workspace-id", repository_directory="/repo/path", notebookutils=mock_notebookutils
            )

            assert deployer.workspace_id == "test-workspace-id"
            assert deployer.repository_directory == "/repo/path"
            assert deployer.environment == "DEV"
            assert deployer.allow_non_empty_workspace is False
            assert deployer.fix_zero_logical_ids is True
            assert deployer._deployment_session_started is False

    def test_initialization_custom_params(self):
        """Test initialization with custom parameters."""
        mock_notebookutils = MagicMock()

        with patch("fabric_launcher.fabric_deployer.FabricWorkspace"):
            deployer = FabricDeployer(
                workspace_id="test-workspace-id",
                repository_directory="/repo/path",
                notebookutils=mock_notebookutils,
                environment="PROD",
                allow_non_empty_workspace=True,
                fix_zero_logical_ids=False,
            )

            assert deployer.environment == "PROD"
            assert deployer.allow_non_empty_workspace is True
            assert deployer.fix_zero_logical_ids is False


class TestRetryOnFailure:
    """Tests for _retry_on_failure static method."""

    def test_retry_success_first_attempt(self):
        """Test successful execution on first attempt."""
        mock_func = MagicMock(return_value="success")

        result = FabricDeployer._retry_on_failure(mock_func, max_retries=3)

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_success_after_failures(self):
        """Test successful execution after failures."""
        mock_func = MagicMock(side_effect=[Exception("fail"), Exception("fail"), "success"])

        with patch("time.sleep"):  # Speed up test
            result = FabricDeployer._retry_on_failure(mock_func, max_retries=3, delay_seconds=1)

        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_all_attempts_fail(self):
        """Test when all retry attempts fail."""
        mock_func = MagicMock(side_effect=Exception("persistent failure"))

        with patch("time.sleep"), pytest.raises(Exception, match="failed after 3 attempts"):
            FabricDeployer._retry_on_failure(mock_func, max_retries=3)

        assert mock_func.call_count == 3

    def test_retry_with_unauthorized_error(self):
        """Test retry adds suggestions for unauthorized errors."""
        mock_func = MagicMock(side_effect=Exception("403 Unauthorized"))

        with patch("time.sleep"), pytest.raises(Exception) as exc_info:
            FabricDeployer._retry_on_failure(mock_func, max_retries=1)

        assert "workspace permissions" in str(exc_info.value).lower()

    def test_retry_with_not_found_error(self):
        """Test retry adds suggestions for not found errors."""
        mock_func = MagicMock(side_effect=Exception("404 Not found"))

        with patch("time.sleep"), pytest.raises(Exception) as exc_info:
            FabricDeployer._retry_on_failure(mock_func, max_retries=1)

        assert "workspace ID" in str(exc_info.value)


class TestDeployItems:
    """Tests for deploy_items method."""

    def test_deploy_items_skip_validation_when_allowed(self):
        """Test deployment skips workspace validation when allowed."""
        mock_notebookutils = MagicMock()

        with (
            patch("fabric_launcher.fabric_deployer.FabricWorkspace"),
            patch("fabric_launcher.fabric_deployer.publish_all_items"),
            patch("fabric_launcher.fabric_deployer.PlatformFileFixer") as mock_fixer,
        ):
            mock_fixer_instance = MagicMock()
            mock_fixer_instance.scan_and_fix_all.return_value = {"files_fixed": 0, "files_with_zero_guid": 0}
            mock_fixer.return_value = mock_fixer_instance

            deployer = FabricDeployer(
                workspace_id="test-workspace-id",
                repository_directory="/repo/path",
                notebookutils=mock_notebookutils,
                allow_non_empty_workspace=True,
            )

            deployer.deploy_items()

            # publish_all_items should be called
            # fixer should be called
            mock_fixer_instance.scan_and_fix_all.assert_called_once()

    def test_deploy_items_skip_fixer(self):
        """Test deployment skips fixer when disabled."""
        mock_notebookutils = MagicMock()

        with (
            patch("fabric_launcher.fabric_deployer.FabricWorkspace"),
            patch("fabric_launcher.fabric_deployer.publish_all_items"),
            patch("fabric_launcher.fabric_deployer.PlatformFileFixer") as mock_fixer,
        ):
            deployer = FabricDeployer(
                workspace_id="test-workspace-id",
                repository_directory="/repo/path",
                notebookutils=mock_notebookutils,
                fix_zero_logical_ids=False,
                allow_non_empty_workspace=True,  # Skip workspace validation too
            )

            deployer.deploy_items()

            # Fixer should not be instantiated
            mock_fixer.assert_not_called()

    def test_deploy_items_specific_types(self):
        """Test deploying specific item types."""
        mock_notebookutils = MagicMock()

        with (
            patch("fabric_launcher.fabric_deployer.FabricWorkspace"),
            patch("fabric_launcher.fabric_deployer.publish_all_items"),
            patch("fabric_launcher.fabric_deployer.PlatformFileFixer") as mock_fixer,
        ):
            mock_fixer_instance = MagicMock()
            mock_fixer_instance.scan_and_fix_all.return_value = {"files_fixed": 0, "files_with_zero_guid": 0}
            mock_fixer.return_value = mock_fixer_instance

            deployer = FabricDeployer(
                workspace_id="test-workspace-id",
                repository_directory="/repo/path",
                notebookutils=mock_notebookutils,
                allow_non_empty_workspace=True,
            )

            deployer.deploy_items(item_types=["Lakehouse", "Notebook"])

            assert deployer.workspace.item_type_in_scope == ["Lakehouse", "Notebook"]
