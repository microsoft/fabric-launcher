"""
Example: Using Post-Deployment Utility Functions

This example demonstrates how to use the post-deployment utility functions
to handle custom item deployments with logical ID replacement.
"""

import sempy.fabric as fabric

from fabric_launcher import create_or_update_fabric_item, get_folder_id_by_name, move_item_to_folder, scan_logical_ids


def main():
    """Main example workflow for post-deployment helpers."""

    # Initialize Fabric client and workspace
    client = fabric.FabricRestClient()
    workspace_id = fabric.get_workspace_id()

    # Configure repository directory (adjust to your environment)
    repository_directory = "/lakehouse/default/Files/src/workspace"

    print("=" * 60)
    print("Post-Deployment Helper Functions Example")
    print("=" * 60)

    # Step 1: Scan logical IDs
    print("\n1. Scanning logical IDs in repository...")
    logical_id_map = scan_logical_ids(
        repository_directory=repository_directory, workspace_id=workspace_id, client=client
    )
    print(f"   Found {len(logical_id_map)} logical ID mappings")

    # Step 2: Create/update a custom item with logical ID replacement
    print("\n2. Creating/updating custom Fabric item...")
    item_id = create_or_update_fabric_item(
        item_name="Custom Integration Notebook",
        item_type="Notebook",
        item_relative_path="Custom/Integration.Notebook",
        repository_directory=repository_directory,
        workspace_id=workspace_id,
        client=client,
        endpoint="notebooks",
        logical_id_map=logical_id_map,
        description="Custom integration with logical ID references",
    )
    print(f"   Item ID: {item_id}")

    # Step 3: Move item to appropriate folder
    print("\n3. Moving item to target folder...")
    success = move_item_to_folder(
        item_name="Custom Integration Notebook",
        item_type="Notebook",
        folder_name="Integration",
        workspace_id=workspace_id,
        client=client,
    )

    if success:
        print("   ✅ Item moved successfully")
    else:
        print("   ⚠️ Failed to move item")

    # Step 4: Lookup folder ID for reference
    print("\n4. Looking up folder ID...")
    folder_id = get_folder_id_by_name(folder_name="Integration", workspace_id=workspace_id, client=client)

    if folder_id:
        print(f"   Folder ID: {folder_id}")
    else:
        print("   Folder not found")

    print("\n" + "=" * 60)
    print("✅ Example completed successfully!")
    print("=" * 60)


def batch_deployment_example():
    """Example: Batch deployment of multiple items."""

    client = fabric.FabricRestClient()
    workspace_id = fabric.get_workspace_id()
    repository_directory = "/lakehouse/default/Files/src/workspace"

    # Scan logical IDs once
    logical_id_map = scan_logical_ids(repository_directory, workspace_id, client)

    # Define items to deploy with their endpoints
    items = [
        {
            "name": "Data Processing",
            "type": "Notebook",
            "path": "Notebooks/DataProcessing.Notebook",
            "endpoint": "notebooks",
            "folder": "Engineering",
        },
        {
            "name": "Analytics Dashboard",
            "type": "Report",
            "path": "Reports/Dashboard.Report",
            "endpoint": "reports",
            "folder": "Analytics",
        },
    ]

    print("Deploying multiple items...")

    for item in items:
        try:
            # Create/update item
            create_or_update_fabric_item(
                item_name=item["name"],
                item_type=item["type"],
                item_relative_path=item["path"],
                repository_directory=repository_directory,
                workspace_id=workspace_id,
                client=client,
                endpoint=item["endpoint"],
                logical_id_map=logical_id_map,
            )

            # Move to folder
            move_item_to_folder(
                item_name=item["name"],
                item_type=item["type"],
                folder_name=item["folder"],
                workspace_id=workspace_id,
                client=client,
            )

            print(f"✅ {item['name']}: Deployed and moved to {item['folder']}")

        except Exception as e:
            print(f"❌ {item['name']}: Failed - {e}")

    print("Batch deployment completed!")


def folder_organization_example():
    """Example: Organize existing items into folders."""

    client = fabric.FabricRestClient()
    workspace_id = fabric.get_workspace_id()

    # Define organization structure
    organization = {
        "Engineering": ["Data Ingestion", "ETL Pipeline"],
        "Analytics": ["Sales Report", "Customer Dashboard"],
        "Operations": ["Monitoring Dashboard"],
    }

    print("Organizing items into folders...")

    for folder_name, item_names in organization.items():
        print(f"\nFolder: {folder_name}")

        for item_name in item_names:
            # Assuming all items are Notebooks (adjust type as needed)
            success = move_item_to_folder(
                item_name=item_name,
                item_type="Notebook",
                folder_name=folder_name,
                workspace_id=workspace_id,
                client=client,
            )

            status = "✅" if success else "❌"
            print(f"  {status} {item_name}")

    print("\nOrganization completed!")


if __name__ == "__main__":
    # Run the main example
    main()

    # Uncomment to run other examples:
    # batch_deployment_example()
    # folder_organization_example()
