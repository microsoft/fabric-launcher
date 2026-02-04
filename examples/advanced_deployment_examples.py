"""
Typical Fabric Notebook Deployment Workflow

This example demonstrates the recommended workflow for deploying a Fabric solution
from a GitHub repository using configuration files stored in the repository.

This is the most common use case for fabric-launcher in production environments.
"""

import notebookutils

from fabric_launcher import FabricLauncher

# ============================================================================
# Recommended Workflow: Config in GitHub Repository
# ============================================================================


def production_deployment_workflow():
    """
    Production deployment workflow with config stored in GitHub.

    This is the recommended approach because:
    1. Configuration is version-controlled alongside your solution code
    2. No local file management needed in Fabric notebooks
    3. Different environments can have different config files
    4. Team collaboration is easier with centralized config
    """

    # Step 1: Define your GitHub repository details
    REPO_OWNER = "myorg"  # noqa: N806
    REPO_NAME = "my-fabric-solution"  # noqa: N806
    CONFIG_FILE_PATH = "config/deployment_prod.yaml"  # Path in your repo  # noqa: N806
    GITHUB_TOKEN = None  # Set if private repo, or use notebookutils.credentials  # noqa: N806

    # Optional: Get GitHub token from Fabric Key Vault if needed
    # GITHUB_TOKEN = notebookutils.credentials.getSecret("MyKeyVault", "github-token")

    print("=" * 70)
    print("🚀 Starting Production Deployment")
    print("=" * 70)

    # Step 2: Initialize FabricLauncher with config from GitHub
    # This automatically downloads the config file from your repository
    launcher = FabricLauncher(
        notebookutils,
        config_repo_owner=REPO_OWNER,
        config_repo_name=REPO_NAME,
        config_file_path=CONFIG_FILE_PATH,
        config_branch="main",
        config_github_token=GITHUB_TOKEN,
        environment="PROD",  # Environment-specific overrides from config
    )

    # Step 3: Deploy using settings from configuration file
    # The config file contains:
    # - Repository details (owner, name, branch, workspace folder)
    # - Deployment settings (staged deployment, validation, retries)
    # - Data upload settings (lakehouse, folder mappings)
    downloader, deployer, report = launcher.download_and_deploy(
        # All parameters come from config file, but can be overridden here if needed
        # validate_after_deployment=True,  # Override config setting if needed
        # deployment_retries=5  # Override config setting if needed
    )

    print("\n" + "=" * 70)
    print("✅ Deployment Completed Successfully!")
    print("=" * 70)

    # Step 4: Display deployment report
    if report:
        print("\n📊 Deployment Summary:")
        print(f"   Duration: {report.duration_seconds:.2f} seconds")
        print(f"   Deployed Items: {len(report.deployed_items)}")
        print(f"   Session ID: {report.session_id}")


# ============================================================================
# Alternative: Minimal Parameters (All from Config)
# ============================================================================


def minimal_deployment():
    """
    Minimal deployment with all settings in config file.

    This is the cleanest approach - just provide repo details and config path,
    everything else comes from the configuration file.
    """

    # Initialize with config from GitHub
    launcher = FabricLauncher(
        notebookutils,
        config_repo_owner="myorg",
        config_repo_name="my-solution",
        config_file_path="config/deployment.yaml",
        environment="PROD",
    )

    # Deploy - all settings from config
    launcher.download_and_deploy()


# ============================================================================
# Development Environment Workflow
# ============================================================================


def dev_environment_deployment():
    """
    Development environment deployment with dev-specific config.

    Uses a different config file for development environment.
    """

    # Use dev-specific configuration file
    launcher = FabricLauncher(
        notebookutils,
        config_repo_owner="myorg",
        config_repo_name="my-solution",
        config_file_path="config/deployment_dev.yaml",  # Dev config
        config_branch="dev",  # Deploy from dev branch
        environment="DEV",
    )

    # Deploy to dev environment
    downloader, deployer, report = launcher.download_and_deploy()

    print("✅ Development deployment completed!")


# ============================================================================
# Multi-Environment Deployment with Single Config
# ============================================================================


def multi_environment_single_config():
    """
    Deploy to different environments using a single config file
    with environment-specific overrides.

    Your deployment.yaml would have sections like:

    environments:
      DEV:
        github:
          branch: dev
        deployment:
          validate_after_deployment: false

      PROD:
        github:
          branch: main
        deployment:
          deployment_retries: 5
          validate_after_deployment: true
    """

    # Same config file, different environment parameter
    # The config file has environment-specific overrides

    # Deploy to DEV
    launcher_dev = FabricLauncher(
        notebookutils,
        config_repo_owner="myorg",
        config_repo_name="my-solution",
        config_file_path="config/deployment.yaml",
        environment="DEV",  # Uses DEV overrides from config
    )
    launcher_dev.download_and_deploy()

    # Deploy to PROD
    launcher_prod = FabricLauncher(
        notebookutils,
        config_repo_owner="myorg",
        config_repo_name="my-solution",
        config_file_path="config/deployment.yaml",
        environment="PROD",  # Uses PROD overrides from config
    )
    launcher_prod.download_and_deploy()


# ============================================================================
# Private Repository with Token from Key Vault
# ============================================================================


def private_repo_with_keyvault():
    """
    Deploy from private repository using GitHub token from Fabric Key Vault.

    This is the secure way to handle private repositories in production.
    """

    # Retrieve GitHub token from Key Vault
    # (You need to create a Key Vault and store your GitHub token there first)
    KEY_VAULT_NAME = "MyFabricKeyVault"  # noqa: N806
    SECRET_NAME = "github-personal-access-token"  # noqa: N806

    try:
        github_token = notebookutils.credentials.getSecret(KEY_VAULT_NAME, SECRET_NAME)
        print("🔐 GitHub token retrieved from Key Vault")
    except Exception as e:
        print(f"⚠️ Could not retrieve token from Key Vault: {e}")
        print("💡 Make sure the Key Vault exists and contains the secret")
        github_token = None

    # Initialize launcher with token
    launcher = FabricLauncher(
        notebookutils,
        config_repo_owner="myorg",
        config_repo_name="my-private-solution",  # Private repository
        config_file_path="config/deployment.yaml",
        config_github_token=github_token,  # Token for private repo access
        environment="PROD",
    )

    # Deploy
    launcher.download_and_deploy()


# ============================================================================
# Parameter Override Example
# ============================================================================


def config_with_parameter_overrides():
    """
    Use config file for most settings, but override specific parameters.

    This is useful when you want consistent base configuration but need
    to override specific values for a particular deployment.
    """

    # Initialize with config from GitHub
    launcher = FabricLauncher(
        notebookutils,
        config_repo_owner="myorg",
        config_repo_name="my-solution",
        config_file_path="config/deployment.yaml",
        environment="PROD",
    )

    # Deploy with parameter overrides
    downloader, deployer, report = launcher.download_and_deploy(
        # Override config file settings for this specific deployment
        branch="hotfix-branch",  # Deploy from different branch
        validate_after_deployment=True,  # Force validation
        deployment_retries=10,  # More retries for this deployment
        lakehouse_name="CustomLakehouse",  # Use different lakehouse
    )

    print("✅ Deployment completed with parameter overrides!")


# ============================================================================
# Run the Examples
# ============================================================================

if __name__ == "__main__":
    """
    Uncomment the workflow you want to execute.

    For most production deployments, use: production_deployment_workflow()
    """

    print("\n" + "=" * 70)
    print("Fabric Launcher - Production Deployment Workflows")
    print("=" * 70 + "\n")

    # Recommended for production
    # production_deployment_workflow()

    # Minimal setup
    # minimal_deployment()

    # Development environment
    # dev_environment_deployment()

    # Multi-environment
    # multi_environment_single_config()

    # Private repository
    # private_repo_with_keyvault()

    # With overrides
    # config_with_parameter_overrides()

    print("\n💡 Tip: Store your configuration files in your GitHub repository")
    print("   alongside your Fabric solution code for version control and")
    print("   easy team collaboration!")
