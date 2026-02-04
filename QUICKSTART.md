# fabric-launcher Quick Reference

Quick syntax reference for [fabric-launcher](https://github.com/microsoft/fabric-launcher). For parameterization details, see [fabric-cicd docs](https://microsoft.github.io/fabric-cicd/0.1.3/).

## Installation

```python
%pip install fabric-launcher
notebookutils.session.restartPython()
```

## Basic Pattern

```python
import notebookutils
from fabric_launcher import FabricLauncher

launcher = FabricLauncher(notebookutils)
launcher.download_and_deploy(repo_owner="org", repo_name="repo")
```

## Common Methods

### download_and_deploy()
All-in-one download and deployment.

```python
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-solution",
    workspace_folder="workspace",          # Folder containing Fabric items
    branch="main",
    item_types=["Lakehouse", "Notebook"],  # Optional: specific types
    item_type_stages=[...],                # Optional: staged deployment
    data_folders={"data": "ref-data"},     # Optional: copy to Lakehouse
    lakehouse_name="DataLH",               # Required if data_folders used
    validate_after_deployment=True,        # Optional: validate items
    generate_report=True,                  # Optional: create report
    deployment_retries=2                   # Optional: retries per stage on failure
)
```

### download_repository()
Download repository without deploying.

```python
launcher.download_repository(
    repo_owner="myorg",
    repo_name="my-solution",
    extract_to=".lakehouse/default/Files/src",
    folder_to_extract="workspace",  # Optional: specific folder
    branch="main"
)
```

### deploy_artifacts()
Deploy from local directory.

```python
launcher.deploy_artifacts(
    repository_directory="./workspace",
    item_types=["Lakehouse", "Notebook"],  # Optional: filter types
    deployment_retries=2                   # Optional: retries on failure
)
```

### upload_files_to_lakehouse()
Upload files to Lakehouse.

```python
launcher.upload_files_to_lakehouse(
    lakehouse_name="MyLakehouse",
    source_directory="./data",
    target_folder="raw",
    file_patterns=["*.json", "*.csv"]
)
```

### run_notebook()
Execute notebook asynchronously.

```python
result = launcher.run_notebook(
    notebook_name="ProcessData",
    parameters={"date": "2024-01-01"},
    timeout_seconds=3600
)
print(f"Job ID: {result['job_id']}")
```

## Staged Deployment

```python
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-solution",
    item_type_stages=[
        ["Lakehouse", "KQLDatabase"],  # Stage 1
        ["Notebook"],                   # Stage 2
        ["SemanticModel", "Report"]    # Stage 3
    ]
)
```

## Configuration Options

```python
launcher = FabricLauncher(
    notebookutils,
    workspace_id=None,                    # Auto-detected
    environment="DEV",                    # DEV, TEST, PROD
    debug=False,                          # Detailed logging
    allow_non_empty_workspace=False,      # Safety check
    fix_zero_logical_ids=True,            # Fix GUID issues
    config_file="config.yaml"             # Local config
)
```

## Configuration File

```python
# Load from GitHub (recommended)
launcher = FabricLauncher(
    notebookutils,
    config_repo_owner="myorg",
    config_repo_name="my-solution",
    config_file_path="config/deployment.yaml",
    environment="PROD"
)
```

**Example config file:**
```yaml
github:
  repo_owner: myorg
  repo_name: my-solution
  branch: main
  workspace_folder: workspace

deployment:
  validate_after_deployment: true
  deployment_retries: 2  # Retries per stage on transient errors

data:
  lakehouse_name: DataLH
  folder_mappings:
    data: reference-data

environments:
  PROD:
    deployment:
      deployment_retries: 3
```

## Item Types

All [fabric-cicd](https://microsoft.github.io/fabric-cicd/0.1.3/) item types supported:

| Category | Types |
|----------|-------|
| **Data** | Lakehouse, KQLDatabase, Eventhouse |
| **Compute** | Notebook, Eventstream |
| **Analytics** | SemanticModel, Report, KQLDashboard |
| **Other** | Reflex, DataAgent, and more |

## Error Handling

```python
try:
    launcher.download_and_deploy(...)
except Exception as e:
    print(f"Deployment failed: {e}")
```

## Troubleshooting

**Check workspace ID:**
```python
import sempy.fabric as fabric
print(fabric.get_workspace_id())
```

**Enable debug mode:**
```python
launcher = FabricLauncher(notebookutils, debug=True)
```

**Reinstall package:**
```python
%pip install fabric-launcher --upgrade --force-reinstall
notebookutils.session.restartPython()
```

## Complete Examples

See `examples/` directory:
- `basic_deployment_examples.py` - Basic workflow
- `advanced_deployment_examples.py` - Advanced features
- `staged_deployment_examples.py` - Multi-stage deployment patterns
- `post_deployment_utils_examples.py` - Post-deployment utilities
