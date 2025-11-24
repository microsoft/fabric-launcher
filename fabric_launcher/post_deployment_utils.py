"""
Post-deployment utility functions for Microsoft Fabric items.

This module provides utility functions for common post-deployment tasks including:
- Folder lookups
- Item definition retrieval
- Logical ID scanning and replacement
- Generic item creation and updates
- Item movement between folders
- Eventhouse and KQL Database operations
- SQL endpoint operations
- Shortcut management
"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


def get_folder_id_by_name(folder_name: str, workspace_id: str, client) -> str:
    """
    Get folder ID by display name.

    Args:
        folder_name: Display name of the folder to find
        workspace_id: Target workspace ID
        client: Fabric REST client instance (e.g., fabric.FabricRestClient())

    Returns:
        Folder ID

    Raises:
        ValueError: If folder is not found
        RuntimeError: If API call fails

    Example:
        >>> from sempy import fabric
        >>> client = fabric.FabricRestClient()
        >>> workspace_id = fabric.get_workspace_id()
        >>> folder_id = get_folder_id_by_name("My Folder", workspace_id, client)
    """
    try:
        url = f"v1/workspaces/{workspace_id}/folders"
        response = client.get(url)

        if response.status_code != 200:
            raise RuntimeError(f"Failed to list folders: HTTP {response.status_code}")

        folders = response.json().get("value", [])
        for folder in folders:
            if folder["displayName"] == folder_name:
                return folder["id"]

        raise ValueError(f"Folder '{folder_name}' not found in workspace")

    except (ValueError, RuntimeError):
        raise
    except Exception as e:
        logger.error(f"Error retrieving folder: {e}")
        raise RuntimeError(f"Error retrieving folder: {e}") from e


def get_item_definition_from_repo(item_relative_path: str, repository_directory: str) -> tuple[dict[str, Any], str]:
    """
    Load item definition files from the extracted repository.

    Args:
        item_relative_path: Relative path to the item within the repository
        repository_directory: Root directory of the extracted repository

    Returns:
        Tuple of (platform_data dict, full item path)

    Example:
        >>> platform_data, item_path = get_item_definition_from_repo(
        ...     "MyFolder/MyNotebook.Notebook",
        ...     "/path/to/extracted/repo"
        ... )
    """
    item_path = Path(repository_directory) / item_relative_path

    # Read .platform file for metadata
    platform_file = item_path / ".platform"

    if not platform_file.exists():
        raise FileNotFoundError(f"Platform file not found: {platform_file}")

    with open(platform_file, encoding="utf-8") as f:
        platform_data = json.load(f)

    return platform_data, item_path


def scan_logical_ids(repository_directory: str, workspace_id: str, client) -> dict[str, str]:
    """
    Scan all .platform files in the repository and map logical IDs to actual workspace IDs.

    Iterates recursively through all .platform files in the downloaded repository,
    extracts logical IDs, and looks up the corresponding deployed item IDs in the
    target workspace.

    Args:
        repository_directory: Root directory of the extracted repository
        workspace_id: Target workspace ID
        client: Fabric REST client instance

    Returns:
        Dictionary mapping original logical IDs to actual workspace item IDs

    Example:
        >>> logical_id_map = scan_logical_ids("/path/to/repo", workspace_id, client)
        >>> print(logical_id_map)
        {'abc-123-def': 'real-guid-456-xyz', ...}
    """
    logical_id_map = {}

    # Find all .platform files recursively
    repo_path = Path(repository_directory)
    platform_files = list(repo_path.rglob(".platform"))

    logger.info(f"Scanning {len(platform_files)} .platform files for logical IDs...")

    for platform_file in platform_files:
        try:
            with open(platform_file, encoding="utf-8") as f:
                platform_data = json.load(f)

            # Extract metadata
            metadata = platform_data.get("metadata", {})
            display_name = metadata.get("displayName")
            item_type = metadata.get("type")

            # Get the logical ID from the config
            config = platform_data.get("config", {})
            logical_id = config.get("logicalId")

            if not all([display_name, item_type, logical_id]):
                continue

            # Look up the actual item ID in the workspace
            try:
                list_items_url = f"v1/workspaces/{workspace_id}/items"
                response = client.get(list_items_url)

                if response.status_code == 200:
                    items = response.json().get("value", [])

                    # Find matching item by name and type
                    for item in items:
                        if item.get("displayName") == display_name and item.get("type") == item_type:
                            actual_id = item.get("id")
                            logical_id_map[logical_id] = actual_id
                            logger.debug(f"Mapped {item_type} '{display_name}': {logical_id} → {actual_id}")
                            break

            except Exception as e:
                logger.warning(f"Could not resolve item '{display_name}': {e}")
                continue

        except Exception as e:
            logger.warning(f"Error processing {platform_file}: {e}")
            continue

    logger.info(f"Logical ID scanning completed ({len(logical_id_map)} mappings)")
    return logical_id_map


def replace_logical_ids(item_definition: dict[str, Any], logical_id_map: dict[str, str]) -> dict[str, Any]:
    """
    Replace logical IDs in an item definition with actual workspace IDs.

    Searches for strings that match any of the original logical IDs and replaces
    them with the corresponding actual workspace IDs.

    Args:
        item_definition: The item definition dictionary (e.g., from get_item_definition_from_repo)
        logical_id_map: Dictionary mapping logical IDs to actual IDs (from scan_logical_ids)

    Returns:
        Updated item definition with replaced logical IDs

    Example:
        >>> platform_data, _ = get_item_definition_from_repo("MyItem.Notebook", repo_dir)
        >>> logical_id_map = scan_logical_ids(repo_dir, workspace_id, client)
        >>> updated_definition = replace_logical_ids(platform_data, logical_id_map)
    """
    # Convert definition to JSON string for replacement
    definition_str = json.dumps(item_definition)

    replacements_made = 0

    # Replace each logical ID with its actual ID
    for logical_id, actual_id in logical_id_map.items():
        if logical_id in definition_str:
            definition_str = definition_str.replace(logical_id, actual_id)
            replacements_made += 1
            logger.debug(f"Replaced logical ID: {logical_id} → {actual_id}")

    # Convert back to dictionary
    updated_definition = json.loads(definition_str)

    if replacements_made > 0:
        logger.info(f"Replaced {replacements_made} logical ID(s) in definition")
    else:
        logger.debug("No logical IDs found in definition")

    return updated_definition


def create_or_update_fabric_item(
    item_name: str,
    item_type: str,
    item_relative_path: str,
    repository_directory: str,
    workspace_id: str,
    client,
    endpoint: str,
    logical_id_map: Optional[dict[str, str]] = None,
    description: str = "",
) -> str:
    """
    Generic function to create and/or update a Fabric item with logical ID replacement.

    This function:
    1. Retrieves the item definition from the repository
    2. Creates the item without a definition (if it doesn't exist)
    3. Replaces logical IDs in the definition (if map provided)
    4. Updates the item with the processed definition

    Args:
        item_name: Display name for the item
        item_type: Type of Fabric item (e.g., "Notebook", "Lakehouse", "Report")
        item_relative_path: Relative path to item in repository (e.g., "Folder/Item.Notebook")
        repository_directory: Root directory of the extracted repository
        workspace_id: Target workspace ID
        client: Fabric REST client instance
        endpoint: REST API endpoint name (e.g., "notebooks", "lakehouses", "semanticModels")
        logical_id_map: Optional dictionary mapping logical IDs to actual IDs
        description: Optional description for the item

    Returns:
        ID of the created or updated item

    Example:
        >>> # Create a notebook with logical ID replacement
        >>> logical_id_map = scan_logical_ids(repo_dir, workspace_id, client)
        >>> item_id = create_or_update_fabric_item(
        ...     item_name="My Notebook",
        ...     item_type="Notebook",
        ...     item_relative_path="Notebooks/MyNotebook.Notebook",
        ...     repository_directory=repo_dir,
        ...     workspace_id=workspace_id,
        ...     client=client,
        ...     endpoint="notebooks",
        ...     logical_id_map=logical_id_map
        ... )
    """
    logger.info(f"Creating/Updating {item_type}: {item_name}")

    try:
        # Step 1: Get item definition from repository
        logger.debug("Loading item definition from repository...")
        platform_data, item_path = get_item_definition_from_repo(item_relative_path, repository_directory)

        # Extract metadata
        metadata = platform_data.get("metadata", {})
        display_name = metadata.get("displayName", item_name)
        item_description = metadata.get("description", description)

        # Step 2: Create the item (without definition)
        logger.info(f"Creating {item_type} item: {display_name}")

        create_url = f"v1/workspaces/{workspace_id}/{endpoint}"

        create_payload = {"displayName": display_name}

        if item_description:
            create_payload["description"] = item_description

        create_response = client.post(create_url, json=create_payload)

        if create_response.status_code in [200, 201]:
            item_data = create_response.json()
            item_id = item_data["id"]
            logger.info(f"{item_type} item created successfully (ID: {item_id})")
        elif create_response.status_code == 409:
            logger.info(f"{item_type} '{display_name}' already exists, retrieving existing item...")

            # Find existing item
            list_url = f"v1/workspaces/{workspace_id}/items"
            list_response = client.get(list_url)

            if list_response.status_code == 200:
                items = list_response.json().get("value", [])
                item_id = None

                for item in items:
                    if item.get("displayName") == display_name and item.get("type") == item_type:
                        item_id = item.get("id")
                        break

                if item_id:
                    logger.info(f"Using existing {item_type} (ID: {item_id})")
                else:
                    raise Exception(f"Could not find existing {item_type} '{display_name}'")
            else:
                raise Exception(f"Failed to list items: {list_response.status_code}")
        else:
            raise Exception(f"Failed to create {item_type}: {create_response.status_code} - {create_response.text}")

        # Step 3: Load and process definition files
        logger.debug("Processing item definition files...")

        # Collect all definition files (excluding .platform)
        definition_parts = []

        for root, _dirs, files in os.walk(item_path):
            # Skip .platform file
            files = [f for f in files if f != ".platform"]

            for file in files:
                file_path = Path(root) / file
                relative_file_path = file_path.relative_to(item_path)

                # Read file content
                with open(file_path, "rb") as f:
                    file_content = f.read()

                # If logical ID map provided, replace IDs in text files
                if logical_id_map and file_path.suffix in (".json", ".py", ".sql", ".kql", ".txt"):
                    try:
                        text_content = file_content.decode("utf-8")

                        # Replace logical IDs
                        for logical_id, actual_id in logical_id_map.items():
                            if logical_id in text_content:
                                text_content = text_content.replace(logical_id, actual_id)
                                logger.debug(f"Replaced logical ID in {relative_file_path}")

                        file_content = text_content.encode("utf-8")
                    except UnicodeDecodeError:
                        # Not a text file, skip replacement
                        pass

                # Encode to base64
                payload_base64 = base64.b64encode(file_content).decode("utf-8")

                definition_parts.append(
                    {
                        "path": str(relative_file_path).replace("\\", "/"),  # Use forward slashes
                        "payload": payload_base64,
                        "payloadType": "InlineBase64",
                    }
                )

        if not definition_parts:
            logger.info("No definition files found, skipping definition update")
            return item_id

        logger.info(f"Uploading {len(definition_parts)} definition file(s)...")

        # Step 4: Update item definition
        update_url = f"v1/workspaces/{workspace_id}/{endpoint}/{item_id}/updateDefinition"

        definition_payload = {"definition": {"parts": definition_parts}}

        update_response = client.post(update_url, json=definition_payload)

        if update_response.status_code in [200, 202]:
            logger.info(f"{item_type} definition updated successfully")
        else:
            logger.warning(f"Definition update returned status {update_response.status_code}")
            logger.debug(f"Response: {update_response.text[:500]}")

        logger.info(f"{item_type} deployment completed: {display_name}")
        return item_id

    except Exception as e:
        logger.error(f"Error creating/updating {item_type}: {e}")
        raise


def move_item_to_folder(item_name: str, item_type: str, folder_name: str, workspace_id: str, client) -> bool:
    """
    Move a specific Fabric item to a specific folder.

    Args:
        item_name: Display name of the item to move
        item_type: Type of Fabric item (e.g., "Notebook", "Lakehouse", "Report")
        folder_name: Display name of the destination folder
        workspace_id: Target workspace ID
        client: Fabric REST client instance

    Returns:
        True if successful, False otherwise

    Example:
        >>> success = move_item_to_folder(
        ...     item_name="My Notebook",
        ...     item_type="Notebook",
        ...     folder_name="Analysis",
        ...     workspace_id=workspace_id,
        ...     client=client
        ... )
    """
    try:
        logger.debug(f"Finding {item_type} '{item_name}'...")

        # Step 1: Find the item ID
        list_url = f"v1/workspaces/{workspace_id}/items"
        list_response = client.get(list_url)

        if list_response.status_code != 200:
            logger.error(f"Failed to list items: {list_response.status_code}")
            return False

        items = list_response.json().get("value", [])
        item_id = None

        for item in items:
            if item.get("displayName") == item_name and item.get("type") == item_type:
                item_id = item.get("id")
                break

        if not item_id:
            logger.error(f"{item_type} '{item_name}' not found in workspace")
            return False

        logger.debug(f"Found {item_type} (ID: {item_id})")

        # Step 2: Get the target folder ID
        logger.debug(f"Finding folder '{folder_name}'...")
        target_folder_id = get_folder_id_by_name(folder_name, workspace_id, client)

        if not target_folder_id:
            logger.error(f"Folder '{folder_name}' not found in workspace")
            return False

        logger.debug(f"Found folder (ID: {target_folder_id})")

        # Step 3: Move the item
        logger.info(f"Moving {item_type} to folder '{folder_name}'...")
        move_url = f"v1/workspaces/{workspace_id}/items/{item_id}/move"
        move_payload = {"targetFolderId": target_folder_id}

        move_response = client.post(move_url, json=move_payload)

        if move_response.status_code == 200:
            logger.info(f"{item_type} '{item_name}' moved to folder '{folder_name}' successfully")
            return True
        logger.error(f"Failed to move item: {move_response.status_code} - {move_response.text}")
        return False

    except Exception as e:
        logger.error(f"Error moving item: {e}")
        return False


def get_kusto_query_uri(workspace_id: str, eventhouse_name: str, client) -> str:
    """
    Retrieve the Kusto query service URI for a given Eventhouse.

    Args:
        workspace_id: Target workspace ID
        eventhouse_name: Display name of the Eventhouse
        client: Fabric REST client instance (e.g., fabric.FabricRestClient())

    Returns:
        Kusto query service URI (e.g., "https://xxxxx.kusto.fabric.microsoft.com")

    Raises:
        ValueError: If the queryServiceUri cannot be retrieved or parsed
        Exception: For other API or network errors

    Example:
        >>> from sempy import fabric
        >>> client = fabric.FabricRestClient()
        >>> workspace_id = fabric.get_workspace_id()
        >>> kusto_uri = get_kusto_query_uri(workspace_id, "MyEventhouse", client)
        >>> print(kusto_uri)
        'https://xxxxx.kusto.fabric.microsoft.com'
    """
    try:
        # Resolve the Eventhouse ID
        logger.debug(f"Resolving Eventhouse '{eventhouse_name}'...")
        list_url = f"v1/workspaces/{workspace_id}/items"
        list_response = client.get(list_url)

        if list_response.status_code != 200:
            raise Exception(f"Failed to list items: {list_response.status_code}")

        items = list_response.json().get("value", [])
        eventhouse_id = None

        for item in items:
            if item.get("displayName") == eventhouse_name and item.get("type") == "Eventhouse":
                eventhouse_id = item.get("id")
                break

        if not eventhouse_id:
            raise ValueError(f"Eventhouse '{eventhouse_name}' not found in workspace")

        logger.debug(f"Found Eventhouse (ID: {eventhouse_id})")

        # Get Eventhouse properties
        url = f"v1/workspaces/{workspace_id}/eventhouses/{eventhouse_id}"
        response = client.get(url)

        if response.status_code != 200:
            raise Exception(f"Failed to get Eventhouse properties: {response.status_code}")

        eventhouse_data = response.json()
        kusto_query_uri = eventhouse_data.get("properties", {}).get("queryServiceUri")

        if not kusto_query_uri:
            raise ValueError("queryServiceUri not found in Eventhouse properties")

        logger.info(f"Retrieved Kusto query URI: {kusto_query_uri}")
        return kusto_query_uri

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Kusto query URI: {e}")
        raise


def exec_kql_command(kusto_query_uri: str, kql_db_name: str, kql_command: str, notebookutils) -> dict:
    """
    Execute a KQL management command against a Kusto database.

    Args:
        kusto_query_uri: Kusto query service URI (from get_kusto_query_uri)
        kql_db_name: Name of the KQL database
        kql_command: KQL management command to execute (e.g., ".create table ...")
        notebookutils: Notebook utilities for authentication (notebookutils.credentials.getToken)

    Returns:
        Response JSON as dictionary

    Raises:
        RuntimeError: If KQL command execution fails
        requests.RequestException: If network error occurs

    Example:
        >>> # Create an external table
        >>> kql_command = ".create-or-alter external table MyTable kind=delta (h@'path/to/data;impersonate')"
        >>> result = exec_kql_command(kusto_uri, "MyDatabase", kql_command, notebookutils)

        >>> # Enable query acceleration
        >>> kql_command = ".alter external table MyTable policy query_acceleration '{\"IsEnabled\": true}'"
        >>> result = exec_kql_command(kusto_uri, "MyDatabase", kql_command, notebookutils)
    """
    try:
        logger.info(f"Executing KQL command on database '{kql_db_name}'")
        logger.debug(f"Command: {kql_command[:100]}...")

        # Get authentication token
        token = notebookutils.credentials.getToken(kusto_query_uri)
        mgmt_url = f"{kusto_query_uri}/v1/rest/mgmt"

        payload = {"csl": kql_command, "db": kql_db_name}

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        response = requests.post(mgmt_url, json=payload, headers=headers, timeout=60)

        logger.debug(f"Response status: {response.status_code}")

        if not response.ok:
            error_msg = f"KQL command failed: HTTP {response.status_code}"
            logger.error(f"{error_msg}: {response.text[:500]}")
            raise RuntimeError(f"{error_msg}: {response.text[:200]}")

        logger.info("KQL command executed successfully")
        return response.json()

    except RuntimeError:
        raise
    except requests.RequestException as e:
        logger.error(f"Network error executing KQL command: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error executing KQL command: {e}")
        raise RuntimeError(f"Unexpected error executing KQL command: {e}") from e


def create_shortcut(
    target_workspace_id: str,
    target_item_name: str,
    target_item_type: str,
    target_path: str,
    target_shortcut_name: str,
    source_workspace_id: str,
    source_item_id: str,
    source_path: str,
    client,
    notebookutils,
) -> dict:
    """
    Create an internal OneLake shortcut in a Fabric item.

    Args:
        target_workspace_id: Workspace ID where the shortcut will be created
        target_item_name: Name of the target item (e.g., Lakehouse or KQL Database name)
        target_item_type: Type of target item (e.g., "Lakehouse", "KQLDatabase")
        target_path: Path within the target item where shortcut will be created (e.g., "Tables", "Files")
        target_shortcut_name: Name for the new shortcut
        source_workspace_id: Workspace ID containing the source item
        source_item_id: ID of the source item
        source_path: Path within the source item to link to (e.g., "Tables/MyTable")
        client: Fabric REST client instance
        notebookutils: Notebook utilities for authentication

    Returns:
        Response JSON dictionary

    Raises:
        ValueError: If target item is not found
        RuntimeError: If shortcut creation fails
        requests.RequestException: If network error occurs

    Example:
        >>> # Create shortcut in a Lakehouse
        >>> result = create_shortcut(
        ...     target_workspace_id=workspace_id,
        ...     target_item_name="MyLakehouse",
        ...     target_item_type="Lakehouse",
        ...     target_path="Tables",
        ...     target_shortcut_name="ExternalData",
        ...     source_workspace_id=source_workspace_id,
        ...     source_item_id=source_lakehouse_id,
        ...     source_path="Tables/SourceTable",
        ...     client=client,
        ...     notebookutils=notebookutils
        ... )
    """
    try:
        logger.info(f"Creating shortcut '{target_shortcut_name}' in {target_item_type} '{target_item_name}'")

        # Resolve target item ID
        logger.debug("Resolving target item ID...")
        list_url = f"v1/workspaces/{target_workspace_id}/items"
        list_response = client.get(list_url)

        if list_response.status_code != 200:
            raise RuntimeError(f"Failed to list items: HTTP {list_response.status_code}")

        items = list_response.json().get("value", [])
        target_item_id = None

        for item in items:
            if item.get("displayName") == target_item_name and item.get("type") == target_item_type:
                target_item_id = item.get("id")
                break

        if not target_item_id:
            raise ValueError(f"{target_item_type} '{target_item_name}' not found in workspace")

        logger.debug(f"Found target item (ID: {target_item_id})")

        # Create shortcut
        base_url = client.default_base_url
        url = f"{base_url}/v1/workspaces/{target_workspace_id}/items/{target_item_id}/shortcuts"

        payload = {
            "path": target_path,
            "name": target_shortcut_name,
            "target": {
                "type": "OneLake",
                "oneLake": {
                    "workspaceId": source_workspace_id,
                    "itemId": source_item_id,
                    "path": source_path,
                },
            },
        }

        token = notebookutils.credentials.getToken("pbi")
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        logger.debug(f"Response status: {response.status_code}")

        if response.ok:
            logger.info(f"Shortcut '{target_shortcut_name}' created successfully")
            try:
                return response.json()
            except ValueError:
                return {"status": "success"}

        error_msg = f"Shortcut creation failed: HTTP {response.status_code}"
        logger.error(f"{error_msg}: {response.text[:500]}")
        raise RuntimeError(f"{error_msg}: {response.text[:200]}")

    except (ValueError, RuntimeError):
        raise
    except requests.RequestException as e:
        logger.error(f"Network error creating shortcut: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating shortcut: {e}")
        raise RuntimeError(f"Unexpected error creating shortcut: {e}") from e


def create_accelerated_shortcut_in_kql_db(
    target_workspace_id: str,
    target_kql_db_name: str,
    target_shortcut_name: str,
    source_workspace_id: str,
    source_path: str,
    target_eventhouse_name: str,
    source_lakehouse_name: str,
    client,
    notebookutils,
) -> bool:
    """
    Create OneLake shortcut and accelerated external table in KQL Database.

    This function:
    1. Creates a OneLake shortcut in the KQL Database pointing to a Lakehouse table
    2. Creates an external table in Kusto using the shortcut
    3. Enables query acceleration on the external table

    Args:
        target_workspace_id: Workspace ID containing the KQL Database
        target_kql_db_name: Name of the KQL Database
        target_shortcut_name: Name for the shortcut and external table
        source_workspace_id: Workspace ID containing the source Lakehouse
        source_path: Path to the table in the Lakehouse (e.g., "Tables/MyTable")
        target_eventhouse_name: Name of the Eventhouse containing the KQL Database
        source_lakehouse_name: Name of the source Lakehouse
        client: Fabric REST client instance
        notebookutils: Notebook utilities for authentication and path resolution

    Returns:
        True if successful, False otherwise

    Example:
        >>> success = create_accelerated_shortcut_in_kql_db(
        ...     target_workspace_id=workspace_id,
        ...     target_kql_db_name="MyKQLDatabase",
        ...     target_shortcut_name="Meters",
        ...     source_workspace_id=workspace_id,
        ...     source_path="Tables/meters",
        ...     target_eventhouse_name="MyEventhouse",
        ...     source_lakehouse_name="ReferenceDataLH",
        ...     client=client,
        ...     notebookutils=notebookutils
        ... )
    """
    try:
        logger.info(f"Creating accelerated shortcut '{target_shortcut_name}' in KQL Database '{target_kql_db_name}'")

        # Step 1: Resolve source Lakehouse ID
        logger.debug(f"Resolving source Lakehouse '{source_lakehouse_name}'...")
        list_url = f"v1/workspaces/{source_workspace_id}/items"
        list_response = client.get(list_url)

        if list_response.status_code != 200:
            logger.error(f"Failed to list items in source workspace: {list_response.status_code}")
            return False

        items = list_response.json().get("value", [])
        source_item_id = None

        for item in items:
            if item.get("displayName") == source_lakehouse_name and item.get("type") == "Lakehouse":
                source_item_id = item.get("id")
                break

        if not source_item_id:
            logger.error(f"Source Lakehouse '{source_lakehouse_name}' not found in workspace")
            return False

        logger.debug(f"Found source Lakehouse (ID: {source_item_id})")

        # Step 2: Create shortcut
        target_path = "Shortcut"  # Fixed value for KQL Database

        shortcut_result = create_shortcut(
            target_workspace_id=target_workspace_id,
            target_item_name=target_kql_db_name,
            target_item_type="KQLDatabase",
            target_path=target_path,
            target_shortcut_name=target_shortcut_name,
            source_workspace_id=source_workspace_id,
            source_item_id=source_item_id,
            source_path=source_path,
            client=client,
            notebookutils=notebookutils,
        )

        if not shortcut_result:
            logger.error("Aborting: Shortcut creation failed")
            return False

        logger.info("Shortcut created successfully")

        # Step 2: Get Kusto query URI
        kusto_query_uri = get_kusto_query_uri(target_workspace_id, target_eventhouse_name, client)

        # Step 3: Construct OneLake path for external table
        logger.debug("Resolving KQL Database item ID...")
        list_url = f"v1/workspaces/{target_workspace_id}/items"
        list_response = client.get(list_url)

        if list_response.status_code != 200:
            logger.error(f"Failed to list items: {list_response.status_code}")
            return False

        items = list_response.json().get("value", [])
        target_kql_db_id = None

        for item in items:
            if item.get("displayName") == target_kql_db_name and item.get("type") == "KQLDatabase":
                target_kql_db_id = item.get("id")
                break

        if not target_kql_db_id:
            logger.error(f"KQL Database '{target_kql_db_name}' not found")
            return False

        # Get Lakehouse tables path to construct base path
        lakehouse_properties = notebookutils.lakehouse.getWithProperties(source_lakehouse_name)
        lakehouse_table_path = lakehouse_properties.properties["oneLakeTablesPath"]
        base_path = "/".join(lakehouse_table_path.rstrip("/").split("/")[:-2])
        kql_db_source_path = f"{base_path}/{target_kql_db_id}/{target_path}/{target_shortcut_name}"

        logger.debug(f"External table path: {kql_db_source_path}")

        # Step 4: Create external table
        logger.info(f"Creating external table '{target_shortcut_name}'...")
        kql_command = (
            f".create-or-alter external table {target_shortcut_name} "
            f"kind=delta (h@'{kql_db_source_path};impersonate')"
        )

        result = exec_kql_command(kusto_query_uri, target_kql_db_name, kql_command, notebookutils)

        if not result:
            logger.error("Failed to create external table")
            return False

        logger.info("External table created successfully")

        # Step 5: Enable query acceleration
        logger.info(f"Enabling query acceleration on '{target_shortcut_name}'...")
        kql_command = (
            f'.alter external table {target_shortcut_name} policy query_acceleration '
            f"""'{{"IsEnabled": true, "Hot": "365.00:00:00", "MaxAge": "01:00:00"}}'"""
        )

        result = exec_kql_command(kusto_query_uri, target_kql_db_name, kql_command, notebookutils)

        if not result:
            logger.warning("Failed to enable query acceleration (table may still be usable)")
            return True  # Consider this a partial success

        logger.info("Query acceleration enabled successfully")
        logger.info(f"Accelerated shortcut '{target_shortcut_name}' created successfully")
        return True

    except Exception as e:
        logger.error(f"Error creating accelerated shortcut: {e}")
        return False


def get_sql_endpoint(workspace_id: str, item_name: str, item_type: str, client) -> str:
    """
    Get the SQL endpoint connection string for a Fabric item.

    Args:
        workspace_id: Target workspace ID
        item_name: Display name of the item (e.g., Lakehouse or Warehouse name)
        item_type: Type of item (e.g., "Lakehouse", "Warehouse", "SQLEndpoint")
        client: Fabric REST client instance

    Returns:
        SQL endpoint connection string

    Raises:
        ValueError: If item is not found or item type is unsupported
        RuntimeError: If API call fails or connection string is not available

    Example:
        >>> from sempy import fabric
        >>> client = fabric.FabricRestClient()
        >>> workspace_id = fabric.get_workspace_id()
        >>> sql_endpoint = get_sql_endpoint(workspace_id, "MyLakehouse", "Lakehouse", client)
        >>> print(sql_endpoint)
        'xxxxx.datawarehouse.fabric.microsoft.com'
    """
    try:
        logger.info(f"Retrieving SQL endpoint for {item_type} '{item_name}'")

        # Find the item
        list_url = f"v1/workspaces/{workspace_id}/items"
        list_response = client.get(list_url)

        if list_response.status_code != 200:
            raise RuntimeError(f"Failed to list items: HTTP {list_response.status_code}")

        items = list_response.json().get("value", [])
        item_id = None

        for item in items:
            if item.get("displayName") == item_name and item.get("type") == item_type:
                item_id = item.get("id")
                break

        if not item_id:
            raise ValueError(f"{item_type} '{item_name}' not found in workspace")

        logger.debug(f"Found {item_type} (ID: {item_id})")

        # Get item properties based on type
        if item_type == "Lakehouse":
            url = f"v1/workspaces/{workspace_id}/lakehouses/{item_id}"
        elif item_type == "Warehouse":
            url = f"v1/workspaces/{workspace_id}/warehouses/{item_id}"
        elif item_type == "SQLEndpoint":
            url = f"v1/workspaces/{workspace_id}/sqlEndpoints/{item_id}"
        else:
            raise ValueError(f"Unsupported item type for SQL endpoint: {item_type}")

        response = client.get(url)

        if response.status_code != 200:
            raise RuntimeError(f"Failed to get {item_type} properties: HTTP {response.status_code}")

        item_data = response.json()

        # SQL endpoint may be in different property locations depending on item type
        sql_endpoint = item_data.get("properties", {}).get("connectionString")

        if not sql_endpoint:
            sql_endpoint = item_data.get("properties", {}).get("sqlEndpointProperties", {}).get("connectionString")

        if not sql_endpoint:
            raise RuntimeError(f"SQL endpoint connection string not found in {item_type} properties")

        logger.info(f"Retrieved SQL endpoint: {sql_endpoint}")
        return sql_endpoint

    except (ValueError, RuntimeError):
        raise
    except Exception as e:
        logger.error(f"Error retrieving SQL endpoint: {e}")
        raise RuntimeError(f"Error retrieving SQL endpoint: {e}") from e


def exec_sql_query(
    sql_endpoint: str, database_name: str, sql_query: str, notebookutils, timeout: int = 60
) -> list:
    """
    Execute a SQL query against a Fabric SQL endpoint.

    Args:
        sql_endpoint: SQL endpoint connection string (from get_sql_endpoint)
        database_name: Name of the database to query
        sql_query: SQL query to execute
        notebookutils: Notebook utilities for authentication
        timeout: Request timeout in seconds (default: 60)

    Returns:
        List of result rows as dictionaries

    Raises:
        RuntimeError: If SQL query execution fails
        requests.RequestException: If network error occurs

    Warning:
        This function executes raw SQL queries without parameterization. Ensure queries
        are properly validated and sanitized before execution, especially if they contain
        user input. Never pass unsanitized user input directly into SQL queries to prevent
        SQL injection attacks.

    Example:
        >>> # Get SQL endpoint
        >>> sql_endpoint = get_sql_endpoint(workspace_id, "MyLakehouse", "Lakehouse", client)
        >>>
        >>> # Execute query
        >>> sql_query = "SELECT TOP 10 * FROM meters WHERE meter_type = 'residential'"
        >>> results = exec_sql_query(sql_endpoint, "MyLakehouse", sql_query, notebookutils)
        >>>
        >>> if results:
        ...     for row in results:
        ...         print(row)
    """
    try:
        logger.info(f"Executing SQL query on database '{database_name}'")
        logger.debug(f"Query: {sql_query[:100]}...")

        # Construct connection string
        connection_string = f"https://{sql_endpoint}"

        # Get authentication token
        token = notebookutils.credentials.getToken(connection_string)

        # Construct API endpoint URL
        api_url = f"{connection_string}/sql/v1/databases/{database_name}/query"

        payload = {"query": sql_query}

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)

        logger.debug(f"Response status: {response.status_code}")

        if not response.ok:
            error_msg = f"SQL query failed: HTTP {response.status_code}"
            logger.error(f"{error_msg}: {response.text[:500]}")
            raise RuntimeError(f"{error_msg}: {response.text[:200]}")

        result_data = response.json()

        # Parse results based on response structure
        # The actual structure may vary - adjust based on your API response format
        rows = result_data.get("rows", [])
        columns = result_data.get("columns", [])

        if columns:
            # Convert to list of dictionaries for easier access
            results = []
            for row in rows:
                row_dict = {}
                for idx, col_name in enumerate(columns):
                    row_dict[col_name] = row[idx] if idx < len(row) else None
                results.append(row_dict)

            logger.info(f"SQL query executed successfully ({len(results)} rows)")
            return results

        logger.info("SQL query executed successfully")
        return rows

    except RuntimeError:
        raise
    except requests.RequestException as e:
        logger.error(f"Network error executing SQL query: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error executing SQL query: {e}")
        raise RuntimeError(f"Unexpected error executing SQL query: {e}") from e
