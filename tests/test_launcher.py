"""
Unit tests for FabricLauncher module.

Note: These tests mock notebookutils and fabric dependencies since they're
only available in Fabric notebook environment.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fabric_launcher.launcher import FabricLauncher


class TestFabricLauncherInitialization(unittest.TestCase):
    """Test cases for FabricLauncher initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_notebookutils = Mock()

    @patch("sempy.fabric")
    def test_initialization_basic(self, mock_fabric):
        """Test basic FabricLauncher initialization."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"

        launcher = FabricLauncher(notebookutils=self.mock_notebookutils)

        self.assertEqual(launcher.notebookutils, self.mock_notebookutils)
        self.assertEqual(launcher.workspace_id, "test-workspace-id")
        self.assertEqual(launcher.environment, "DEV")
        self.assertFalse(launcher.debug)
        self.assertFalse(launcher.allow_non_empty_workspace)

    @patch("sempy.fabric")
    def test_initialization_with_custom_params(self, mock_fabric):
        """Test initialization with custom parameters."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"

        launcher = FabricLauncher(
            notebookutils=self.mock_notebookutils,
            workspace_id="custom-workspace-id",
            environment="PROD",
            debug=True,
            allow_non_empty_workspace=True,
        )

        self.assertEqual(launcher.workspace_id, "custom-workspace-id")
        self.assertEqual(launcher.environment, "PROD")
        self.assertTrue(launcher.debug)
        self.assertTrue(launcher.allow_non_empty_workspace)

    @patch("sempy.fabric")
    @patch("fabric_launcher.launcher.DeploymentConfig")
    def test_initialization_with_local_config(self, mock_config_class, mock_fabric):
        """Test initialization with local config file."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"

        mock_config_instance = Mock()
        mock_config_class.return_value = mock_config_instance

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("github:\n  repo_owner: test\n")
            config_path = f.name

        try:
            FabricLauncher(notebookutils=self.mock_notebookutils, config_file=config_path)

            # Verify config was loaded
            mock_config_class.assert_called_with(config_path=config_path)
        finally:
            Path(config_path).unlink()

    @patch("sempy.fabric")
    @patch("fabric_launcher.launcher.DeploymentConfig")
    def test_initialization_with_github_config(self, mock_config_class, mock_fabric):
        """Test initialization with GitHub config."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"

        mock_config_instance = Mock()
        mock_config_class.return_value = mock_config_instance

        FabricLauncher(
            notebookutils=self.mock_notebookutils,
            config_repo_owner="test-org",
            config_repo_name="test-repo",
            config_file_path="config/deployment.yaml",
        )

        # Verify config was loaded from GitHub
        mock_config_class.assert_called_once()
        call_kwargs = mock_config_class.call_args.kwargs
        self.assertEqual(call_kwargs["repo_owner"], "test-org")
        self.assertEqual(call_kwargs["repo_name"], "test-repo")
        self.assertEqual(call_kwargs["config_file_path"], "config/deployment.yaml")


class TestFabricLauncherProperties(unittest.TestCase):
    """Test lazy-loaded properties."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_notebookutils = Mock()

    @patch("sempy.fabric")
    @patch("fabric_launcher.launcher.LakehouseFileManager")
    def test_file_manager_property(self, mock_file_manager_class, mock_fabric):
        """Test file_manager property lazy initialization."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"

        launcher = FabricLauncher(self.mock_notebookutils)

        # First access should create instance
        file_manager = launcher.file_manager
        mock_file_manager_class.assert_called_once_with(self.mock_notebookutils)

        # Second access should return same instance
        file_manager2 = launcher.file_manager
        self.assertIs(file_manager, file_manager2)
        # Should not create new instance
        self.assertEqual(mock_file_manager_class.call_count, 1)

    @patch("sempy.fabric")
    @patch("fabric_launcher.launcher.NotebookExecutor")
    def test_notebook_executor_property(self, mock_executor_class, mock_fabric):
        """Test notebook_executor property lazy initialization."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"

        launcher = FabricLauncher(self.mock_notebookutils)

        # First access should create instance
        executor = launcher.notebook_executor
        mock_executor_class.assert_called_once_with(self.mock_notebookutils)

        # Second access should return same instance
        executor2 = launcher.notebook_executor
        self.assertIs(executor, executor2)

    @patch("sempy.fabric")
    @patch("fabric_launcher.launcher.DeploymentValidator")
    def test_validator_property(self, mock_validator_class, mock_fabric):
        """Test validator property lazy initialization."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"

        launcher = FabricLauncher(self.mock_notebookutils)

        # First access should create instance
        validator = launcher.validator
        mock_validator_class.assert_called_once()

        # Second access should return same instance
        validator2 = launcher.validator
        self.assertIs(validator, validator2)


class TestFabricLauncherMethods(unittest.TestCase):
    """Test FabricLauncher methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_notebookutils = Mock()

    @patch("sempy.fabric")
    @patch("fabric_launcher.launcher.GitHubDownloader")
    def test_download_repository(self, mock_downloader_class, mock_fabric):
        """Test download_repository method."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"

        mock_downloader_instance = Mock()
        mock_downloader_class.return_value = mock_downloader_instance

        launcher = FabricLauncher(self.mock_notebookutils)

        with tempfile.TemporaryDirectory() as temp_dir:
            launcher.download_repository(
                repo_owner="test-org", repo_name="test-repo", extract_to=temp_dir, branch="main"
            )

            # Verify downloader was created with correct params
            mock_downloader_class.assert_called_once_with(
                repo_owner="test-org", repo_name="test-repo", branch="main", github_token=None
            )

            # Verify extraction was called
            mock_downloader_instance.download_and_extract_folder.assert_called_once()

    @patch("sempy.fabric")
    @patch("fabric_launcher.launcher.FabricDeployer")
    def test_deploy_artifacts(self, mock_deployer_class, mock_fabric):
        """Test deploy_artifacts method."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"

        mock_deployer_instance = Mock()
        mock_deployer_class.return_value = mock_deployer_instance

        launcher = FabricLauncher(self.mock_notebookutils)

        with tempfile.TemporaryDirectory() as temp_dir:
            launcher.deploy_artifacts(repository_directory=temp_dir, item_types=["Lakehouse", "Notebook"])

            # Verify deployer was created
            mock_deployer_class.assert_called_once()

            # Verify deploy_items was called with item types
            mock_deployer_instance.deploy_items.assert_called_once_with(["Lakehouse", "Notebook"])

    @patch("sempy.fabric")
    def test_download_config_from_github_static_method(self, mock_fabric):
        """Test download_config_from_github static method."""
        with patch("fabric_launcher.launcher.DeploymentConfig") as mock_config_class:
            mock_config_instance = Mock()
            mock_config_instance.config_path = "/tmp/config.yaml"
            mock_config_class.return_value = mock_config_instance

            result = FabricLauncher.download_config_from_github(
                repo_owner="test-org", repo_name="test-repo", config_file_path="config/deployment.yaml"
            )

            # Verify config was downloaded
            mock_config_class.assert_called_once()
            self.assertEqual(result, "/tmp/config.yaml")


class TestFabricLauncherDownloadAndDeploy(unittest.TestCase):
    """Test download_and_deploy workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_notebookutils = Mock()

    @patch("sempy.fabric")
    @patch("fabric_launcher.launcher.GitHubDownloader")
    @patch("fabric_launcher.launcher.FabricDeployer")
    @patch("fabric_launcher.launcher.DeploymentReport")
    def test_download_and_deploy_basic(
        self, mock_report_class, mock_deployer_class, mock_downloader_class, mock_fabric
    ):
        """Test basic download_and_deploy workflow."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"

        # Mock downloader
        mock_downloader_instance = Mock()
        mock_downloader_class.return_value = mock_downloader_instance

        # Mock deployer
        mock_deployer_instance = Mock()
        mock_deployer_class.return_value = mock_deployer_instance

        # Mock report
        mock_report_instance = Mock()
        mock_report_instance.session_id = "20241121_120000"
        mock_report_class.return_value = mock_report_instance

        launcher = FabricLauncher(self.mock_notebookutils)

        with tempfile.TemporaryDirectory() as temp_dir:
            downloader, deployer, report = launcher.download_and_deploy(
                repo_owner="test-org", repo_name="test-repo", extract_to=temp_dir, generate_report=True
            )

            # Verify components were created
            self.assertIsNotNone(downloader)
            self.assertIsNotNone(deployer)
            self.assertIsNotNone(report)

            # Verify report steps were added
            self.assertTrue(mock_report_instance.add_step.called)

    @patch("sempy.fabric")
    def test_download_and_deploy_missing_params(self, mock_fabric):
        """Test download_and_deploy with missing required parameters."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"

        launcher = FabricLauncher(self.mock_notebookutils)

        with self.assertRaises(ValueError) as context:
            launcher.download_and_deploy()

        self.assertIn("repo_owner and repo_name are required", str(context.exception))

    @patch("sempy.fabric")
    @patch("fabric_launcher.launcher.GitHubDownloader")
    @patch("fabric_launcher.launcher.FabricDeployer")
    @patch("fabric_launcher.launcher.DeploymentReport")
    def test_download_and_deploy_with_item_type_stages(
        self, mock_report_class, mock_deployer_class, mock_downloader_class, mock_fabric
    ):
        """Test download_and_deploy with item_type_stages for staged deployment."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"
        mock_fabric.list_items.return_value = Mock(empty=True)

        # Mock downloader
        mock_downloader_instance = Mock()
        mock_downloader_class.return_value = mock_downloader_instance

        # Mock deployer
        mock_deployer_instance = Mock()
        mock_deployer_class.return_value = mock_deployer_instance

        # Mock report
        mock_report_instance = Mock()
        mock_report_instance.session_id = "20241122_120000"
        mock_report_class.return_value = mock_report_instance

        launcher = FabricLauncher(self.mock_notebookutils)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Define staged deployment
            stages = [["Eventhouse", "KQLDatabase"], ["Notebook", "Eventstream"], ["SemanticModel", "Report"]]

            downloader, deployer, report = launcher.download_and_deploy(
                repo_owner="test-org",
                repo_name="test-repo",
                extract_to=temp_dir,
                item_type_stages=stages,
                generate_report=True,
            )

            # Verify deployer was created
            mock_deployer_class.assert_called_once()

            # Verify deploy_items was called 3 times (once per stage)
            self.assertEqual(mock_deployer_instance.deploy_items.call_count, 3)

            # Verify each stage was deployed with correct item types
            calls = mock_deployer_instance.deploy_items.call_args_list
            self.assertEqual(calls[0][0][0], ["Eventhouse", "KQLDatabase"])
            self.assertEqual(calls[1][0][0], ["Notebook", "Eventstream"])
            self.assertEqual(calls[2][0][0], ["SemanticModel", "Report"])

    @patch("sempy.fabric")
    def test_download_and_deploy_item_types_and_stages_mutually_exclusive(self, mock_fabric):
        """Test that item_types and item_type_stages cannot be used together."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"

        launcher = FabricLauncher(self.mock_notebookutils)

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError) as context:
                launcher.download_and_deploy(
                    repo_owner="test-org",
                    repo_name="test-repo",
                    extract_to=temp_dir,
                    item_types=["Lakehouse"],
                    item_type_stages=[["Eventhouse"], ["Notebook"]],
                )

            self.assertIn("mutually exclusive", str(context.exception))

    @patch("sempy.fabric")
    @patch("fabric_launcher.launcher.GitHubDownloader")
    @patch("fabric_launcher.launcher.FabricDeployer")
    @patch("fabric_launcher.launcher.DeploymentReport")
    def test_download_and_deploy_single_stage_with_item_type_stages(
        self, mock_report_class, mock_deployer_class, mock_downloader_class, mock_fabric
    ):
        """Test item_type_stages with a single stage."""
        mock_fabric.get_workspace_id.return_value = "test-workspace-id"
        mock_fabric.list_items.return_value = Mock(empty=True)

        # Mock downloader
        mock_downloader_instance = Mock()
        mock_downloader_class.return_value = mock_downloader_instance

        # Mock deployer
        mock_deployer_instance = Mock()
        mock_deployer_class.return_value = mock_deployer_instance

        # Mock report
        mock_report_instance = Mock()
        mock_report_instance.session_id = "20241122_120000"
        mock_report_class.return_value = mock_report_instance

        launcher = FabricLauncher(self.mock_notebookutils)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Single stage deployment
            stages = [["Lakehouse", "Notebook"]]

            downloader, deployer, report = launcher.download_and_deploy(
                repo_owner="test-org",
                repo_name="test-repo",
                extract_to=temp_dir,
                item_type_stages=stages,
                generate_report=True,
            )

            # Verify deploy_items was called once with the single stage
            mock_deployer_instance.deploy_items.assert_called_once_with(["Lakehouse", "Notebook"])


if __name__ == "__main__":
    unittest.main()
