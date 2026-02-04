"""
Staged Deployment Examples

This module demonstrates different patterns for staging Fabric item deployments
using the item_type_stages parameter. Staging ensures dependencies are deployed
before dependent items.
"""

import notebookutils

from fabric_launcher import FabricLauncher

# ============================================================================
# Example 1: Basic Three-Stage Deployment
# ============================================================================


def example_basic_staged_deployment():
    """Deploy in three stages: data stores, compute, analytics."""

    launcher = FabricLauncher(notebookutils)

    launcher.download_and_deploy(
        repo_owner="myorg",
        repo_name="my-solution",
        workspace_folder="workspace",
        item_type_stages=[
            ["Lakehouse", "KQLDatabase", "Eventhouse"],  # Stage 1: Data stores
            ["Notebook", "Eventstream"],  # Stage 2: Compute
            ["SemanticModel", "Report", "KQLDashboard"],  # Stage 3: Analytics
        ],
    )

    print("✅ Three-stage deployment completed!")


# ============================================================================
# Example 2: Two-Stage Deployment (Data then Everything Else)
# ============================================================================


def example_two_stage_deployment():
    """Deploy data stores first, then all other items."""

    launcher = FabricLauncher(notebookutils)

    launcher.download_and_deploy(
        repo_owner="myorg",
        repo_name="my-solution",
        item_type_stages=[
            ["Lakehouse", "KQLDatabase"],  # Stage 1: Data stores only
            [
                "Notebook",
                "Eventstream",
                "SemanticModel",
                "Report",
            ],  # Stage 2: Everything else
        ],
    )

    print("✅ Two-stage deployment completed!")


# ============================================================================
# Example 3: Fine-Grained Staging for Complex Dependencies
# ============================================================================


def example_complex_staged_deployment():
    """
    Deploy in multiple stages with fine-grained control for complex dependencies.

    Use case: When you have specific dependency chains like:
    - Lakehouses must exist before Notebooks can reference them
    - Notebooks must run before Reports can use their outputs
    - Semantic models depend on specific data being loaded
    """

    launcher = FabricLauncher(notebookutils)

    launcher.download_and_deploy(
        repo_owner="myorg",
        repo_name="complex-solution",
        workspace_folder="workspace",
        item_type_stages=[
            ["Lakehouse"],  # Stage 1: Create data storage
            ["KQLDatabase", "Eventhouse"],  # Stage 2: Add real-time analytics
            ["Notebook"],  # Stage 3: Deploy data processing notebooks
            ["SemanticModel"],  # Stage 4: Deploy semantic models
            ["Report", "KQLDashboard"],  # Stage 5: Deploy visualization
        ],
    )

    print("✅ Complex staged deployment completed!")


# ============================================================================
# Example 4: Staged Deployment with Data Upload
# ============================================================================


def example_staged_with_data():
    """Deploy in stages and upload reference data between stages."""

    launcher = FabricLauncher(notebookutils, environment="PROD")

    # Stage 1: Deploy data stores and upload reference data
    launcher.download_and_deploy(
        repo_owner="myorg",
        repo_name="my-solution",
        workspace_folder="workspace",
        item_type_stages=[
            ["Lakehouse", "KQLDatabase"],  # Deploy data stores first
        ],
        data_folders={"data": "reference-data"},  # Upload data files
        lakehouse_name="ReferenceDataLH",
        data_file_patterns=["*.json", "*.csv"],
    )

    print("✅ Stage 1 completed: Data stores deployed and data uploaded")

    # Stage 2: Deploy compute and analytics (now that data is ready)
    launcher.download_and_deploy(
        repo_owner="myorg",
        repo_name="my-solution",
        workspace_folder="workspace",
        item_type_stages=[
            ["Notebook", "Eventstream"],  # Compute
            ["SemanticModel", "Report"],  # Analytics
        ],
    )

    print("✅ Stage 2 completed: Compute and analytics deployed")


# ============================================================================
# Example 5: Conditional Staging Based on Environment
# ============================================================================


def example_environment_based_staging():
    """Use different staging strategies for different environments."""

    import os

    environment = os.environ.get("FABRIC_ENV", "DEV")
    launcher = FabricLauncher(notebookutils, environment=environment)

    if environment == "DEV":
        # DEV: Deploy everything at once for faster iteration
        launcher.download_and_deploy(
            repo_owner="myorg",
            repo_name="my-solution",
            workspace_folder="workspace",
            # No item_type_stages = deploy all at once
        )
        print("✅ DEV: Fast deployment completed")

    elif environment == "TEST":
        # TEST: Two-stage deployment for basic validation
        launcher.download_and_deploy(
            repo_owner="myorg",
            repo_name="my-solution",
            workspace_folder="workspace",
            item_type_stages=[
                ["Lakehouse", "KQLDatabase"],  # Data first
                ["Notebook", "SemanticModel", "Report"],  # Then compute/analytics
            ],
            validate_after_deployment=True,
        )
        print("✅ TEST: Two-stage deployment with validation completed")

    else:  # PROD
        # PROD: Fine-grained staging with validation and reporting
        launcher.download_and_deploy(
            repo_owner="myorg",
            repo_name="my-solution",
            workspace_folder="workspace",
            item_type_stages=[
                ["Lakehouse", "KQLDatabase"],
                ["Notebook", "Eventstream"],
                ["SemanticModel"],
                ["Report", "KQLDashboard"],
            ],
            validate_after_deployment=True,
            generate_report=True,
            deployment_retries=5,
        )
        print("✅ PROD: Multi-stage deployment with full validation completed")


# ============================================================================
# Example 6: Staged Deployment with Post-Stage Validation
# ============================================================================


def example_staged_with_validation():
    """Validate items after each stage before proceeding."""

    launcher = FabricLauncher(notebookutils)

    # Stage 1: Deploy data stores
    launcher.download_and_deploy(
        repo_owner="myorg",
        repo_name="my-solution",
        workspace_folder="workspace",
        item_type_stages=[
            ["Lakehouse", "KQLDatabase"],
        ],
    )

    # Validate Stage 1
    print("\n🔍 Validating Stage 1...")
    results = launcher.validate_deployment(test_lakehouses=True, test_lakehouses_list=["RawData", "ProcessedData"])

    if not results["all_accessible"]:
        raise Exception("Stage 1 validation failed. Stopping deployment.")

    print("✅ Stage 1 validated successfully")

    # Stage 2: Deploy compute and analytics
    launcher.download_and_deploy(
        repo_owner="myorg",
        repo_name="my-solution",
        workspace_folder="workspace",
        item_type_stages=[
            ["Notebook", "SemanticModel", "Report"],
        ],
    )

    # Validate Stage 2
    print("\n🔍 Validating Stage 2...")
    results = launcher.validate_deployment(test_notebooks=True)

    if not results["all_accessible"]:
        raise Exception("Stage 2 validation failed.")

    print("✅ All stages deployed and validated successfully")


# ============================================================================
# Example 7: Staging Pattern for Event-Driven Architecture
# ============================================================================


def example_event_driven_staging():
    """
    Staging pattern optimized for event-driven architectures.

    Deploy in order: data stores, event ingestion, event processing, analytics.
    """

    launcher = FabricLauncher(notebookutils, environment="PROD")

    launcher.download_and_deploy(
        repo_owner="myorg",
        repo_name="event-driven-solution",
        workspace_folder="workspace",
        item_type_stages=[
            ["Lakehouse", "KQLDatabase"],  # Stage 1: Storage layer
            ["Eventhouse"],  # Stage 2: Real-time analytics storage
            ["Eventstream"],  # Stage 3: Event ingestion streams
            ["Notebook"],  # Stage 4: Event processing logic
            ["KQLDashboard", "Report"],  # Stage 5: Visualization
        ],
    )

    print("✅ Event-driven solution deployed in optimized stages")


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    print("Staged Deployment Examples")
    print("=" * 60)

    # Uncomment the example you want to run:

    # example_basic_staged_deployment()
    # example_two_stage_deployment()
    # example_complex_staged_deployment()
    # example_staged_with_data()
    # example_environment_based_staging()
    # example_staged_with_validation()
    # example_event_driven_staging()
