# Quick Start Guide

Get started with fabric-launcher in minutes.

## Installation

In a Microsoft Fabric notebook:

```python
%pip install fabric-launcher
notebookutils.session.restartPython()
```

## Basic Usage

### 1. Simple Deployment

Deploy a GitHub repository to your Fabric workspace:

```python
import notebookutils
from fabric_launcher import FabricLauncher

launcher = FabricLauncher(notebookutils)
launcher.download_and_deploy(
    repo_owner="your-org",
    repo_name="your-repo"
)
```

### 2. Deploy Specific Folder

Deploy a specific folder from your repository:

```python
launcher.download_and_deploy(
    repo_owner="your-org",
    repo_name="your-repo",
    workspace_folder="fabric-workspace",  # Folder containing Fabric items
    branch="main"
)
```

### 3. Deploy Specific Item Types

Deploy only certain types of items:

```python
launcher.download_and_deploy(
    repo_owner="your-org",
    repo_name="your-repo",
    item_types=["Lakehouse", "Notebook"]
)
```

### 4. Staged Deployment

Deploy items in stages (dependencies first):

```python
launcher.download_and_deploy(
    repo_owner="your-org",
    repo_name="your-repo",
    item_type_stages=[
        ["Lakehouse"],              # Stage 1: Data storage
        ["Notebook"],               # Stage 2: Processing logic
        ["SemanticModel", "Report"] # Stage 3: Analytics
    ]
)
```

### 5. Upload Data Files

Upload reference data to a lakehouse:

```python
launcher.download_and_deploy(
    repo_owner="your-org",
    repo_name="your-repo",
    data_folders={
        "data/reference": "reference-data",
        "data/lookups": "lookups"
    },
    lakehouse_name="MyLakehouse"
)
```

## Using Configuration Files

### Create a Configuration File

Create `deployment.yaml`:

```yaml
github:
  repo_owner: your-org
  repo_name: your-repo
  branch: main
  workspace_folder: workspace

deployment:
  item_types:
    - Lakehouse
    - Notebook
  validate_after_deployment: true

data:
  lakehouse_name: DataLakehouse
  folder_mappings:
    data: reference-data

environments:
  DEV:
    github:
      branch: develop
  PROD:
    deployment:
      validate_after_deployment: true
```

### Deploy with Configuration

```python
from fabric_launcher import FabricLauncher

# Local configuration file
launcher = FabricLauncher(
    notebookutils,
    config_file="deployment.yaml",
    environment="PROD"
)
launcher.download_and_deploy()

# Or load from GitHub
launcher = FabricLauncher(
    notebookutils,
    config_repo_owner="your-org",
    config_repo_name="your-repo",
    config_file_path="config/deployment.yaml",
    environment="PROD"
)
launcher.download_and_deploy()
```

## Advanced Features

### Separate Download and Deploy

```python
# Download repository
repo_path = launcher.download_repository(
    repo_owner="your-org",
    repo_name="your-repo",
    extract_to="/lakehouse/default/Files/src"
)

# Deploy later
launcher.deploy_artifacts(
    repository_directory=repo_path,
    item_types=["Notebook"]
)
```

### Post-Deployment Actions

```python
from fabric_launcher import FabricLauncher

launcher = FabricLauncher(notebookutils)

# Deploy with validation
launcher.download_and_deploy(
    repo_owner="your-org",
    repo_name="your-repo",
    validate_after_deployment=True,
    generate_report=True
)

# Run a notebook after deployment
result = launcher.run_notebook(
    notebook_name="Initialize Data",
    parameters={"date": "2024-01-01"}
)
print(f"Job ID: {result['job_id']}")
```

### Enable Logging

Configure logging for detailed output:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

launcher = FabricLauncher(notebookutils, debug=True)
launcher.download_and_deploy(...)
```

## Common Patterns

### Development Workflow

```python
launcher = FabricLauncher(notebookutils, environment="DEV")
launcher.download_and_deploy(
    repo_owner="your-org",
    repo_name="your-repo",
    branch="develop",
    allow_non_empty_workspace=True  # Allow updates
)
```

### Production Deployment

```python
launcher = FabricLauncher(notebookutils, environment="PROD")
launcher.download_and_deploy(
    repo_owner="your-org",
    repo_name="your-repo",
    branch="main",
    validate_after_deployment=True,
    generate_report=True
)
```

## Troubleshooting

### Check Workspace ID

```python
import sempy.fabric as fabric
print(f"Workspace ID: {fabric.get_workspace_id()}")
```

### Reinstall Package

```python
%pip install fabric-launcher --upgrade --force-reinstall
notebookutils.session.restartPython()
```

### View Deployment Report

Access the deployment report after deployment with `generate_report=True`:

```python
launcher.download_and_deploy(
    repo_owner="your-org",
    repo_name="your-repo",
    generate_report=True
)

# Access report
print(launcher.deployment_report.to_markdown())
```

## Next Steps

- See [API Reference](API.md) for complete documentation
- Check [examples/](../examples/) for more usage patterns
- Review [CONTRIBUTING.md](../CONTRIBUTING.md) to contribute
