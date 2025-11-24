"""
Fabric Launcher - A wrapper around fabric-cicd for Fabric solution deployment

This package provides a high-level interface for deploying Microsoft Fabric solutions
from GitHub repositories. It orchestrates:
- GitHub repository downloads
- Fabric workspace item deployments
- File uploads to Lakehouse
- Notebook execution

Designed to be used within Fabric Python notebooks with notebookutils available.
"""

__version__ = "0.3.0"

from .config_manager import DeploymentConfig
from .deployment_report import DeploymentReport
from .deployment_validator import DeploymentValidator
from .fabric_deployer import FabricDeployer, FabricNotebookTokenCredential
from .file_operations import LakehouseFileManager
from .github_downloader import GitHubDownloader
from .launcher import FabricLauncher
from .notebook_executor import NotebookExecutor
from .post_deployment_utils import (
    create_or_update_fabric_item,
    get_folder_id_by_name,
    get_item_definition_from_repo,
    move_item_to_folder,
    replace_logical_ids,
    scan_logical_ids,
)

__all__ = [
    "FabricLauncher",
    "GitHubDownloader",
    "FabricDeployer",
    "FabricNotebookTokenCredential",
    "LakehouseFileManager",
    "NotebookExecutor",
    "DeploymentConfig",
    "DeploymentValidator",
    "DeploymentReport",
    # Post-deployment utilities
    "get_folder_id_by_name",
    "get_item_definition_from_repo",
    "scan_logical_ids",
    "replace_logical_ids",
    "create_or_update_fabric_item",
    "move_item_to_folder",
]
