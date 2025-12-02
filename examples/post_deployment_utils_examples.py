"""
Example: Using Post-Deployment Utility Functions

This example demonstrates how to use the post-deployment utility functions for:
- Custom item deployments with logical ID replacement
- Item organization and folder management
- Eventhouse and KQL Database operations
- Creating shortcuts and accelerated external tables
- SQL endpoint queries and KQL command execution

Prerequisites:
- Microsoft Fabric workspace with appropriate permissions
- For Eventhouse/SQL examples: Eventhouse with KQL Database and Lakehouse with tables
- sempy.fabric package installed (available in Fabric notebooks)
"""

import sempy.fabric as fabric

from fabric_launcher import (
    create_accelerated_shortcut_in_kql_db,
    create_or_update_fabric_item,
    create_shortcut,
    exec_kql_command,
    exec_sql_query,
    get_folder_id_by_name,
    get_kusto_query_uri,
    get_sql_endpoint,
    move_item_to_folder,
    scan_logical_ids,
)

# Note: notebookutils is only available in Fabric notebooks
try:
    import notebookutils
except ImportError:
    print("⚠️ notebookutils not available - some functions require Fabric notebook environment")
    notebookutils = None


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


def eventhouse_sql_examples():
    """Examples: Eventhouse, KQL Database, and SQL Operations."""

    # Initialize Fabric client
    client = fabric.FabricRestClient()
    workspace_id = fabric.resolve_workspace_id()

    # Define your resources (adjust these to match your environment)
    eventhouse_name = "PowerUtilitiesEH"
    kql_db_name = "PowerUtilitiesEH"
    source_lakehouse_name = "ReferenceDataLH"

    print("\n" + "=" * 60)
    print("Eventhouse and SQL Operations Examples")
    print("=" * 60)

    # Example 1: Get Kusto Query URI
    print("\n--- Example 1: Get Kusto Query URI ---")
    try:
        kusto_uri = get_kusto_query_uri(workspace_id, eventhouse_name, client)
        print(f"✅ Kusto Query URI: {kusto_uri}")
    except Exception as e:
        print(f"❌ Error: {e}")
        kusto_uri = None

    # Example 2: Execute KQL Management Commands
    print("\n--- Example 2: Execute KQL Management Commands ---")
    if not notebookutils:
        print("⚠️ Skipping - requires notebookutils (Fabric notebook environment)")
    elif kusto_uri:
        try:
            # Show tables
            kql_command = ".show tables"
            print(f"Executing: {kql_command}")
            result = exec_kql_command(kusto_uri, kql_db_name, kql_command, notebookutils)
            if result:
                print("✅ Command executed successfully")
        except Exception as e:
            print(f"❌ Error: {e}")

    # Example 3: Create Shortcut
    print("\n--- Example 3: Create OneLake Shortcut ---")
    if not notebookutils:
        print("⚠️ Skipping - requires notebookutils (Fabric notebook environment)")
    else:
        try:
            source_lakehouse_id = fabric.resolve_item_id(source_lakehouse_name, "Lakehouse")
            result = create_shortcut(
                target_workspace_id=workspace_id,
                target_item_name=kql_db_name,
                target_item_type="KQLDatabase",
                target_path="Shortcut",
                target_shortcut_name="SourceData",
                source_workspace_id=workspace_id,
                source_item_id=source_lakehouse_id,
                source_path="Tables/substations",
                client=client,
                notebookutils=notebookutils,
            )
            if result:
                print("✅ Shortcut created successfully")
        except Exception as e:
            print(f"❌ Error: {e}")

    # Example 4: Create Accelerated Shortcuts
    print("\n--- Example 4: Create Accelerated Shortcuts in KQL Database ---")
    if not notebookutils:
        print("⚠️ Skipping - requires notebookutils (Fabric notebook environment)")
    else:
        try:
            tables = ["substations", "feeders"]

            for table in tables:
                print(f"\nProcessing table: {table}")
                success = create_accelerated_shortcut_in_kql_db(
                    target_workspace_id=workspace_id,
                    target_kql_db_name=kql_db_name,
                    target_shortcut_name=table.capitalize(),
                    source_workspace_id=workspace_id,
                    source_path=f"Tables/{table}",
                    target_eventhouse_name=eventhouse_name,
                    source_lakehouse_name=source_lakehouse_name,
                    client=client,
                    notebookutils=notebookutils,
                )
                print(f"{'✅' if success else '⚠️'} Table '{table}'")
        except Exception as e:
            print(f"❌ Error: {e}")

    # Example 5: Get SQL Endpoint
    print("\n--- Example 5: Get SQL Endpoint ---")
    try:
        sql_endpoint = get_sql_endpoint(workspace_id, source_lakehouse_name, "Lakehouse", client)
        if sql_endpoint:
            print(f"✅ SQL Endpoint: {sql_endpoint}")
        else:
            print("⚠️ SQL endpoint not found")
    except Exception as e:
        print(f"❌ Error: {e}")
        sql_endpoint = None

    # Example 6: Execute SQL Queries
    print("\n--- Example 6: Execute SQL Queries ---")
    if not notebookutils:
        print("⚠️ Skipping - requires notebookutils (Fabric notebook environment)")
    elif sql_endpoint:
        try:
            sql_query = "SELECT COUNT(*) as total_meters FROM meters"
            print(f"Executing: {sql_query}")
            results = exec_sql_query(sql_endpoint, source_lakehouse_name, sql_query, notebookutils)
            if results:
                print(f"✅ Results: {results}")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("Eventhouse/SQL Examples Completed")
    print("=" * 60)


if __name__ == "__main__":
    # Run the main example
    main()

    # Uncomment to run other examples:
    # batch_deployment_example()
    # folder_organization_example()
    # eventhouse_sql_examples()
