"""
Fabric Deployment Module

This module provides functionality to deploy Fabric workspace items using fabric-cicd library.
Designed to work within Fabric notebooks with notebookutils available.
"""

import base64
import json
import time
from typing import Any, Optional

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
        claims: Optional[str] = None,
        tenant_id: Optional[str] = None,
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
            raise ValueError(f"Invalid JWT token format: {e}")


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

    @staticmethod
    def _retry_on_failure(func, max_retries: int = 3, delay_seconds: int = 5, operation_name: str = "Operation"):
        """
        Retry a function on failure with exponential backoff.

        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            delay_seconds: Initial delay between retries (doubles each time)
            operation_name: Name of operation for error messages

        Returns:
            Function result if successful

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_exception = e

                if attempt < max_retries - 1:
                    wait_time = delay_seconds * (2**attempt)
                    print(f"⚠️ {operation_name} failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    print(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ {operation_name} failed after {max_retries} attempts")

        # All retries failed
        error_msg = f"{operation_name} failed after {max_retries} attempts. Last error: {str(last_exception)}"

        # Provide helpful suggestions based on error type
        suggestions = []
        error_str = str(last_exception).lower()

        if "unauthorized" in error_str or "403" in error_str:
            suggestions.append("Check workspace permissions - you need Member or Admin role")
            suggestions.append("Verify your authentication token is valid")
        elif "not found" in error_str or "404" in error_str:
            suggestions.append("Verify the workspace ID is correct")
            suggestions.append("Check that all referenced items exist")
        elif "timeout" in error_str or "timed out" in error_str:
            suggestions.append("The operation may take longer - try increasing timeout")
            suggestions.append("Check your network connection")
        elif "already exists" in error_str or "conflict" in error_str or "409" in error_str:
            suggestions.append("An item with this name already exists")
            suggestions.append("Consider using allow_non_empty_workspace=True if intentional")
        elif "capacity" in error_str:
            suggestions.append("Check that your Fabric capacity is running")
            suggestions.append("Verify capacity has sufficient resources")

        if suggestions:
            error_msg += "\n\n💡 Suggestions:\n"
            for suggestion in suggestions:
                error_msg += f"  • {suggestion}\n"

        raise Exception(error_msg)

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

    def deploy_items(self, item_types: Optional[list[str]] = None) -> None:
        """
        Deploy Fabric items to the workspace.

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

        # Validate workspace is empty (unless explicitly allowed)
        if not self.allow_non_empty_workspace:
            print("🔍 Validating workspace is empty...")
            self._validate_workspace_is_empty()
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
