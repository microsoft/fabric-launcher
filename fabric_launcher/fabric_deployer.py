"""Fabric Deployment Module

This module provides functionality to deploy Fabric workspace items using fabric-cicd library.
Designed to work within Fabric notebooks with notebookutils available.
"""

__all__ = ["FabricNotebookTokenCredential", "FabricDeployer"]

import base64
import json
from typing import Any

import fabric_cicd.constants
from azure.core.credentials import AccessToken, TokenCredential
from fabric_cicd import FabricWorkspace, publish_all_items

from fabric_launcher.platform_file_fixer import PlatformFileFixer


class FabricNotebookTokenCredential(TokenCredential):
    """
    Token credential for Fabric Notebooks using notebookutils authentication.

    This class enables the fabric-cicd library to authenticate when run in a Fabric notebook
    by leveraging the notebookutils.credentials API.
    """

    def __init__(self, notebookutils):
        """
        Initialize the credential with notebookutils.

        Args:
            notebookutils: The notebookutils module from Fabric notebook environment
        """
        self.notebookutils = notebookutils

    def get_token(
        self,
        *scopes: str,
        claims: str | None = None,
        tenant_id: str | None = None,
        enable_cae: bool = False,
        **kwargs: Any,
    ) -> AccessToken:
        """
        Get access token from Fabric notebook environment.

        Args:
            scopes: Token scopes (not used in Fabric notebook context)
            claims: Optional claims
            tenant_id: Optional tenant ID
            enable_cae: Enable Continuous Access Evaluation
            **kwargs: Additional keyword arguments

        Returns:
            AccessToken with token and expiration
        """
        access_token = self.notebookutils.credentials.getToken("pbi")
        expiration = self._extract_jwt_expiration(access_token)
        return AccessToken(token=access_token, expires_on=expiration)

    def _extract_jwt_expiration(self, token: str) -> int:
        """
        Extract expiration timestamp from JWT token.

        Args:
            token: JWT token string

        Returns:
            Expiration timestamp as integer

        Raises:
            ValueError: If token format is invalid or missing expiration
        """
        try:
            # Split JWT and get payload (middle part)
            payload_b64 = token.split(".")[1]
            # Add padding if needed for base64 decoding
            payload_b64 += "=" * (-len(payload_b64) % 4)
            # Decode and parse payload
            payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
            payload = json.loads(payload_bytes.decode("utf-8"))
            # Extract expiration claim
            exp = payload.get("exp")
            if exp is None:
                raise ValueError("JWT missing expiration claim")
            return exp
        except (IndexError, json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid JWT token format: {e}") from e


class FabricDeployer:
    """
    Handler for deploying Fabric workspace items.

    This class wraps the fabric-cicd library functionality and provides
    methods to deploy various types of Fabric items.
    """

    def __init__(
        self,
        workspace_id: str,
        repository_directory: str,
        notebookutils,
        environment: str = "DEV",
        api_root_url: str = "https://api.fabric.microsoft.com",
        debug: bool = False,
        allow_non_empty_workspace: bool = False,
        fix_zero_logical_ids: bool = True,
    ):
        """
        Initialize the Fabric deployer.

        Args:
            workspace_id: Target Fabric workspace ID
            repository_directory: Local directory containing Fabric item definitions
            notebookutils: The notebookutils module from Fabric notebook environment
            environment: Deployment environment (DEV, TEST, PROD)
            api_root_url: Fabric API root URL
            debug: Enable debug logging
            allow_non_empty_workspace: Allow deployment to workspaces with existing items
            fix_zero_logical_ids: Fix zero GUID logicalIds in .platform files
        """
        self.workspace_id = workspace_id
        self.repository_directory = repository_directory
        self.environment = environment
        self.notebookutils = notebookutils
        self.allow_non_empty_workspace = allow_non_empty_workspace
        self.fix_zero_logical_ids = fix_zero_logical_ids
        self._deployment_session_started = False  # Track if first deployment has occurred

        # Configure fabric-cicd constants
        fabric_cicd.constants.DEFAULT_API_ROOT_URL = api_root_url

        # Enable debug logging if requested
        if debug:
            from fabric_cicd import change_log_level

            change_log_level("DEBUG")

        # Initialize token credential
        self.token_credential = FabricNotebookTokenCredential(notebookutils)

        # Initialize FabricWorkspace
        self.workspace = FabricWorkspace(
            workspace_id=workspace_id,
            environment=environment,
            repository_directory=repository_directory,
            token_credential=self.token_credential,
        )

    def _validate_workspace_is_empty(self) -> None:
        """
        Validate that the workspace only contains the current notebook.

        Raises:
            RuntimeError: If workspace contains items other than the current notebook
        """
        import sempy.fabric as fabric

        # Get current notebook context
        try:
            current_notebook_name = self.notebookutils.runtime.context["currentNotebookName"]
        except Exception:
            # If we can't get the notebook name, skip validation
            print("⚠️ Warning: Could not determine current notebook name. Skipping workspace validation.")
            return

        # Get all items in the workspace
        try:
            all_items = fabric.list_items(workspace=self.workspace_id)

            if all_items.empty:
                print("✅ Workspace validation passed: Workspace is empty")
                return

            # Filter out the current notebook
            other_items = all_items[all_items["Display Name"] != current_notebook_name]

            if other_items.empty:
                print(f"✅ Workspace validation passed: Only contains current notebook '{current_notebook_name}'")
                return

            # Workspace contains other items
            print("=" * 60)
            print("❌ WORKSPACE VALIDATION FAILED")
            print("=" * 60)
            print(f"The target workspace contains {len(other_items)} item(s) in addition to the current notebook.")
            print("\nExisting items:")
            for _idx, item in other_items.iterrows():
                print(f"  • {item['Display Name']} ({item['Type']})")

            print("\n⚠️ DEPLOYMENT BLOCKED")
            print("To deploy to a non-empty workspace, initialize FabricDeployer with:")
            print("  allow_non_empty_workspace=True")
            print("=" * 60)

            raise RuntimeError(
                f"Workspace contains {len(other_items)} existing item(s). "
                "Deployment to non-empty workspaces requires explicit confirmation. "
                "Set allow_non_empty_workspace=True to proceed."
            )

        except RuntimeError:
            # Re-raise our validation error
            raise
        except Exception as e:
            print(f"⚠️ Warning: Could not validate workspace contents: {e}")
            print("Proceeding with deployment...")

    def deploy_items(self, item_types: list[str] | None = None) -> None:
        """
        Deploy Fabric items to the workspace.

        For staged deployments, workspace validation only occurs on the first stage.
        Subsequent stages in the same deployment session skip validation since the
        workspace is expected to contain items from previous stages.

        Args:
            item_types: List of item types to deploy. If None, deploys all items.
                       Example types: "Lakehouse", "Notebook", "Eventstream", "KQLDatabase"
        """
        # Fix zero GUID logicalIds in .platform files (if enabled)
        if self.fix_zero_logical_ids:
            print("🔧 Checking for zero GUID logicalIds in .platform files...")
            fixer = PlatformFileFixer(self.repository_directory)
            results = fixer.scan_and_fix_all(dry_run=False)

            if results["files_fixed"] > 0:
                print(f"✅ Fixed {results['files_fixed']} .platform file(s) with zero GUID logicalIds")
            elif results["files_with_zero_guid"] > 0:
                print(f"⚠️ Warning: Found {results['files_with_zero_guid']} file(s) with issues but could not fix them")
        else:
            print("⚠️ Skipping logicalId validation (fix_zero_logical_ids=False)")

        # Validate workspace is empty (unless explicitly allowed or already validated in this session)
        if not self.allow_non_empty_workspace:
            if not self._deployment_session_started:
                # First deployment in this session - validate workspace is empty
                print("🔍 Validating workspace is empty...")
                self._validate_workspace_is_empty()
                self._deployment_session_started = True
                print("✅ Workspace validation passed - subsequent stages will skip validation")
            else:
                # Subsequent deployment in same session - skip validation
                print("ℹ️ Skipping workspace validation (already validated in this deployment session)")
        else:
            print("⚠️ Skipping workspace validation (allow_non_empty_workspace=True)")

        if item_types:
            self.workspace.item_type_in_scope = item_types
            print("🚀 Starting deployment of Fabric items...")
            print(f"📋 Item types in scope: {', '.join(item_types)}")
        else:
            print("🚀 Starting deployment of all Fabric items...")

        publish_all_items(self.workspace)
        print("✅ Deployment completed successfully!")
