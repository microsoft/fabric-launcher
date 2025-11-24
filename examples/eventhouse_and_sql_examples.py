"""
Advanced Examples: Eventhouse, KQL Database, and SQL Operations

This example demonstrates the use of post-deployment utility functions for:
- Eventhouse and KQL Database operations
- Creating shortcuts and accelerated external tables
- SQL endpoint queries
- KQL command execution

Prerequisites:
- Microsoft Fabric workspace with appropriate permissions
- Eventhouse with KQL Database
- Lakehouse with tables to create shortcuts from
- sempy.fabric package installed
"""

import sempy.fabric as fabric

from fabric_launcher.post_deployment_utils import (
    create_accelerated_shortcut_in_kql_db,
    create_shortcut,
    exec_kql_command,
    exec_sql_query,
    get_kusto_query_uri,
    get_sql_endpoint,
)

# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════

# Initialize Fabric client
client = fabric.FabricRestClient()
workspace_id = fabric.resolve_workspace_id()

# Define your resources (adjust these to match your environment)
EVENTHOUSE_NAME = "PowerUtilitiesEH"
KQL_DB_NAME = "PowerUtilitiesEH"
SOURCE_LAKEHOUSE_NAME = "ReferenceDataLH"
SOURCE_LAKEHOUSE_ID = fabric.resolve_item_id(SOURCE_LAKEHOUSE_NAME, "Lakehouse")

# Note: notebookutils is only available in Fabric notebooks
# For local development/testing, you'll need to provide authentication differently
try:
    import notebookutils
except ImportError:
    print("⚠️ notebookutils not available - some functions require Fabric notebook environment")
    notebookutils = None


# ═══════════════════════════════════════════════════════════════════
# Example 1: Get Kusto Query URI
# ═══════════════════════════════════════════════════════════════════


def example_get_kusto_uri():
    """Example: Retrieve Kusto query service URI for an Eventhouse."""
    print("\n" + "=" * 60)
    print("Example 1: Get Kusto Query URI")
    print("=" * 60)

    try:
        kusto_uri = get_kusto_query_uri(workspace_id, EVENTHOUSE_NAME, client)
        print(f"✅ Kusto Query URI: {kusto_uri}")
        return kusto_uri
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
# Example 2: Execute KQL Management Command
# ═══════════════════════════════════════════════════════════════════


def example_exec_kql_command(kusto_uri: str):
    """Example: Execute KQL management commands."""
    print("\n" + "=" * 60)
    print("Example 2: Execute KQL Management Commands")
    print("=" * 60)

    if not notebookutils:
        print("⚠️ Skipping - requires notebookutils (Fabric notebook environment)")
        return

    try:
        # Example 1: Show database schema
        kql_command = ".show database schema"
        print(f"\nExecuting: {kql_command}")
        result = exec_kql_command(kusto_uri, KQL_DB_NAME, kql_command, notebookutils)

        if result:
            print("✅ Command executed successfully")
            print(f"Response: {result}")

        # Example 2: Show tables
        kql_command = ".show tables"
        print(f"\nExecuting: {kql_command}")
        result = exec_kql_command(kusto_uri, KQL_DB_NAME, kql_command, notebookutils)

        if result:
            print("✅ Command executed successfully")

        # Example 3: Create external table (if shortcut exists)
        table_name = "ExampleTable"
        kql_command = (
            f".create-or-alter external table {table_name} "
            f"kind=delta (h@'abfss://workspace@onelake.dfs.fabric.microsoft.com/path/to/data;impersonate')"
        )
        print("\nExample command for creating external table:")
        print(kql_command)

    except Exception as e:
        print(f"❌ Error: {e}")


# ═══════════════════════════════════════════════════════════════════
# Example 3: Create Shortcut in Lakehouse or KQL Database
# ═══════════════════════════════════════════════════════════════════


def example_create_shortcut():
    """Example: Create an internal OneLake shortcut."""
    print("\n" + "=" * 60)
    print("Example 3: Create Shortcut")
    print("=" * 60)

    if not notebookutils:
        print("⚠️ Skipping - requires notebookutils (Fabric notebook environment)")
        return

    try:
        # Create shortcut in KQL Database pointing to Lakehouse table
        result = create_shortcut(
            target_workspace_id=workspace_id,
            target_item_name=KQL_DB_NAME,
            target_item_type="KQLDatabase",
            target_path="Shortcut",  # Fixed path for KQL Database
            target_shortcut_name="MeterData",
            source_workspace_id=workspace_id,
            source_item_id=SOURCE_LAKEHOUSE_ID,
            source_path="Tables/meters",
            client=client,
            notebookutils=notebookutils,
        )

        if result:
            print("✅ Shortcut created successfully")
            print(f"Response: {result}")
        else:
            print("⚠️ Shortcut creation returned no result (may already exist)")

    except Exception as e:
        print(f"❌ Error: {e}")


# ═══════════════════════════════════════════════════════════════════
# Example 4: Create Accelerated Shortcut in KQL Database
# ═══════════════════════════════════════════════════════════════════


def example_create_accelerated_shortcut():
    """Example: Create shortcut with accelerated external table."""
    print("\n" + "=" * 60)
    print("Example 4: Create Accelerated Shortcut in KQL Database")
    print("=" * 60)

    if not notebookutils:
        print("⚠️ Skipping - requires notebookutils (Fabric notebook environment)")
        return

    try:
        # List of tables to create shortcuts for
        tables = ["substations", "feeders", "transformers", "meters"]

        for table in tables:
            print(f"\nProcessing table: {table}")

            success = create_accelerated_shortcut_in_kql_db(
                target_workspace_id=workspace_id,
                target_kql_db_name=KQL_DB_NAME,
                target_shortcut_name=table.capitalize(),
                source_workspace_id=workspace_id,
                source_item_id=SOURCE_LAKEHOUSE_ID,
                source_path=f"Tables/{table}",
                target_eventhouse_name=EVENTHOUSE_NAME,
                source_lakehouse_name=SOURCE_LAKEHOUSE_NAME,
                client=client,
                notebookutils=notebookutils,
            )

            if success:
                print(f"✅ Accelerated shortcut '{table}' created successfully")
            else:
                print(f"⚠️ Failed to create accelerated shortcut '{table}'")

    except Exception as e:
        print(f"❌ Error: {e}")


# ═══════════════════════════════════════════════════════════════════
# Example 5: Get SQL Endpoint
# ═══════════════════════════════════════════════════════════════════


def example_get_sql_endpoint():
    """Example: Retrieve SQL endpoint connection string."""
    print("\n" + "=" * 60)
    print("Example 5: Get SQL Endpoint")
    print("=" * 60)

    try:
        # Get SQL endpoint for Lakehouse
        sql_endpoint = get_sql_endpoint(workspace_id, SOURCE_LAKEHOUSE_NAME, "Lakehouse", client)

        if sql_endpoint:
            print(f"✅ SQL Endpoint: {sql_endpoint}")
            return sql_endpoint
        print("⚠️ SQL endpoint not found")
        return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
# Example 6: Execute SQL Query
# ═══════════════════════════════════════════════════════════════════


def example_exec_sql_query(sql_endpoint: str):
    """Example: Execute SQL queries against SQL endpoint."""
    print("\n" + "=" * 60)
    print("Example 6: Execute SQL Query")
    print("=" * 60)

    if not notebookutils:
        print("⚠️ Skipping - requires notebookutils (Fabric notebook environment)")
        return

    try:
        # Example 1: Count records
        sql_query = "SELECT COUNT(*) as total_meters FROM meters"
        print(f"\nExecuting: {sql_query}")

        results = exec_sql_query(sql_endpoint, SOURCE_LAKEHOUSE_NAME, sql_query, notebookutils)

        if results:
            print("✅ Query executed successfully")
            print(f"Results: {results}")

        # Example 2: Get meter types distribution
        sql_query = """
        SELECT
            meter_type,
            COUNT(*) as count,
            AVG(max_amps) as avg_max_amps
        FROM meters
        GROUP BY meter_type
        ORDER BY count DESC
        """
        print("\nExecuting aggregation query...")

        results = exec_sql_query(sql_endpoint, SOURCE_LAKEHOUSE_NAME, sql_query, notebookutils, timeout=120)

        if results:
            print("✅ Query executed successfully")
            print("\nResults:")
            for row in results:
                print(f"  {row}")

        # Example 3: Join query across tables
        sql_query = """
        SELECT TOP 10
            m.meter_id,
            m.meter_type,
            t.transformer_id,
            t.kva_rating,
            f.feeder_name
        FROM meters m
        JOIN transformers t ON m.transformer_id = t.transformer_id
        JOIN feeders f ON t.feeder_id = f.feeder_id
        WHERE m.meter_type = 'residential'
        """
        print("\nExecuting join query...")

        results = exec_sql_query(sql_endpoint, SOURCE_LAKEHOUSE_NAME, sql_query, notebookutils)

        if results:
            print("✅ Query executed successfully")
            print(f"Retrieved {len(results)} rows")

    except Exception as e:
        print(f"❌ Error: {e}")


# ═══════════════════════════════════════════════════════════════════
# Main Execution
# ═══════════════════════════════════════════════════════════════════


def main():
    """Run all examples."""
    print("=" * 60)
    print("Eventhouse and SQL Operations Examples")
    print("=" * 60)

    # Example 1: Get Kusto URI
    kusto_uri = example_get_kusto_uri()

    # Example 2: Execute KQL commands (requires notebookutils)
    if kusto_uri:
        example_exec_kql_command(kusto_uri)

    # Example 3: Create shortcut (requires notebookutils)
    example_create_shortcut()

    # Example 4: Create accelerated shortcuts (requires notebookutils)
    example_create_accelerated_shortcut()

    # Example 5: Get SQL endpoint
    sql_endpoint = example_get_sql_endpoint()

    # Example 6: Execute SQL queries (requires notebookutils)
    if sql_endpoint:
        example_exec_sql_query(sql_endpoint)

    print("\n" + "=" * 60)
    print("Examples completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
