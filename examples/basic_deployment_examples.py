"""
Advanced Usage Examples for fabric-launcher

This file demonstrates advanced capabilities including:
- Configuration file support
- Post-deployment validation
- Deployment reporting
- Retry logic
- Enhanced error handling
- Custom post-deployment scenarios

Note: fabric-launcher wraps fabric-cicd for deployment operations.
For parameterization and value replacement guidance, see:
https://microsoft.github.io/fabric-cicd/0.1.3/
"""

import notebookutils

from fabric_launcher import FabricLauncher

# ============================================================================
# Example 1: Using Configuration Files from GitHub
# ============================================================================


def example_config_from_github():
    """Deploy using a configuration file downloaded from GitHub repository."""

    # Method 1: Initialize launcher with config from GitHub (recommended)
    launcher = FabricLauncher(
        notebookutils,
        config_repo_owner="myorg",
        config_repo_name="my-solution",
        config_file_path="config/deployment.yaml",  # Path within the repo
        config_branch="main",
        config_github_token="ghp_xxx",  # Optional, for private repos
        environment="PROD",
    )

    # Deploy using config file settings
    # All parameters (repo, workspace_folder, data_folders, etc.) come from config
    downloader, deployer, report = launcher.download_and_deploy()

    print("✅ Deployment completed using configuration file from GitHub!")


def example_config_download_then_use():
    """Download config file first, then use it."""

    # Method 2: Download config file separately, then initialize launcher
    config_path = FabricLauncher.download_config_from_github(
        repo_owner="myorg",
        repo_name="my-solution",
        config_file_path="config/deployment.yaml",
        save_to="my_deployment_config.yaml",  # Optional: save to specific location
    )

    # Initialize launcher with downloaded config
    launcher = FabricLauncher(notebookutils, config_file=config_path, environment="DEV")

    # Deploy using config file settings
    downloader, deployer, report = launcher.download_and_deploy()

    print("✅ Deployment completed using downloaded configuration file!")


def example_local_config_file():
    """Deploy using a local configuration file (for development/testing)."""

    # Create a template configuration file (one-time)
    from fabric_launcher import DeploymentConfig

    DeploymentConfig.create_template("my_deployment_config.yaml")

    # Edit the file with your settings, then use it
    launcher = FabricLauncher(notebookutils, config_file="my_deployment_config.yaml", environment="DEV")

    # Deploy using config file settings
    downloader, deployer, report = launcher.download_and_deploy()

    print("✅ Deployment completed using local configuration file!")


# ============================================================================
# Example 2: Deployment with Validation and Reporting
# ============================================================================


def example_validated_deployment():
    """Deploy with automatic validation and comprehensive reporting."""

    launcher = FabricLauncher(notebookutils, environment="TEST")

    # Deploy with validation and reporting enabled
    downloader, deployer, report = launcher.download_and_deploy(
        repo_owner="myorg",
        repo_name="my-solution",
        workspace_folder="workspace",
        validate_after_deployment=True,  # Run post-deployment validation
        generate_report=True,  # Generate deployment report
        max_retries=3,  # Retry failed operations up to 3 times
    )

    # The report is automatically printed and saved
    # You can also access it programmatically
    if report:
        print(f"\nDeployment Session ID: {report.session_id}")
        print(f"Total Duration: {report.duration_seconds:.2f} seconds")

        # Check if any steps failed
        failed_steps = [step for step in report.steps if step["status"] == "Failed"]
        if failed_steps:
            print(f"\n⚠️ {len(failed_steps)} step(s) failed:")
            for step in failed_steps:
                print(f"  - {step['step_name']}: {step['details']}")


# ============================================================================
# Example 3: Manual Validation After Deployment
# ============================================================================


def example_manual_validation():
    """Deploy and then manually validate specific items."""

    launcher = FabricLauncher(notebookutils)

    # Deploy without automatic validation
    downloader, deployer, report = launcher.download_and_deploy(
        repo_owner="myorg", repo_name="my-solution", validate_after_deployment=False
    )

    # Later, manually validate specific items
    print("\n🔍 Running manual validation...")

    validation_results = launcher.validate_deployment(
        test_notebooks=True,
        test_lakehouses=True,
        test_notebooks_list=["DataProcessor", "ReportGenerator"],
        test_lakehouses_list=["RawData", "ProcessedData"],
    )

    # Check results
    if validation_results["all_accessible"]:
        print("✅ All items passed validation!")
    else:
        print(f"⚠️ {validation_results['failed_count']} items failed validation")

        # Print details of failed items
        for item in validation_results["items"]:
            if not item["accessible"]:
                print(f"  ❌ {item['name']} ({item['type']}): {item['error']}")


# ============================================================================
# Example 4: Configuration File with Multiple Environments
# ============================================================================


def example_multi_environment_config():
    """Use configuration file with environment-specific overrides."""

    # Example config file structure (save as deployment_config.yaml):
    """
    github:
      repo_owner: myorg
      repo_name: my-solution
      branch: main
      workspace_folder: workspace

    deployment:
      validate_after_deployment: true
      max_retries: 3

    data:
      lakehouse_name: DataLH
      folder_mappings:
        data/reference: reference-data
        data/samples: sample-data
      file_patterns:
        - "*.json"
        - "*.csv"

    environments:
      DEV:
        deployment:
          item_types:
            - Lakehouse
            - Notebook

      TEST:
        github:
          branch: test
        data:
          lakehouse_name: TestDataLH

      PROD:
        deployment:
          validate_after_deployment: true
          max_retries: 5
        allow_non_empty_workspace: false
    """

    # Deploy to DEV
    launcher_dev = FabricLauncher(notebookutils, config_file="deployment_config.yaml", environment="DEV")
    launcher_dev.download_and_deploy()

    # Deploy to PROD with environment-specific settings
    launcher_prod = FabricLauncher(notebookutils, config_file="deployment_config.yaml", environment="PROD")
    launcher_prod.download_and_deploy()


# ============================================================================
# Example 5: Custom Deployment with Retry Logic
# ============================================================================


def example_retry_and_error_handling():
    """Demonstrate retry logic and enhanced error handling."""

    launcher = FabricLauncher(
        notebookutils,
        debug=True,  # Enable detailed logging
    )

    try:
        # Deploy with custom retry settings
        downloader, deployer, report = launcher.download_and_deploy(
            repo_owner="myorg",
            repo_name="my-solution",
            workspace_folder="workspace",
            max_retries=5,  # Retry up to 5 times on failure
            generate_report=True,
        )

        print("✅ Deployment succeeded!")

    except Exception as e:
        print(f"❌ Deployment failed: {e}")

        # The error message includes helpful suggestions
        # Example output:
        # """
        # ❌ Deployment failed: Workspace validation failed after 3 attempts.
        #
        # 💡 Suggestions:
        #   • Check workspace permissions - you need Contributor or Admin role
        #   • Verify your authentication token is valid
        # """


# ============================================================================
# Example 6: Programmatic Report Analysis
# ============================================================================


def example_report_analysis():
    """Analyze deployment report programmatically."""

    launcher = FabricLauncher(notebookutils)

    # Deploy with reporting
    _, _, report = launcher.download_and_deploy(repo_owner="myorg", repo_name="my-solution", generate_report=True)

    if report:
        # Save report to file
        report.save_report("deployment_report.json")

        # Analyze report
        print("\n📊 Deployment Report Analysis")
        print("=" * 60)
        print(f"Session ID: {report.session_id}")
        print(f"Timestamp: {report.timestamp}")
        print(f"Duration: {report.duration_seconds:.2f} seconds")
        print(f"Total Steps: {len(report.steps)}")

        # Count step statuses
        status_counts = {}
        for step in report.steps:
            status = step["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        print("\nStep Status Summary:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")

        # List deployed items
        if report.deployed_items:
            print(f"\nDeployed Items ({len(report.deployed_items)}):")
            for item in report.deployed_items:
                status_icon = "✅" if item["status"] == "Success" else "⚠️"
                print(f"  {status_icon} {item['item_name']} ({item['item_type']})")


# ============================================================================
# Example 7: Creating Configuration Templates
# ============================================================================


def example_config_templates():
    """Generate and customize configuration templates."""

    from fabric_launcher import DeploymentConfig

    # Create a template configuration file
    DeploymentConfig.create_template("my_config.yaml")
    print("✅ Configuration template created: my_config.yaml")

    # Load and inspect configuration
    config = DeploymentConfig(config_path="my_config.yaml")

    # Get configuration sections
    github_config = config.get_github_config()
    deployment_config = config.get_deployment_config()
    data_config = config.get_data_config()

    print(f"\nGitHub Config: {github_config}")
    print(f"Deployment Config: {deployment_config}")
    print(f"Data Config: {data_config}")


# ============================================================================
# Example 8: Custom Deployment Scenarios
# ============================================================================


def example_custom_item_deployment():
    """Deploy unsupported item types using post-deployment notebook."""

    launcher = FabricLauncher(notebookutils)

    # Deploy supported items first
    launcher.download_and_deploy(repo_owner="myorg", repo_name="my-solution")

    # Run post-deployment notebook for custom item types
    # Your notebook can contain custom code to deploy unsupported items
    result = launcher.run_notebook(
        notebook_name="Deploy-Custom-Items", parameters={"environment": "prod", "deploy_custom_connectors": True}
    )

    print(f"✅ Custom deployment completed. Job ID: {result['job_id']}")


def example_post_deployment_configuration():
    """Configure deployed items using post-deployment notebook."""

    launcher = FabricLauncher(notebookutils)

    # Deploy all items
    downloader, deployer, report = launcher.download_and_deploy(
        repo_owner="myorg", repo_name="my-solution", generate_report=True
    )

    # Run post-deployment configuration
    # Your notebook can configure permissions, connections, etc.
    result = launcher.run_notebook(
        notebook_name="Post-Deploy-Config",
        parameters={
            "setup_permissions": True,
            "initialize_data": True,
            "configure_connections": True,
            "deployed_items": len(report.deployed_items),
        },
    )

    print(f"✅ Post-deployment configuration completed. Job ID: {result['job_id']}")


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    print("Advanced fabric-launcher Examples")
    print("=" * 60)

    # Uncomment the example you want to run:

    # example_config_based_deployment()
    # example_validated_deployment()
    # example_manual_validation()
    # example_multi_environment_config()
    # example_retry_and_error_handling()
    # example_report_analysis()
    # example_config_templates()
    # example_custom_item_deployment()
    # example_post_deployment_configuration()
