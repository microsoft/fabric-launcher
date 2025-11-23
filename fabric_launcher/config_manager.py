"""
Configuration Management Module

This module provides functionality to load and manage deployment configurations
from YAML or JSON files. Supports downloading config files from GitHub repositories.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Optional

import requests
import yaml


class DeploymentConfig:
    """
    Handler for loading and managing deployment configurations.

    Supports loading from YAML or JSON files with environment-specific overrides.
    Can download configuration files from GitHub repositories for use in Fabric notebooks.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
        config_file_path: Optional[str] = None,
        branch: str = "main",
        github_token: Optional[str] = None,
    ):
        """
        Initialize the configuration manager.

        Can load from local file or download from GitHub repository.

        Args:
            config_path: Path to local configuration file (YAML or JSON)
            repo_owner: GitHub repository owner (for downloading from GitHub)
            repo_name: GitHub repository name (for downloading from GitHub)
            config_file_path: Path to config file within the GitHub repository
            branch: Git branch to download from (default: "main")
            github_token: GitHub personal access token (optional, for private repos)

        Example (local file):
            config = DeploymentConfig(config_path="deployment_config.yaml")

        Example (from GitHub):
            config = DeploymentConfig(
                repo_owner="myorg",
                repo_name="my-solution",
                config_file_path="config/deployment_config.yaml",
                github_token="ghp_xxx"  # Optional
            )
        """
        self.config_path = config_path
        self.config: dict[str, Any] = {}

        # If GitHub parameters provided, download config from GitHub
        if repo_owner and repo_name and config_file_path:
            print(f"📥 Downloading configuration from GitHub: {repo_owner}/{repo_name}/{config_file_path}")
            self.config_path = self._download_config_from_github(
                repo_owner=repo_owner,
                repo_name=repo_name,
                file_path=config_file_path,
                branch=branch,
                github_token=github_token,
            )
            print("✅ Configuration downloaded successfully")

        # Load config from local path
        if self.config_path and Path(self.config_path).exists():
            self.load_config(self.config_path)

    def _download_config_from_github(
        self, repo_owner: str, repo_name: str, file_path: str, branch: str = "main", github_token: Optional[str] = None
    ) -> str:
        """
        Download a configuration file from a GitHub repository.

        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            file_path: Path to config file within the repository
            branch: Git branch (default: "main")
            github_token: GitHub personal access token (optional)

        Returns:
            Path to downloaded configuration file (in temp directory)

        Raises:
            Exception: If download fails
        """
        # Construct GitHub raw content URL
        url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/{file_path}"

        # Set up headers with token if provided
        headers = {}
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        try:
            # Download the file
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Save to temporary file
            file_extension = Path(file_path).suffix
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=file_extension, delete=False, encoding="utf-8"
            ) as temp_file:
                temp_file.write(response.text)
                return temp_file.name

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(
                    f"Configuration file not found in repository: {file_path}\n"
                    f"Repository: {repo_owner}/{repo_name}\n"
                    f"Branch: {branch}\n"
                    f"URL attempted: {url}"
                ) from e
            if e.response.status_code == 401 or e.response.status_code == 403:
                raise PermissionError(
                    f"Access denied to repository. This may be a private repository.\n"
                    f"Repository: {repo_owner}/{repo_name}\n"
                    f"Please provide a github_token parameter for private repositories."
                ) from e
            raise Exception(f"Failed to download config file: {e}") from e
        except Exception as e:
            raise Exception(
                f"Error downloading configuration from GitHub: {e}\n"
                f"Repository: {repo_owner}/{repo_name}\n"
                f"File: {file_path}\n"
                f"Branch: {branch}"
            ) from e

    def load_config(self, config_path: str) -> dict[str, Any]:
        """
        Load configuration from a YAML or JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            Dictionary containing configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If file format is not supported
        """
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        file_ext = Path(config_path).suffix.lower()

        try:
            with open(config_path, encoding="utf-8") as f:
                if file_ext in [".yaml", ".yml"]:
                    self.config = yaml.safe_load(f) or {}
                elif file_ext == ".json":
                    self.config = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_ext}. Use .yaml, .yml, or .json")

            print(f"✅ Configuration loaded from {config_path}")
            return self.config

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}") from e
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}") from e

    def get(self, key: str, default: Any = None, environment: Optional[str] = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., "github.repo_owner")
            default: Default value if key not found
            environment: Environment name for environment-specific overrides

        Returns:
            Configuration value or default
        """
        # Check environment-specific override first
        if environment:
            env_key = f"environments.{environment}.{key}"
            value = self._get_nested(self.config, env_key)
            if value is not None:
                return value

        # Fall back to general config
        value = self._get_nested(self.config, key)
        return value if value is not None else default

    def _get_nested(self, data: dict, key: str) -> Any:
        """Get nested dictionary value using dot notation."""
        keys = key.split(".")
        value = data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return None
            else:
                return None

        return value

    def get_github_config(self, environment: Optional[str] = None) -> dict[str, Any]:
        """Get GitHub-specific configuration."""
        return {
            "repo_owner": self.get("github.repo_owner", environment=environment),
            "repo_name": self.get("github.repo_name", environment=environment),
            "branch": self.get("github.branch", "main", environment=environment),
            "github_token": self.get("github.token", environment=environment),
            "workspace_folder": self.get("github.workspace_folder", "workspace", environment=environment),
        }

    def get_deployment_config(self, environment: Optional[str] = None) -> dict[str, Any]:
        """Get deployment-specific configuration."""
        return {
            "environment": environment or self.get("deployment.environment", "DEV"),
            "item_types": self.get("deployment.item_types", environment=environment),
            "allow_non_empty_workspace": self.get(
                "deployment.allow_non_empty_workspace", False, environment=environment
            ),
            "fix_zero_logical_ids": self.get("deployment.fix_zero_logical_ids", True, environment=environment),
        }

    def get_data_config(self, environment: Optional[str] = None) -> dict[str, Any]:
        """Get data folder configuration."""
        return {
            "lakehouse_name": self.get("data.lakehouse_name", environment=environment),
            "folder_mappings": self.get("data.folder_mappings", {}, environment=environment),
            "file_patterns": self.get("data.file_patterns", environment=environment),
        }

    def get_notebook_config(self, environment: Optional[str] = None) -> dict[str, Any]:
        """Get post-deployment notebook configuration."""
        return {
            "notebook_name": self.get("post_deployment.notebook_name", environment=environment),
            "parameters": self.get("post_deployment.parameters", {}, environment=environment),
            "timeout_seconds": self.get("post_deployment.timeout_seconds", 3600, environment=environment),
        }

    def validate_required_fields(self, required_fields: list[str], environment: Optional[str] = None) -> list[str]:
        """
        Validate that required configuration fields are present.

        Args:
            required_fields: List of required field keys
            environment: Environment name

        Returns:
            List of missing fields
        """
        missing = []
        for field in required_fields:
            if self.get(field, environment=environment) is None:
                missing.append(field)
        return missing

    def save_config(self, output_path: str, format: str = "yaml") -> None:
        """
        Save current configuration to file.

        Args:
            output_path: Path to save configuration
            format: Output format ('yaml' or 'json')
        """
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                if format.lower() == "yaml":
                    yaml.safe_dump(self.config, f, default_flow_style=False, sort_keys=False)
                elif format.lower() == "json":
                    json.dump(self.config, f, indent=2)
                else:
                    raise ValueError(f"Unsupported format: {format}")

            print(f"✅ Configuration saved to {output_path}")

        except Exception as e:
            raise ValueError(f"Error saving configuration: {e}") from e

    @staticmethod
    def create_template(output_path: str, format: str = "yaml") -> None:
        """
        Create a template configuration file.

        Args:
            output_path: Path to save template
            format: Output format ('yaml' or 'json')
        """
        template = {
            "github": {
                "repo_owner": "your-org",
                "repo_name": "your-repo",
                "branch": "main",
                "workspace_folder": "workspace",
                "token": "",  # Optional: for private repos
            },
            "deployment": {
                "environment": "DEV",
                "allow_non_empty_workspace": False,
                "fix_zero_logical_ids": True,  # Replace zero GUIDs with unique identifiers
                "item_types": None,  # None = deploy all types
            },
            "data": {
                "lakehouse_name": "DataLH",
                "folder_mappings": {"data": "reference-data", "samples": "sample-data"},
                "file_patterns": ["*.json", "*.csv", "*.parquet"],
            },
            "post_deployment": {
                "notebook_name": "Initialize-Data",
                "parameters": {"environment": "DEV"},
                "timeout_seconds": 3600,
            },
            "environments": {
                "DEV": {"deployment": {"environment": "DEV"}},
                "TEST": {"deployment": {"environment": "TEST"}},
                "PROD": {"deployment": {"environment": "PROD", "allow_non_empty_workspace": False}},
            },
        }

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                if format.lower() == "yaml":
                    yaml.safe_dump(template, f, default_flow_style=False, sort_keys=False)
                elif format.lower() == "json":
                    json.dump(template, f, indent=2)
                else:
                    raise ValueError(f"Unsupported format: {format}")

            print(f"✅ Configuration template created at {output_path}")
            print("📝 Edit this file with your deployment settings")

        except Exception as e:
            raise ValueError(f"Error creating template: {e}") from e
