"""Fabric Launcher - Main Orchestration Module

This module provides the main FabricLauncher class that orchestrates all operations:
- Downloading source code from GitHub
- Deploying Fabric workspace items
- Uploading files to Lakehouse
- Executing Fabric notebooks

This is a wrapper around the fabric-cicd library designed for use in Fabric notebooks.
"""

__all__ = ["FabricLauncher"]

from pathlib import Path
from typing import Any

from .config_manager import DeploymentConfig
from .deployment_report import DeploymentReport
from .deployment_validator import DeploymentValidator
from .fabric_deployer import FabricDeployer
from .file_operations import LakehouseFileManager
from .github_downloader import GitHubDownloader
from .notebook_executor import NotebookExecutor


class FabricLauncher:
    """
    Main orchestrator for Fabric solution deployment and management.

    This class provides a high-level interface for:
    - Downloading source code from GitHub repositories
    - Deploying Fabric items to a workspace
    - Uploading files to Lakehouse Files area
    - Executing Fabric notebooks

    Example usage:
        >>> import notebookutils
        >>> from fabric_launcher import FabricLauncher
        >>>
        >>> # Initialize the launcher with config from GitHub
        >>> launcher = FabricLauncher(
        ...     notebookutils,
        ...     config_repo_owner="myorg",
        ...     config_repo_name="my-solution",
        ...     config_file_path="config/deployment.yaml"
        ... )
        >>>
        >>> # Download and deploy from GitHub
        >>> launcher.download_and_deploy()
        >>>
        >>> # Upload files to Lakehouse
        >>> launcher.upload_files_to_lakehouse(
        ...     lakehouse_name="MyLakehouse",
        ...     source_directory="./data",
        ...     target_folder="raw"
        ... )
        >>>
        >>> # Execute a notebook
        >>> launcher.run_notebook("ProcessData")
    """

    @staticmethod
    def download_config_from_github(
        repo_owner: str,
        repo_name: str,
        config_file_path: str,
        branch: str = "main",
        github_token: str | None = None,
        save_to: str | None = None,
    ) -> str:
        """
        Download a configuration file from GitHub repository.

        This is a utility method that can be used independently to download
        configuration files before initializing FabricLauncher.

        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            config_file_path: Path to config file within the repository
            branch: Git branch (default: "main")
            github_token: GitHub token for private repos (optional)
            save_to: Local path to save config file (optional, uses temp file if None)

        Returns:
            Path to downloaded configuration file

        Example:
            >>> config_path = FabricLauncher.download_config_from_github(
            ...     repo_owner="myorg",
            ...     repo_name="my-solution",
            ...     config_file_path="config/deployment.yaml"
            ... )
            >>> launcher = FabricLauncher(notebookutils, config_file=config_path)
        """
        config = DeploymentConfig(
            repo_owner=repo_owner,
            repo_name=repo_name,
            config_file_path=config_file_path,
            branch=branch,
            github_token=github_token,
        )

        # If save_to specified, copy the temp file there
        if save_to and config.config_path:
            import shutil

            shutil.copy(config.config_path, save_to)
            print(f"💾 Configuration saved to: {save_to}")
            return save_to

        return config.config_path

    def __init__(
        self,
        notebookutils,
        workspace_id: str | None = None,
        environment: str = "DEV",
        api_root_url: str = "https://api.fabric.microsoft.com",
        debug: bool = False,
        allow_non_empty_workspace: bool = False,
        fix_zero_logical_ids: bool = True,
        config_file: str | None = None,
        config_repo_owner: str | None = None,
        config_repo_name: str | None = None,
        config_file_path: str | None = None,
        config_branch: str = "main",
        config_github_token: str | None = None,
    ):
        """
        Initialize the Fabric Launcher.

        Args:
            notebookutils: The notebookutils module from Fabric notebook environment
            workspace_id: Target workspace ID (auto-detected if None)
            environment: Deployment environment (DEV, TEST, PROD)
            api_root_url: Fabric API root URL
            debug: Enable debug logging
            allow_non_empty_workspace: Allow deployment to workspaces with existing items
            fix_zero_logical_ids: Fix zero GUID logicalIds in .platform files
            config_file: Optional path to local configuration file (YAML or JSON)
            config_repo_owner: GitHub repository owner (for downloading config from GitHub)
            config_repo_name: GitHub repository name (for downloading config from GitHub)
            config_file_path: Path to config file within the GitHub repository
            config_branch: Git branch for config file (default: "main")
            config_github_token: GitHub token for private repositories (optional)

        Example (local config):
            launcher = FabricLauncher(notebookutils, config_file="deployment_config.yaml")

        Example (config from GitHub):
            launcher = FabricLauncher(
                notebookutils,
                config_repo_owner="myorg",
                config_repo_name="my-solution",
                config_file_path="config/deployment.yaml",
                config_github_token="ghp_xxx"  # Optional
            )
        """
        import sempy.fabric as fabric

        self.notebookutils = notebookutils
        self.workspace_id = workspace_id or fabric.get_workspace_id()
        self.environment = environment
        self.api_root_url = api_root_url
        self.debug = debug
        self.allow_non_empty_workspace = allow_non_empty_workspace
        self.fix_zero_logical_ids = fix_zero_logical_ids

        # Load configuration from file if provided
        self.config = None

        # Priority 1: Config from GitHub
        if config_repo_owner and config_repo_name and config_file_path:
            try:
                self.config = DeploymentConfig(
                    repo_owner=config_repo_owner,
                    repo_name=config_repo_name,
                    config_file_path=config_file_path,
                    branch=config_branch,
                    github_token=config_github_token,
                )
                print(f"📄 Loaded configuration from GitHub: {config_repo_owner}/{config_repo_name}/{config_file_path}")
            except Exception as e:
                print(f"⚠️ Warning: Could not load config from GitHub: {e}")

        # Priority 2: Local config file
        elif config_file:
            try:
                self.config = DeploymentConfig(config_path=config_file)
                print(f"📄 Loaded configuration from local file: {config_file}")
            except Exception as e:
                print(f"⚠️ Warning: Could not load local config file: {e}")

        # Initialize components (lazy initialization)
        self._github_downloader = None
        self._fabric_deployer = None
        self._file_manager = None
        self._notebook_executor = None
        self._validator = None

        print("🚀 Fabric Launcher initialized")
        print(f"📍 Workspace ID: {self.workspace_id}")
        print(f"🏷️ Environment: {self.environment}")

    @property
    def file_manager(self) -> LakehouseFileManager:
        """Get or create the file manager instance."""
        if self._file_manager is None:
            self._file_manager = LakehouseFileManager(self.notebookutils)
        return self._file_manager

    @property
    def notebook_executor(self) -> NotebookExecutor:
        """Get or create the notebook executor instance."""
        if self._notebook_executor is None:
            self._notebook_executor = NotebookExecutor(self.notebookutils)
        return self._notebook_executor

    @property
    def validator(self) -> DeploymentValidator:
        """Get or create the deployment validator instance."""
        if self._validator is None:
            self._validator = DeploymentValidator(workspace_id=self.workspace_id, notebookutils=self.notebookutils)
        return self._validator

    def _deploy_with_retry(
        self,
        deployer: FabricDeployer,
        item_types: list[str] | None,
        retries_remaining: int,
        stage_description: str = "Deployment",
    ) -> None:
        """
        Deploy items with automatic retry on failure.

        On retry, automatically sets allow_non_empty_workspace=True since previous
        attempt may have deployed some items before failing.

        Args:
            deployer: FabricDeployer instance to use for deployment
            item_types: List of item types to deploy (None for all)
            retries_remaining: Number of retries remaining (0 = no retries)
            stage_description: Description for logging (e.g., "Stage 1: Lakehouses")
        """
        import time

        try:
            deployer.deploy_items(item_types)
        except Exception as e:
            if retries_remaining > 0:
                print(f"\n⚠️ {stage_description} failed: {str(e)}")
                print(f"🔄 Retrying in 10 seconds... ({retries_remaining} retries remaining)")
                time.sleep(10)

                # On retry, allow non-empty workspace since previous attempt may have deployed items
                deployer.allow_non_empty_workspace = True
                deployer._deployment_session_started = True  # Skip workspace validation on retry

                self._deploy_with_retry(deployer, item_types, retries_remaining - 1, stage_description)
            else:
                # No retries remaining, re-raise the exception
                raise

    @property
    def repository_path(self) -> str | None:
        """
        Get the path where the repository was extracted.

        Returns:
            Path to extracted repository, or None if not yet deployed

        Example:
            >>> launcher.download_and_deploy(repo_owner="myorg", repo_name="my-solution")
            >>> print(f"Repository extracted to: {launcher.repository_path}")
        """
        if self._fabric_deployer:
            return self._fabric_deployer.repository_directory
        return None

    @property
    def workspace_directory(self) -> str | None:
        """
        Get the path to the workspace folder within the extracted repository.

        This is the directory containing the Fabric workspace artifacts that were
        deployed. Useful for accessing workspace item definitions post-deployment.

        Returns:
            Path to workspace directory, or None if not yet deployed

        Example:
            >>> launcher.download_and_deploy(repo_owner="myorg", repo_name="my-solution")
            >>> print(f"Workspace artifacts in: {launcher.workspace_directory}")
        """
        if self._fabric_deployer and hasattr(self._fabric_deployer, "repository_directory"):
            return self._fabric_deployer.repository_directory
        return None

    @property
    def deployment_config(self) -> dict | None:
        """
        Get the current deployment configuration.

        Returns:
            Dictionary containing configuration settings, or None if no config loaded

        Example:
            >>> launcher = FabricLauncher(notebookutils, config_file="config.yaml")
            >>> config = launcher.deployment_config
            >>> print(f"GitHub repo: {config['github']['repo_owner']}/{config['github']['repo_name']}")
        """
        if self.config:
            return {
                "github": self.config.get_github_config(environment=self.environment),
                "deployment": self.config.get_deployment_config(environment=self.environment),
                "data": self.config.get_data_config(environment=self.environment),
                "notebook": self.config.get_notebook_config(environment=self.environment),
            }
        return None

    def get_data_folder_path(self, folder_name: str) -> str | None:
        """
        Get the full path to a data folder within the extracted repository.

        This is useful for accessing downloaded data files after repository extraction.

        Args:
            folder_name: Name of the folder (e.g., "data", "samples")

        Returns:
            Full path to the folder, or None if repository not downloaded

        Example:
            >>> launcher.download_and_deploy(repo_owner="myorg", repo_name="my-solution")
            >>> data_path = launcher.get_data_folder_path("data")
            >>> print(f"Data files located at: {data_path}")
        """
        if self.repository_path:
            from pathlib import Path

            folder_path = Path(self.repository_path) / folder_name
            return str(folder_path) if folder_path.exists() else None
        return None

    def list_data_folders(self) -> list[str]:
        """
        List all directories in the extracted repository.

        Returns:
            List of folder names in the repository root, empty list if not downloaded

        Example:
            >>> launcher.download_and_deploy(repo_owner="myorg", repo_name="my-solution")
            >>> folders = launcher.list_data_folders()
            >>> print(f"Available folders: {', '.join(folders)}")
        """
        if self.repository_path:
            from pathlib import Path

            repo_path = Path(self.repository_path)
            if repo_path.exists():
                return [item.name for item in repo_path.iterdir() if item.is_dir()]
        return []

    def download_repository(
        self,
        repo_owner: str,
        repo_name: str,
        extract_to: str,
        branch: str = "main",
        folder_to_extract: str = "",
        github_token: str | None = None,
        remove_folder_prefix: str = "",
    ) -> GitHubDownloader:
        """
        Download and extract a GitHub repository.

        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            extract_to: Local directory to extract files to
            branch: Git branch to download (default: "main")
            folder_to_extract: Folder path within the repo to extract (empty for entire repo)
            github_token: GitHub personal access token (optional, for private repos)
            remove_folder_prefix: Prefix to remove from extracted file paths

        Returns:
            GitHubDownloader instance for further operations
        """
        self._github_downloader = GitHubDownloader(
            repo_owner=repo_owner, repo_name=repo_name, branch=branch, github_token=github_token
        )

        self._github_downloader.download_and_extract_folder(
            extract_to=extract_to, folder_to_extract=folder_to_extract, remove_folder_prefix=remove_folder_prefix
        )

        return self._github_downloader

    def deploy_artifacts(
        self,
        repository_directory: str,
        item_types: list[str] | None = None,
        allow_non_empty_workspace: bool | None = None,
        deployment_retries: int = 2,
    ) -> FabricDeployer:
        """
        Deploy Fabric artifacts to the workspace.

        Args:
            repository_directory: Local directory containing Fabric item definitions
            item_types: List of item types to deploy (None for all)
            allow_non_empty_workspace: Allow deployment to workspaces with existing items
                                       (None uses instance setting from __init__)
            deployment_retries: Number of retry attempts on deployment failure (default: 2).
                               On retry, automatically sets allow_non_empty_workspace=True.

        Returns:
            FabricDeployer instance for further operations
        """
        # Use instance setting if parameter not provided
        if allow_non_empty_workspace is None:
            allow_non_empty_workspace = self.allow_non_empty_workspace

        self._fabric_deployer = FabricDeployer(
            workspace_id=self.workspace_id,
            repository_directory=repository_directory,
            notebookutils=self.notebookutils,
            environment=self.environment,
            api_root_url=self.api_root_url,
            debug=self.debug,
            allow_non_empty_workspace=allow_non_empty_workspace,
            fix_zero_logical_ids=self.fix_zero_logical_ids,
        )

        self._deploy_with_retry(
            deployer=self._fabric_deployer,
            item_types=item_types,
            retries_remaining=deployment_retries,
            stage_description="Deployment",
        )
        return self._fabric_deployer

    def download_and_deploy(
        self,
        repo_owner: str = None,
        repo_name: str = None,
        workspace_folder: str = "workspace",
        branch: str = "main",
        github_token: str | None = None,
        extract_to: str | None = None,
        item_types: list[str] | None = None,
        item_type_stages: list[list[str]] | None = None,
        data_folders: dict[str, str] | None = None,
        lakehouse_name: str | None = None,
        data_file_patterns: list[str] | None = None,
        validate_after_deployment: bool = True,
        generate_report: bool = True,
        deployment_retries: int = 2,
        allow_non_empty_workspace: bool | None = None,
    ):
        """
        Download from GitHub and deploy in one operation.

        This method downloads the repository, deploys workspace artifacts, and optionally
        copies data folders to a Lakehouse. It supports configuration files, validation,
        and comprehensive reporting.

        Args:
            repo_owner: GitHub repository owner (or from config file)
            repo_name: GitHub repository name (or from config file)
            workspace_folder: Folder path within the repo containing workspace artifacts
            branch: Git branch to download (default: "main")
            github_token: GitHub personal access token (optional)
            extract_to: Local directory to extract files to (auto-generated if None)
            item_types: List of item types to deploy (None for all). Mutually exclusive with item_type_stages.
            item_type_stages: Array of arrays for staged deployment. Each inner array contains item types
                            to deploy in that stage. Example: [["Eventhouse", "KQLDatabase"], ["Notebook"]].
                            Mutually exclusive with item_types.
            data_folders: Optional dictionary mapping repository data folders to Lakehouse folders
                         e.g., {"data": "reference-data", "samples": "sample-data"}
            lakehouse_name: Name of Lakehouse for data upload (required if data_folders specified)
            data_file_patterns: Optional file patterns for data upload (e.g., ["*.json", "*.csv"])
            validate_after_deployment: Run post-deployment validation
            generate_report: Generate and display deployment report
            deployment_retries: Number of retry attempts on deployment failure (default: 2).
                               On retry, automatically sets allow_non_empty_workspace=True
                               since previous attempt may have deployed some items.
            allow_non_empty_workspace: Allow deployment to workspaces with existing items
                                       (None uses instance setting from __init__)

        Returns:
            Tuple of (GitHubDownloader, FabricDeployer, DeploymentReport) instances

        Example:
            >>> launcher.download_and_deploy(
            ...     repo_owner="myorg",
            ...     repo_name="my-solution",
            ...     workspace_folder="workspace",
            ...     data_folders={"data": "reference-data", "samples": "samples"},
            ...     lakehouse_name="ReferenceDataLH"
            ... )
        """
        print("=" * 60)
        print("🚀 Starting download and deployment workflow")
        print("=" * 60)

        # Initialize deployment report
        report = DeploymentReport() if generate_report else None

        if report:
            report.start_deployment(
                repo_owner=repo_owner,
                repo_name=repo_name,
                branch=branch,
                workspace_id=self.workspace_id,
            )
            report.add_step("Initialization", "success", "Beginning deployment workflow")

        # Validate mutually exclusive parameters
        if item_types is not None and item_type_stages is not None:
            error_msg = "❌ item_types and item_type_stages are mutually exclusive. Provide only one."
            if report:
                report.add_step("Initialization", "Failed", error_msg)
            raise ValueError(error_msg)

        # Use config file values if not provided as parameters
        if self.config:
            github_cfg = self.config.get_github_config()
            repo_owner = repo_owner or github_cfg.get("repo_owner")
            repo_name = repo_name or github_cfg.get("repo_name")
            branch = github_cfg.get("branch", branch)
            github_token = github_token or github_cfg.get("github_token")
            workspace_folder = github_cfg.get("workspace_folder", workspace_folder)

            deploy_cfg = self.config.get_deployment_config()
            item_types = item_types or deploy_cfg.get("item_types")
            validate_after_deployment = deploy_cfg.get("validate_after_deployment", validate_after_deployment)
            deployment_retries = deploy_cfg.get("deployment_retries", deployment_retries)
            if allow_non_empty_workspace is None:
                allow_non_empty_workspace = deploy_cfg.get("allow_non_empty_workspace", self.allow_non_empty_workspace)

            data_cfg = self.config.get_data_config()
            if data_cfg:
                data_folders = data_folders or data_cfg.get("folder_mappings")
                lakehouse_name = lakehouse_name or data_cfg.get("lakehouse_name")
                data_file_patterns = data_file_patterns or data_cfg.get("file_patterns")

        # Use instance setting if parameter not provided
        if allow_non_empty_workspace is None:
            allow_non_empty_workspace = self.allow_non_empty_workspace

        # Validate required parameters
        if not repo_owner or not repo_name:
            error_msg = "❌ repo_owner and repo_name are required. Provide them as parameters or in a config file."
            if report:
                report.add_step("Initialization", "Failed", error_msg)
            raise ValueError(error_msg)

        # Default extraction path
        if extract_to is None:
            extract_to = ".lakehouse/default/Files/src"

        # Step 1: Download entire repository
        if report:
            report.add_step("Download", "success", f"Downloading {repo_owner}/{repo_name}")

        print("\n📥 Step 1: Downloading from GitHub")
        try:
            downloader = self.download_repository(
                repo_owner=repo_owner,
                repo_name=repo_name,
                extract_to=extract_to,
                branch=branch,
                folder_to_extract="",  # Download entire repo
                github_token=github_token,
            )
            if report:
                report.add_step("Download", "success", f"Downloaded from {repo_owner}/{repo_name}")
        except Exception as e:
            if report:
                report.add_step("Download", "error", str(e))
            raise

        # Construct repository directory path
        repository_directory = str(Path(extract_to) / workspace_folder)

        # Step 2: Deploy artifacts
        if report:
            report.add_step("Deployment", "success", "Deploying workspace artifacts")

        print("\n🚀 Step 2: Deploying to Fabric workspace")

        try:
            # Handle staged deployment if item_type_stages provided
            if item_type_stages:
                print(f"📋 Deploying in {len(item_type_stages)} stages")

                # Initialize deployer once
                self._fabric_deployer = FabricDeployer(
                    workspace_id=self.workspace_id,
                    repository_directory=repository_directory,
                    notebookutils=self.notebookutils,
                    environment=self.environment,
                    api_root_url=self.api_root_url,
                    debug=self.debug,
                    allow_non_empty_workspace=allow_non_empty_workspace,
                    fix_zero_logical_ids=self.fix_zero_logical_ids,
                )

                # Deploy each stage with retry logic
                for stage_num, stage_item_types in enumerate(item_type_stages, 1):
                    stage_description = f"Stage {stage_num}/{len(item_type_stages)}: {', '.join(stage_item_types)}"
                    print(f"\n  📦 {stage_description}")
                    self._deploy_with_retry(
                        deployer=self._fabric_deployer,
                        item_types=stage_item_types,
                        retries_remaining=deployment_retries,
                        stage_description=stage_description,
                    )

                deployer = self._fabric_deployer
                print(f"\n✅ All {len(item_type_stages)} deployment stages completed")
            else:
                # Deploy items using deploy_artifacts (single stage)
                deployer = self.deploy_artifacts(
                    repository_directory=repository_directory,
                    item_types=item_types,
                    allow_non_empty_workspace=allow_non_empty_workspace,
                    deployment_retries=deployment_retries,
                )

            if report:
                report.add_step("Deployment", "success", "Workspace artifacts deployed")
        except Exception as e:
            if report:
                report.add_step("Deployment", "error", str(e))
                report.end_deployment(success=False)
            raise

        # Step 3: Copy data folders to Lakehouse (if specified)
        if data_folders and lakehouse_name:
            if report:
                report.add_step("Data Upload", "success", f"Copying data to {lakehouse_name}")

            print("\n📁 Step 3: Copying data folders to Lakehouse")
            try:
                self.copy_data_folders_to_lakehouse(
                    lakehouse_name=lakehouse_name,
                    repository_base_path=extract_to,
                    folder_mappings=data_folders,
                    file_patterns=data_file_patterns,
                    recursive=True,
                )
                if report:
                    report.add_step("Data Upload", "success", f"Data copied to {lakehouse_name}")
            except Exception as e:
                if report:
                    report.add_step("Data Upload", "error", str(e))
                print(f"\n⚠️ Warning: Data upload failed: {e}")
        elif data_folders and not lakehouse_name:
            print("\n⚠️ Warning: data_folders specified but lakehouse_name not provided. Skipping data upload.")

        # Step 4: Post-deployment validation
        validation_results = None
        if validate_after_deployment:
            if report:
                report.add_step("Validation", "success", "Running post-deployment validation")

            print("\n🔍 Step 4: Validating deployment")
            try:
                validation_results = self.validator.validate_deployment()

                if validation_results["all_accessible"]:
                    print("✅ All deployed items are accessible")
                    if report:
                        report.add_step("Validation", "success", "All items validated successfully")
                else:
                    print(f"⚠️ {validation_results['failed_count']} item(s) failed accessibility checks")
                    if report:
                        report.add_step(
                            "Validation", "warning", f"{validation_results['failed_count']} items not accessible"
                        )

                # Add validation results to report
                if report:
                    # Get detailed accessibility results if available
                    accessibility_check = validation_results.get("checks", {}).get("accessibility", {})
                    detailed_items = accessibility_check.get("items", [])

                    if detailed_items:
                        # Use detailed accessibility results
                        for item in detailed_items:
                            report.add_deployed_item(
                                item_name=item["name"],
                                item_type=item["type"],
                                status="success" if item.get("accessible", False) else "warning",
                                details=item.get("error"),
                            )
                    else:
                        # Fallback to basic items list
                        for item in validation_results.get("items", []):
                            report.add_deployed_item(item_name=item["name"], item_type=item["type"], status="success")
            except Exception as e:
                print(f"\n⚠️ Validation failed: {e}")
                if report:
                    report.add_step("Validation", "error", str(e))

        print("\n" + "=" * 60)
        print("✅ Download and deployment workflow completed!")
        print("=" * 60)

        # Mark deployment as completed
        if report:
            report.end_deployment(success=True)

        # Generate and display report
        if generate_report and report:
            print("\n")
            report.print_report()

            # Save report to file
            report_path = str(Path(extract_to) / f"deployment_report_{report.session_id}.json")
            report.save_report(report_path)
            print(f"\n📊 Detailed report saved to: {report_path}")

        return downloader, deployer, report

    def upload_files_to_lakehouse(
        self,
        lakehouse_name: str,
        source_directory: str,
        target_folder: str = "data",
        file_patterns: list[str] | None = None,
    ) -> None:
        """
        Upload files from a local directory to Lakehouse Files area.

        Args:
            lakehouse_name: Name of the target Lakehouse
            source_directory: Local directory containing files to upload
            target_folder: Target folder path in Lakehouse Files area
            file_patterns: List of file patterns to match (e.g., ["*.json"])
        """
        self.file_manager.upload_files_to_lakehouse(
            lakehouse_name=lakehouse_name,
            source_directory=source_directory,
            target_folder=target_folder,
            file_patterns=file_patterns,
        )

    def upload_file_to_lakehouse(self, lakehouse_name: str, file_path: str, target_folder: str = "data") -> None:
        """
        Upload a single file to Lakehouse Files area.

        Args:
            lakehouse_name: Name of the target Lakehouse
            file_path: Path to the file to upload
            target_folder: Target folder path in Lakehouse Files area
        """
        self.file_manager.upload_file_to_lakehouse(
            lakehouse_name=lakehouse_name, file_path=file_path, target_folder=target_folder
        )

    def copy_folder_to_lakehouse(
        self,
        lakehouse_name: str,
        source_folder: str,
        target_folder: str = "data",
        file_patterns: list[str] | None = None,
        recursive: bool = True,
    ) -> None:
        """
        Copy a folder from local repository to Lakehouse Files area.

        Args:
            lakehouse_name: Name of the target Lakehouse
            source_folder: Local folder path to copy from
            target_folder: Target folder path in Lakehouse Files area
            file_patterns: List of file patterns to match (e.g., ["*.json"])
            recursive: Whether to copy subdirectories recursively
        """
        self.file_manager.copy_folder_to_lakehouse(
            lakehouse_name=lakehouse_name,
            source_folder=source_folder,
            target_folder=target_folder,
            file_patterns=file_patterns,
            recursive=recursive,
        )

    def copy_data_folders_to_lakehouse(
        self,
        lakehouse_name: str,
        repository_base_path: str,
        folder_mappings: dict[str, str],
        file_patterns: list[str] | None = None,
        recursive: bool = True,
    ) -> None:
        """
        Copy multiple data folders from repository to Lakehouse.

        This is useful after downloading a repository that contains both workspace
        artifacts and data folders. The workspace folder is used for deployment,
        while data folders are copied to Lakehouse.

        Args:
            lakehouse_name: Name of the target Lakehouse
            repository_base_path: Base path where repository was extracted
            folder_mappings: Dictionary mapping repository folders to Lakehouse folders
                            e.g., {"data": "reference-data", "samples": "sample-data"}
            file_patterns: List of file patterns to match (e.g., ["*.json", "*.csv"])
            recursive: Whether to copy subdirectories recursively

        Example:
            >>> launcher.copy_data_folders_to_lakehouse(
            ...     lakehouse_name="ReferenceDataLH",
            ...     repository_base_path=".lakehouse/default/Files/src",
            ...     folder_mappings={
            ...         "data": "reference-data",
            ...         "samples": "sample-data"
            ...     }
            ... )
        """
        self.file_manager.download_and_copy_folders_to_lakehouse(
            lakehouse_name=lakehouse_name,
            github_downloader=None,  # Not needed for local copy
            repository_base_path=repository_base_path,
            folder_mappings=folder_mappings,
            file_patterns=file_patterns,
            recursive=recursive,
        )

    def run_notebook(
        self,
        notebook_name: str,
        parameters: dict[str, Any] | None = None,
        workspace_id: str | None = None,
        timeout_seconds: int = 3600,
    ) -> dict[str, Any]:
        """
        Trigger execution of a Fabric notebook (asynchronous).

        Args:
            notebook_name: Name of the notebook to execute
            parameters: Dictionary of parameters to pass to the notebook
            workspace_id: Target workspace ID (uses current if None)
            timeout_seconds: Timeout for notebook execution

        Returns:
            Dictionary with execution result information
        """
        return self.notebook_executor.run_notebook(
            notebook_name=notebook_name,
            workspace_id=workspace_id,
            parameters=parameters,
            timeout_seconds=timeout_seconds,
        )

    def run_notebook_synchronous(
        self, notebook_name: str, parameters: dict[str, Any] | None = None, timeout_seconds: int = 3600
    ) -> dict[str, Any]:
        """
        Run a notebook synchronously (blocks until completion).

        Args:
            notebook_name: Name of the notebook to execute
            parameters: Dictionary of parameters to pass to the notebook
            timeout_seconds: Timeout for notebook execution

        Returns:
            Dictionary with execution result information
        """
        return self.notebook_executor.run_notebook_synchronous(
            notebook_name=notebook_name, parameters=parameters, timeout_seconds=timeout_seconds
        )

    def get_notebook_job_status(self, notebook_id: str, job_id: str, workspace_id: str | None = None) -> dict[str, Any]:
        """
        Get the status of a notebook job.

        Args:
            notebook_id: ID of the notebook
            job_id: ID of the job
            workspace_id: Target workspace ID (uses current if None)

        Returns:
            Dictionary with job status information
        """
        return self.notebook_executor.get_job_status(notebook_id=notebook_id, job_id=job_id, workspace_id=workspace_id)

    def validate_deployment(
        self,
        test_notebooks: bool = True,
        test_lakehouses: bool = True,
        test_notebooks_list: list[str] | None = None,
        test_lakehouses_list: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Validate deployed items are accessible and functional.

        Args:
            test_notebooks: Test notebook accessibility
            test_lakehouses: Test lakehouse accessibility
            test_notebooks_list: Specific notebooks to test (tests all if None)
            test_lakehouses_list: Specific lakehouses to test (tests all if None)

        Returns:
            Dictionary with validation results
        """
        return self.validator.validate_deployment(
            test_notebooks=test_notebooks,
            test_lakehouses=test_lakehouses,
            test_notebooks_list=test_notebooks_list,
            test_lakehouses_list=test_lakehouses_list,
        )

    def create_config_template(self, output_path: str = "deployment_config.yaml") -> None:
        """
        Create a template configuration file.

        Args:
            output_path: Path where to save the template config file
        """
        DeploymentConfig.create_template(output_path)
        print(f"✅ Configuration template created at: {output_path}")
        print("📝 Edit this file with your deployment settings")
