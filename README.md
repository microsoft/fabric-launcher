# fabric-launcher

A library to automate initial deployment of Microsoft Fabric solutions from GitHub repositories into Fabric workspaces, which is ideal for:
- Solution accelerators
- Demos
- Tutorials
- Samples

The **fabric-launcher** library is a wrapper around the [fabric-cicd](https://github.com/microsoft/fabriccicd) and supports all Fabric item types supported by [fabric-cicd](https://github.com/microsoft/fabriccicd).

## Overview

`fabric-launcher` provides a high-level Python interface for orchestrating end-to-end deployment of Microsoft Fabric workspace solutions. It's designed to be used within Fabric Python notebooks and simplifies:

- 📥 **Downloading source code** from GitHub repositories
- 🚀 **Deploying artifacts** to Fabric workspaces (all item types supported by [fabric-cicd](https://microsoft.github.io/fabric-cicd/0.1.3/))
- 📁 **Uploading files** to Lakehouse Files area
- ▶️ **Triggering notebook execution** for post-deployment tasks and custom configurations

> **Note**: This package wraps [fabric-cicd](https://microsoft.github.io/fabric-cicd/0.1.3/) and supports all Fabric item types that fabric-cicd supports. For the latest compatibility information, parameterization guidance, and value replacement syntax, please refer to the [fabric-cicd documentation](https://microsoft.github.io/fabric-cicd/0.1.3/).

## Features

- **Simple API**: High-level methods that abstract away complexity
- **Fabric-native**: Designed for use in Fabric notebooks with `notebookutils` integration
- **Flexible deployment**: Support for staged deployment (data stores first, then compute) or custom item type selection
- **GitHub integration**: Direct download and extraction from public or private GitHub repositories
- **File management**: Easy upload of reference data or configuration files to Lakehouse
- **Notebook orchestration**: Trigger and monitor Fabric notebook execution for post-deployment tasks and custom configurations
- **Full fabric-cicd compatibility**: Supports all item types and features provided by [fabric-cicd](https://microsoft.github.io/fabric-cicd/0.1.3/)

## Installation

Install from PyPI:

```bash
%pip install fabric-launcher
```

Or install with upgrade for dependencies:

```bash
%pip install fabric-launcher --upgrade
%pip install --upgrade azure-core azure-identity
```

**Note**: After installation, restart the Python kernel:

```python
notebookutils.session.restartPython()
```

## Quick Start

### Recommended: Using Configuration Files from GitHub

The recommended approach is to store your deployment configuration in your GitHub repository alongside your Fabric solution. This provides version control, easy team collaboration, and works seamlessly in Fabric notebooks.

```python
import notebookutils
from fabric_launcher import FabricLauncher

# Initialize launcher with config file from your GitHub repository
launcher = FabricLauncher(
    notebookutils,
    config_repo_owner="myorg",
    config_repo_name="my-fabric-solution",
    config_file_path="config/deployment.yaml",  # Path in your repo
    environment="PROD"
)

# Deploy - all settings come from config file
launcher.download_and_deploy()
```

Your `config/deployment.yaml` in the repository:
```yaml
github:
  repo_owner: myorg
  repo_name: my-fabric-solution
  branch: main
  workspace_folder: workspace

deployment:
  staged_deployment: true
  validate_after_deployment: true

data:
  lakehouse_name: DataLH
  folder_mappings:
    data: reference-data
```

### Alternative: Basic Usage Without Config

```python
import notebookutils
from fabric_launcher import FabricLauncher

# Initialize the launcher
launcher = FabricLauncher(notebookutils)

# Download and deploy from GitHub in one operation
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-fabric-solution",
    workspace_folder="workspace",
    branch="main",
    data_folders={"data": "reference-data"},  # Optional
    lakehouse_name="DataLH"  # Optional
)
```

### Staged Deployment

Deploy items in multiple stages using the `item_type_stages` parameter:

```python
import notebookutils
from fabric_launcher import FabricLauncher

launcher = FabricLauncher(notebookutils)

# Deploy in stages: data stores first, then compute and analytics
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-fabric-solution",
    item_type_stages=[
        ["Eventhouse", "KQLDatabase", "Lakehouse"],  # Stage 1: Data stores
        ["Notebook", "Eventstream"],                  # Stage 2: Compute
        ["SemanticModel", "Report", "KQLDashboard"]  # Stage 3: Analytics
    ]
)
```

**Benefits:**
- Deploy dependencies first (e.g., Lakehouses before Notebooks)
- Better control over deployment order
- Clear separation of concerns
- Improved error isolation

### Complete Example

```python
import notebookutils
from fabric_launcher import FabricLauncher

# Initialize with custom settings
launcher = FabricLauncher(
    notebookutils,
    environment="PROD",
    debug=False,
    allow_non_empty_workspace=False  # Safety check: only deploy to empty workspaces
)

# Step 1: Download from GitHub
launcher.download_repository(
    repo_owner="myorg",
    repo_name="my-fabric-solution",
    extract_to=".lakehouse/default/Files/src",
    folder_to_extract="workspace",
    branch="main"
)

# Step 2: Deploy artifacts with staged deployment
launcher.deploy_artifacts(
    repository_directory=".lakehouse/default/Files/src/workspace"
)

# Step 3: Upload reference data files
launcher.upload_files_to_lakehouse(
    lakehouse_name="MyLakehouse",
    source_directory="./local-data",
    target_folder="reference-data",
    file_patterns=["*.json", "*.csv"]
)

# Step 4: Execute a post-deployment notebook
# Use for custom configurations, unsupported item types, or additional setup
result = launcher.run_notebook(
    notebook_name="Initialize-Data",
    parameters={"environment": "prod"}
)
print(f"Notebook job ID: {result['job_id']}")
```

## Advanced Features

### Configuration Files from GitHub

Store deployment configuration in your repository for version control and team collaboration:

```python
# Initialize with config from GitHub (recommended for production)
launcher = FabricLauncher(
    notebookutils,
    config_repo_owner="myorg",
    config_repo_name="my-solution",
    config_file_path="config/deployment.yaml",
    config_branch="main",
    config_github_token="ghp_xxx",  # Optional: for private repos
    environment="PROD"
)

# Deploy using all settings from config file
downloader, deployer, report = launcher.download_and_deploy()
```

**Benefits:**
- Configuration version-controlled with your code
- No local file management in Fabric notebooks
- Easy environment-specific overrides (DEV, TEST, PROD)
- Team collaboration with centralized settings

### Post-Deployment Validation

Automatically validate that deployed items are accessible:

```python
# Enable automatic validation
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-solution",
    validate_after_deployment=True  # Validates all deployed items
)

# Or validate manually after deployment
validation_results = launcher.validate_deployment(
    test_notebooks=True,
    test_lakehouses=True,
    test_notebooks_list=["DataProcessor", "ReportGenerator"]
)

if not validation_results["all_accessible"]:
    print(f"Warning: {validation_results['failed_count']} items failed validation")
```

### Deployment Reports

Get comprehensive deployment tracking and audit trails:

```python
downloader, deployer, report = launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-solution",
    generate_report=True  # Generate detailed report
)

# Report is automatically displayed and saved
print(f"Duration: {report.duration_seconds:.2f} seconds")
print(f"Deployed Items: {len(report.deployed_items)}")
print(f"Report saved to: deployment_report_{report.session_id}.json")
```

### Automatic Retry with Exponential Backoff

Handle transient failures automatically:

```python
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-solution",
    max_retries=5  # Retry failed operations up to 5 times
)
# Automatically retries with exponential backoff: 5s, 10s, 20s, 40s, 80s
```

### Enhanced Error Messages

Get actionable suggestions when errors occur:

```
❌ Deployment failed: 403 Forbidden

💡 Suggestions:
  • Check workspace permissions - you need Contributor or Admin role
  • Verify your authentication token is valid

🔧 Troubleshooting Tips:
  • Verify you have proper permissions on the workspace
  • Check Fabric service health: https://fabric.microsoft.com/status
```

### Private Repositories with Key Vault

Securely access private repositories using Fabric Key Vault:

```python
# Retrieve GitHub token from Key Vault
github_token = notebookutils.credentials.getSecret(
    "MyKeyVault", 
    "github-token"
)

# Use with config from private repository
launcher = FabricLauncher(
    notebookutils,
    config_repo_owner="myorg",
    config_repo_name="my-private-solution",
    config_file_path="config/deployment.yaml",
    config_github_token=github_token
)
```

## Main Methods

### `download_and_deploy()`

Download from GitHub and deploy in one operation.

```python
# Deploy all items at once
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-solution",
    workspace_folder="workspace",
    branch="main"
)

# Deploy specific item types
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-solution",
    item_types=["Lakehouse", "Notebook"]
)

# Deploy in stages (recommended for complex solutions)
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-solution",
    item_type_stages=[
        ["Eventhouse", "KQLDatabase"],      # Stage 1
        ["Notebook", "Eventstream"],        # Stage 2
        ["SemanticModel", "Report"]         # Stage 3
    ]
)
```

### `upload_files_to_lakehouse()`

Upload files to Lakehouse Files area.

```python
launcher.upload_files_to_lakehouse(
    lakehouse_name="MyLakehouse",
    source_directory="./data",
    target_folder="raw",
    file_patterns=["*.json", "*.csv"]
)
```

### `copy_data_folders_to_lakehouse()`

Copy multiple data folders from downloaded repository to Lakehouse.

```python
launcher.copy_data_folders_to_lakehouse(
    lakehouse_name="ReferenceDataLH",
    repository_base_path=".lakehouse/default/Files/src",
    folder_mappings={
        "data": "reference-data",
        "samples": "sample-data"
    },
    file_patterns=["*.json", "*.csv"],
    recursive=True
)
```

### `copy_folder_to_lakehouse()`

Copy a single folder to Lakehouse.

```python
launcher.copy_folder_to_lakehouse(
    lakehouse_name="DataLH",
    source_folder="./local-data",
    target_folder="reference-data",
    file_patterns=["*.json"]
)
```

### `run_notebook()`

Trigger notebook execution for post-deployment tasks.

Use this method to:
- Deploy item types not supported by fabric-cicd (requires custom code)
- Perform post-deployment configuration
- Initialize data or run setup tasks
- Execute any custom deployment logic

```python
result = launcher.run_notebook(
    notebook_name="ProcessData",
    parameters={"date": "2024-01-01"}
)
```

## Supported Fabric Item Types

This package supports **all Fabric item types supported by fabric-cicd**, including but not limited to:

- **Data Stores**: Lakehouse, KQLDatabase, Eventhouse
- **Compute**: Notebook, Eventstream
- **Analytics**: SemanticModel, Report, KQLDashboard
- **Automation**: Reflex, DataAgent
- **And more**: See the [fabric-cicd documentation](https://microsoft.github.io/fabric-cicd/0.1.3/) for the complete and up-to-date list of supported item types

> **Important**: For item types not yet supported by fabric-cicd, you can handle deployment through custom code in a post-deployment notebook using the `run_notebook()` method. This allows you to extend functionality beyond the core deployment capabilities.

## Safety Features

### Workspace Validation

By default, `fabric-launcher` validates that the target workspace is empty (except for the current notebook) before deployment. This prevents accidentally overwriting existing work.

```python
# Default: validates workspace is empty
launcher = FabricLauncher(notebookutils)
launcher.download_and_deploy(...)  # Blocks if workspace has existing items

# To deploy to non-empty workspace
launcher = FabricLauncher(
    notebookutils,
    allow_non_empty_workspace=True  # Explicitly allow
)
```

If validation fails, deployment is blocked with a clear error message listing existing items.


## Requirements

- Python 3.9+
- Access to Microsoft Fabric workspace
- Running within a Fabric Python notebook (for `notebookutils` access)
- Dependencies: `fabric-cicd`, `azure-core`, `azure-identity`, `requests`, `sempy`, `pyyaml`

## Parameterization and Value Replacement

For guidance on parameterizing your Fabric artifacts and using value replacement during deployment (e.g., environment-specific connection strings, workspace IDs, etc.), please refer to the [fabric-cicd documentation](https://microsoft.github.io/fabric-cicd/0.1.3/). The `fabric-launcher` package passes all deployment operations to fabric-cicd, so all parameterization features and syntax from fabric-cicd are fully supported.

## Custom Deployment Scenarios

### Deploying Unsupported Item Types

If you need to deploy Fabric item types not yet supported by fabric-cicd, you can handle this through a post-deployment notebook:

```python
# Deploy supported items first
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-solution"
)

# Run post-deployment notebook for custom item types
launcher.run_notebook(
    notebook_name="Deploy-Custom-Items",
    parameters={"environment": "prod"}
)
```

Your `Deploy-Custom-Items` notebook can contain custom code using Fabric APIs or other libraries to deploy unsupported items.

### Post-Deployment Configuration

Similarly, any post-deployment configuration (e.g., setting up permissions, configuring connections, initializing data) can be handled in a post-deployment notebook:

```python
# Deploy all items
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-solution"
)

# Configure deployed items
launcher.run_notebook(
    notebook_name="Post-Deploy-Config",
    parameters={
        "setup_permissions": True,
        "initialize_data": True
    }
)
```

## Examples

See the `examples/` directory for comprehensive usage examples:
- `example_usage.py` - Basic usage examples
- `advanced_usage.py` - Advanced features (config files, validation, reporting)
- `deployment_config_example.yaml` - Sample configuration file
- `Example_Deployment.ipynb` - Interactive notebook example

## Development and Testing

### Running Tests

The package includes comprehensive unit tests covering all major functionality.

#### Using unittest (built-in, no additional dependencies)

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_launcher

# Run with verbose output
python -m unittest discover tests -v
```

#### Using pytest (recommended)

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=fabric_launcher --cov-report=html

# Run specific test file
pytest tests/test_launcher.py -v
```

#### Test Coverage

Current test coverage includes:
- ✅ GitHub repository download and extraction
- ✅ Configuration management (YAML/JSON)
- ✅ Configuration download from GitHub
- ✅ Deployment reporting and tracking
- ✅ Main launcher orchestration
- ✅ Error handling and edge cases

See `tests/README.md` for detailed testing documentation.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/fabric-launcher.git
cd fabric-launcher

# Install in development mode with test dependencies
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov=fabric_launcher

# Check code formatting
black --check fabric_launcher/ tests/

# Run linter
flake8 fabric_launcher/ tests/
```

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

The CI/CD pipeline will automatically run tests on multiple Python versions and operating systems.

## License

MIT
