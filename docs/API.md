# API Reference

Complete API reference for fabric-launcher.

## FabricLauncher

Main class for deploying Microsoft Fabric solutions from GitHub repositories.

### Constructor

```python
FabricLauncher(
    notebookutils,
    workspace_id: Optional[str] = None,
    environment: str = "DEV",
    debug: bool = False,
    allow_non_empty_workspace: bool = False,
    fix_zero_logical_ids: bool = True,
    config_file: Optional[str] = None,
    config_repo_owner: Optional[str] = None,
    config_repo_name: Optional[str] = None,
    config_file_path: Optional[str] = None
)
```

**Parameters:**
- `notebookutils`: Fabric notebook utilities object
- `workspace_id`: Target workspace ID (auto-detected if not provided)
- `environment`: Environment name for configuration (DEV, TEST, PROD)
- `debug`: Enable detailed logging
- `allow_non_empty_workspace`: Allow deployment to non-empty workspaces
- `fix_zero_logical_ids`: Automatically fix zero GUID logical IDs
- `config_file`: Path to local YAML configuration file
- `config_repo_owner`: GitHub owner for remote config file
- `config_repo_name`: GitHub repository for remote config file
- `config_file_path`: Path to config file within GitHub repository

### Methods

#### download_and_deploy()

Download repository and deploy artifacts in one operation.

```python
download_and_deploy(
    repo_owner: str,
    repo_name: str,
    workspace_folder: str = "workspace",
    branch: str = "main",
    item_types: Optional[List[str]] = None,
    item_type_stages: Optional[List[List[str]]] = None,
    data_folders: Optional[Dict[str, str]] = None,
    lakehouse_name: Optional[str] = None,
    validate_after_deployment: bool = False,
    generate_report: bool = False
) -> dict
```

**Parameters:**
- `repo_owner`: GitHub repository owner
- `repo_name`: GitHub repository name
- `workspace_folder`: Folder in repo containing Fabric items
- `branch`: Git branch to deploy from
- `item_types`: List of item types to deploy (None = all)
- `item_type_stages`: List of lists for staged deployment
- `data_folders`: Dict mapping source to target folders in lakehouse
- `lakehouse_name`: Lakehouse name for data uploads
- `validate_after_deployment`: Run post-deployment validation
- `generate_report`: Generate deployment report

**Returns:** Dictionary with deployment results

#### download_repository()

Download and extract GitHub repository.

```python
download_repository(
    repo_owner: str,
    repo_name: str,
    extract_to: str,
    folder_to_extract: Optional[str] = None,
    branch: str = "main"
) -> str
```

**Parameters:**
- `repo_owner`: GitHub repository owner
- `repo_name`: GitHub repository name
- `extract_to`: Target directory for extraction
- `folder_to_extract`: Specific folder to extract from repo
- `branch`: Git branch to download

**Returns:** Path to extracted repository

#### deploy_artifacts()

Deploy Fabric artifacts from local directory.

```python
deploy_artifacts(
    repository_directory: str,
    item_types: Optional[List[str]] = None,
    item_type_stages: Optional[List[List[str]]] = None
) -> dict
```

**Parameters:**
- `repository_directory`: Path to directory containing Fabric items
- `item_types`: List of item types to deploy
- `item_type_stages`: List of lists for staged deployment

**Returns:** Dictionary with deployment results

#### upload_files_to_lakehouse()

Upload files to a Fabric Lakehouse.

```python
upload_files_to_lakehouse(
    lakehouse_name: str,
    source_directory: str,
    target_folder: str,
    file_patterns: Optional[List[str]] = None
) -> None
```

**Parameters:**
- `lakehouse_name`: Name of target lakehouse
- `source_directory`: Source directory containing files
- `target_folder`: Target folder within lakehouse
- `file_patterns`: List of glob patterns for files to upload

#### run_notebook()

Execute a notebook asynchronously.

```python
run_notebook(
    notebook_name: str,
    parameters: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 3600
) -> dict
```

**Parameters:**
- `notebook_name`: Name of notebook to execute
- `parameters`: Dictionary of parameters to pass to notebook
- `timeout_seconds`: Maximum execution time

**Returns:** Dictionary with job_id and status

## Post-Deployment Utilities

Functions for custom post-deployment operations.

### get_folder_id_by_name()

Get folder ID by display name.

```python
get_folder_id_by_name(
    folder_name: str,
    workspace_id: str,
    client
) -> Optional[str]
```

**Parameters:**
- `folder_name`: Display name of folder
- `workspace_id`: Target workspace ID
- `client`: Fabric REST client instance

**Returns:** Folder ID if found, None otherwise

### scan_logical_ids()

Scan repository for logical IDs and map to actual workspace IDs.

```python
scan_logical_ids(
    repository_directory: str,
    workspace_id: str,
    client
) -> dict
```

**Parameters:**
- `repository_directory`: Root directory of extracted repository
- `workspace_id`: Target workspace ID
- `client`: Fabric REST client instance

**Returns:** Dictionary mapping logical IDs to actual IDs

### replace_logical_ids()

Replace logical IDs in item definition with actual IDs.

```python
replace_logical_ids(
    item_definition: dict,
    logical_id_map: dict
) -> dict
```

**Parameters:**
- `item_definition`: Item definition dictionary
- `logical_id_map`: Dictionary mapping logical to actual IDs

**Returns:** Updated item definition

### create_or_update_fabric_item()

Create or update a Fabric item with logical ID replacement.

```python
create_or_update_fabric_item(
    item_name: str,
    item_type: str,
    item_relative_path: str,
    repository_directory: str,
    workspace_id: str,
    client,
    endpoint: str,
    logical_id_map: Optional[dict] = None,
    description: str = ""
) -> str
```

**Parameters:**
- `item_name`: Display name for the item
- `item_type`: Type of Fabric item
- `item_relative_path`: Relative path to item in repository
- `repository_directory`: Root directory of repository
- `workspace_id`: Target workspace ID
- `client`: Fabric REST client instance
- `endpoint`: REST API endpoint name
- `logical_id_map`: Optional logical ID mapping
- `description`: Optional item description

**Returns:** ID of created/updated item

### move_item_to_folder()

Move a Fabric item to a specific folder.

```python
move_item_to_folder(
    item_name: str,
    item_type: str,
    folder_name: str,
    workspace_id: str,
    client
) -> bool
```

**Parameters:**
- `item_name`: Display name of item to move
- `item_type`: Type of Fabric item
- `folder_name`: Display name of destination folder
- `workspace_id`: Target workspace ID
- `client`: Fabric REST client instance

**Returns:** True if successful, False otherwise

## Configuration Manager

### DeploymentConfig

Load and manage deployment configurations from YAML files.

```python
config = DeploymentConfig("deployment.yaml", environment="PROD")
```

**Methods:**
- `get(key, default=None)`: Get configuration value
- `get_github_config()`: Get GitHub-related settings
- `get_deployment_config()`: Get deployment settings
- `get_data_config()`: Get data upload settings
