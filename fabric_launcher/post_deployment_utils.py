"""
Post-deployment utility functions for Microsoft Fabric items.

This module provides utility functions for common post-deployment tasks including:
- Folder lookups
- Item definition retrieval
- Logical ID scanning and replacement
- Generic item creation and updates
- Item movement between folders
"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def get_folder_id_by_name(folder_name: str, workspace_id: str, client) -> Optional[str]:
    """
    Get folder ID by display name.

    Args:
        folder_name: Display name of the folder to find
        workspace_id: Target workspace ID
        client: Fabric REST client instance (e.g., fabric.FabricRestClient())

    Returns:
        Folder ID if found, None otherwise

    Example:
        >>> from sempy import fabric
        >>> client = fabric.FabricRestClient()
        >>> workspace_id = fabric.get_workspace_id()
        >>> folder_id = get_folder_id_by_name("My Folder", workspace_id, client)
    """
    try:
        url = f"v1/workspaces/{workspace_id}/folders"
        response = client.get(url)

        if response.status_code == 200:
            folders = response.json().get("value", [])
            for folder in folders:
                if folder["displayName"] == folder_name:
                    return folder["id"]

        return None

    except Exception as e:
        logger.error(f"Error retrieving folder: {e}")
        return None


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
