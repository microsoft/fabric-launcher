"""
Unit tests for DeploymentConfig module.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from fabric_launcher.config_manager import DeploymentConfig


class TestDeploymentConfig(unittest.TestCase):
    """Test cases for DeploymentConfig class."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_config = {
            "github": {
                "repo_owner": "test-org",
                "repo_name": "test-repo",
                "branch": "main",
                "workspace_folder": "workspace",
            },
            "deployment": {"staged_deployment": True, "validate_after_deployment": True, "deployment_retries": 3},
            "data": {"lakehouse_name": "TestLH", "folder_mappings": {"data": "reference-data"}},
            "environments": {"DEV": {"github": {"branch": "dev"}}, "PROD": {"deployment": {"deployment_retries": 5}}},
        }

    def test_load_yaml_config(self):
        """Test loading YAML configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(self.sample_config, f)
            config_path = f.name

        try:
            config = DeploymentConfig(config_path=config_path)

            loaded_config = config.load_config(config_path)
            self.assertEqual(loaded_config["github"]["repo_owner"], "test-org")
            self.assertEqual(loaded_config["deployment"]["deployment_retries"], 3)
        finally:
            Path(config_path).unlink()

    def test_load_json_config(self):
        """Test loading JSON configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.sample_config, f)
            config_path = f.name

        try:
            config = DeploymentConfig(config_path=config_path)

            loaded_config = config.load_config(config_path)
            self.assertEqual(loaded_config["github"]["repo_owner"], "test-org")
            self.assertEqual(loaded_config["deployment"]["deployment_retries"], 3)
        finally:
            Path(config_path).unlink()

    def test_load_config_file_not_found(self):
        """Test loading non-existent configuration file."""
        with self.assertRaises(FileNotFoundError):
            config = DeploymentConfig(config_path="nonexistent.yaml")
            config.load_config("nonexistent.yaml")

    def test_load_config_unsupported_format(self):
        """Test loading unsupported file format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("invalid config")
            config_path = f.name

        try:
            config = DeploymentConfig()
            with self.assertRaises(ValueError):
                config.load_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_get_github_config(self):
        """Test getting GitHub configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(self.sample_config, f)
            config_path = f.name

        try:
            config = DeploymentConfig(config_path=config_path)
            github_config = config.get_github_config()

            self.assertEqual(github_config["repo_owner"], "test-org")
            self.assertEqual(github_config["repo_name"], "test-repo")
            self.assertEqual(github_config["branch"], "main")
        finally:
            Path(config_path).unlink()

    def test_get_deployment_config(self):
        """Test getting deployment configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(self.sample_config, f)
            config_path = f.name

        try:
            config = DeploymentConfig(config_path=config_path)
            deploy_config = config.get_deployment_config()

            # Verify deployment config keys
            self.assertIn("environment", deploy_config)
            self.assertIn("item_types", deploy_config)
            self.assertIn("allow_non_empty_workspace", deploy_config)
            # fix_zero_logical_ids should default to True
            self.assertTrue(deploy_config["fix_zero_logical_ids"])
        finally:
            Path(config_path).unlink()

    def test_get_data_config(self):
        """Test getting data configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(self.sample_config, f)
            config_path = f.name

        try:
            config = DeploymentConfig(config_path=config_path)
            data_config = config.get_data_config()

            self.assertEqual(data_config["lakehouse_name"], "TestLH")
            self.assertIn("data", data_config["folder_mappings"])
        finally:
            Path(config_path).unlink()

    @patch("fabric_launcher.config_manager.requests.get")
    def test_download_config_from_github_success(self, mock_get):
        """Test downloading configuration from GitHub."""
        yaml_content = yaml.dump(self.sample_config)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = yaml_content
        mock_get.return_value = mock_response

        config = DeploymentConfig(
            repo_owner="test-org", repo_name="test-repo", config_file_path="config/deployment.yaml", branch="main"
        )

        # Verify the download was called
        mock_get.assert_called_once()

        # Verify config was loaded
        github_config = config.get_github_config()
        self.assertEqual(github_config["repo_owner"], "test-org")

    @patch("fabric_launcher.config_manager.requests.get")
    def test_download_config_from_github_404(self, mock_get):
        """Test downloading config with 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")

        # Mock the HTTPError
        from requests.exceptions import HTTPError

        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)

        with self.assertRaises(FileNotFoundError):
            DeploymentConfig(repo_owner="test-org", repo_name="test-repo", config_file_path="config/nonexistent.yaml")

    @patch("fabric_launcher.config_manager.requests.get")
    def test_download_config_with_token(self, mock_get):
        """Test downloading config with GitHub token."""
        yaml_content = yaml.dump(self.sample_config)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = yaml_content
        mock_get.return_value = mock_response

        github_token = "test-token-123"
        DeploymentConfig(
            repo_owner="test-org",
            repo_name="test-repo",
            config_file_path="config/deployment.yaml",
            github_token=github_token,
        )

        # Verify token was included in headers
        call_kwargs = mock_get.call_args.kwargs
        self.assertIn("headers", call_kwargs)
        self.assertEqual(call_kwargs["headers"]["Authorization"], f"token {github_token}")

    def test_create_template(self):
        """Test creating configuration template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = str(Path(temp_dir) / "template.yaml")

            DeploymentConfig.create_template(template_path)

            # Verify template was created
            self.assertTrue(Path(template_path).exists())

            # Verify template is valid YAML
            with open(template_path) as f:
                template_config = yaml.safe_load(f)

            self.assertIn("github", template_config)
            self.assertIn("deployment", template_config)
            self.assertIn("data", template_config)


if __name__ == "__main__":
    unittest.main()
