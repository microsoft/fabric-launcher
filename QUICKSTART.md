# fabric-launcher Quick Reference

A wrapper around [fabric-cicd](https://microsoft.github.io/fabric-cicd/0.1.3/) for simplified Fabric deployments.

For parameterization and value replacement, see the [fabric-cicd documentation](https://microsoft.github.io/fabric-cicd/0.1.3/).

## Installation

```python
%pip install fabric-launcher --quiet
%pip install --upgrade azure-core azure-identity --quiet
notebookutils.session.restartPython()
```

## Basic Usage

```python
import notebookutils
from fabric_launcher import FabricLauncher

# Initialize
launcher = FabricLauncher(notebookutils)

# Deploy solution with data folders
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-solution",
    workspace_folder="workspace",
    data_folders={"data": "reference-data"},
    lakehouse_name="DataLH"
)
```

## Common Operations

### Download from GitHub

```python
launcher.download_repository(
    repo_owner="myorg",
    repo_name="my-solution",
    extract_to=".lakehouse/default/Files/src",
    folder_to_extract="workspace",
    branch="main"
)
```

### Deploy Artifacts

```python
# All items (staged)
launcher.deploy_artifacts(
    repository_directory="./workspace"
)

# Specific item types
launcher.deploy_artifacts(
    repository_directory="./workspace",
    item_types=["Lakehouse", "Notebook"]
)
```

### Upload Files to Lakehouse

```python
# From local directory
launcher.upload_files_to_lakehouse(
    lakehouse_name="MyLakehouse",
    source_directory="./data",
    target_folder="raw",
    file_patterns=["*.json", "*.csv"]
)

# Copy data folders from repository to Lakehouse
launcher.copy_data_folders_to_lakehouse(
    lakehouse_name="MyLakehouse",
    repository_base_path=".lakehouse/default/Files/src",
    folder_mappings={
        "data": "reference-data",
        "samples": "sample-data"
    },
    file_patterns=["*.json", "*.csv"]
)
```

### Execute Notebooks

```python
# Asynchronous
# Use for post-deployment tasks, custom item types, or configuration
result = launcher.run_notebook(
    notebook_name="ProcessData",
    parameters={"date": "2024-01-01"}
)
print(f"Job ID: {result['job_id']}")

# Synchronous (wait for completion)
result = launcher.run_notebook_sync(
    notebook_path="ProcessData",
    parameters={"date": "2024-01-01"}
)
```

## Configuration Options

```python
FabricLauncher(
    notebookutils,
    workspace_id=None,      # Auto-detected
    environment="DEV",      # DEV, TEST, PROD
    api_root_url="https://api.fabric.microsoft.com",
    debug=False,           # Enable detailed logging
    allow_non_empty_workspace=False  # Safety check: only deploy to empty workspaces
)
```

## Supported Item Types

Supports **all fabric-cicd item types**, including:

**Data Stores:** Lakehouse, KQLDatabase, Eventhouse

**Compute:** Notebook, Eventstream

**Analytics:** SemanticModel, Report, KQLDashboard

**Automation:** Reflex, DataAgent

**And more** - See [fabric-cicd docs](https://microsoft.github.io/fabric-cicd/0.1.3/) for complete list.

> **Note**: For unsupported item types, use post-deployment notebooks with custom code.

## Error Handling

```python
try:
    launcher.download_and_deploy(...)
except Exception as e:
    print(f"Deployment failed: {e}")
    # Handle error
```

## Advanced Usage

### Staged Deployment

```python
from fabric_launcher import FabricDeployer

deployer = FabricDeployer(
    workspace_id=workspace_id,
    repository_directory="./workspace",
    notebookutils=notebookutils
)

# Stage 1: Data stores
deployer.deploy_data_stores()

# Stage 2: Compute and analytics
deployer.deploy_compute_and_analytics()
```

### Check Notebook Status

```python
status = launcher.get_notebook_job_status(
    notebook_id="abc-123",
    job_id="job-456"
)
print(status)
```

### Cancel Notebook Job

```python
success = launcher.cancel_notebook_job(
    notebook_id="abc-123",
    job_id="job-456"
)
```

## Troubleshooting

### Authentication Issues

```python
import sempy.fabric as fabric
print(f"Workspace ID: {fabric.get_workspace_id()}")
```

### Enable Debug Mode

```python
launcher = FabricLauncher(notebookutils, debug=True)
```

### Reinstall Package

```python
%pip install fabric-launcher --upgrade --force-reinstall
notebookutils.session.restartPython()
```

## Complete Example

```python
import notebookutils
from fabric_launcher import FabricLauncher

# Configuration
REPO_OWNER = "myorg"
REPO_NAME = "retail-solution"
LAKEHOUSE = "DataLH"

# Initialize
launcher = FabricLauncher(notebookutils, environment="PROD")

# Deploy solution
launcher.download_and_deploy(
    repo_owner=REPO_OWNER,
    repo_name=REPO_NAME,
    folder_to_extract="workspace"
)

# Copy data folders to Lakehouse
launcher.copy_data_folders_to_lakehouse(
    lakehouse_name=LAKEHOUSE,
    repository_base_path=".lakehouse/default/Files/src",
    folder_mappings={"data": "reference-data"},
    file_patterns=["*.json", "*.csv"]
)

# Run initialization
result = launcher.run_notebook(
    notebook_name="Initialize-Data",
    parameters={"environment": "PROD"}
)

print(f"✅ Deployment complete! Job ID: {result['job_id']}")
```
