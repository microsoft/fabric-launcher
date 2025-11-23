# Fabric Launcher Package Structure

## Overview

This document describes the complete structure of the `fabric-launcher` PyPI package, which wraps the `fabric-cicd` library to provide simplified Fabric solution deployment from GitHub repositories.

## Package Structure

```
fabric-launcher/
├── fabric_launcher/                 # Main package directory
│   ├── __init__.py                 # Package initialization and exports
│   ├── launcher.py                 # Main FabricLauncher orchestrator class
│   ├── github_downloader.py        # GitHub repository download functionality
│   ├── fabric_deployer.py          # Fabric workspace deployment
│   ├── file_operations.py          # Lakehouse file upload operations
│   ├── notebook_executor.py        # Notebook execution and monitoring
│   └── examples/                   # Usage examples
│       ├── example_usage.py        # Python script example
│       └── Example_Deployment.ipynb # Jupyter notebook example
├── pyproject.toml                  # Package configuration
├── MANIFEST.in                     # Package manifest
├── README.md                       # Main documentation
├── QUICKSTART.md                   # Quick reference guide
├── CHANGELOG.md                    # Version history
├── LICENSE                         # License file
└── SECURITY.md                     # Security policy

```

## Core Modules

### 1. launcher.py - FabricLauncher (Main Orchestrator)

**Purpose**: High-level interface that orchestrates all deployment operations.

**Key Methods**:
- `download_and_deploy()` - All-in-one download and deployment
- `download_repository()` - Download from GitHub
- `deploy_artifacts()` - Deploy Fabric items
- `upload_files_to_lakehouse()` - Upload files to Lakehouse
- `download_and_upload_files_from_github()` - Direct GitHub to Lakehouse
- `run_notebook()` - Trigger notebook execution (async)
- `run_notebook_sync()` - Run notebook synchronously
- `get_notebook_job_status()` - Check job status
- `cancel_notebook_job()` - Cancel running job

**Usage**:
```python
from fabric_launcher import FabricLauncher
launcher = FabricLauncher(notebookutils)
launcher.download_and_deploy(repo_owner="org", repo_name="solution")
```

### 2. github_downloader.py - GitHubDownloader

**Purpose**: Download and extract content from GitHub repositories.

**Key Methods**:
- `download_and_extract_folder()` - Download and extract repository folder
- `download_file()` - Download a single file

**Features**:
- Support for public and private repositories (with token)
- Extract specific folders from repositories
- Remove folder prefixes during extraction

### 3. fabric_deployer.py - FabricDeployer

**Purpose**: Deploy Fabric workspace items using fabric-cicd library.

**Key Classes**:
- `FabricNotebookTokenCredential` - Authentication for Fabric notebooks
- `FabricDeployer` - Deployment orchestrator

**Key Methods**:
- `deploy_items()` - Deploy specific item types
- `deploy_data_stores()` - Deploy Lakehouse, KQLDatabase, Eventhouse
- `deploy_compute_and_analytics()` - Deploy Notebooks, Reports, etc.
- `deploy_all_in_stages()` - Staged deployment (data stores first)

**Supported Item Types**:
- Data Stores: Lakehouse, KQLDatabase, Eventhouse
- Compute: Notebook, Eventstream
- Analytics: SemanticModel, Report, KQLDashboard
- Automation: Reflex, DataAgent

### 4. file_operations.py - LakehouseFileManager

**Purpose**: Manage files in Fabric Lakehouse Files area.

**Key Methods**:
- `upload_files_to_lakehouse()` - Upload multiple files with pattern filtering
- `upload_file_to_lakehouse()` - Upload a single file
- `download_and_upload_from_github()` - Direct GitHub to Lakehouse upload

**Features**:
- File pattern matching (*.json, *.csv, etc.)
- Automatic directory creation
- Lakehouse mounting and unmounting

### 5. notebook_executor.py - NotebookExecutor

**Purpose**: Execute and monitor Fabric notebooks.

**Key Methods**:
- `run_notebook()` - Asynchronous notebook execution
- `run_notebook_synchronous()` - Synchronous execution (blocks)
- `get_job_status()` - Check job status
- `cancel_job()` - Cancel running job

**Features**:
- Parameter passing to notebooks
- Job monitoring and status checking
- Timeout configuration

## Configuration Files

### pyproject.toml

Package metadata and dependencies:
- Package name: `fabric-launcher`
- Version: `0.2.0`
- Python requirement: `>=3.9`
- Dependencies: fabric-cicd, azure-core, azure-identity, requests, sempy

### MANIFEST.in

Specifies files to include in the distribution package.

## Documentation Files

### README.md

Comprehensive documentation including:
- Overview and features
- Installation instructions
- Quick start guide
- Complete API reference
- Usage examples
- Troubleshooting guide

### QUICKSTART.md

Quick reference guide with:
- Common operations
- Code snippets
- Configuration options
- Troubleshooting tips

### CHANGELOG.md

Version history and release notes.

## Examples

### examples/example_usage.py

Python script demonstrating:
- Basic usage
- Step-by-step deployment
- File uploads
- Notebook execution
- Advanced component usage

### examples/Example_Deployment.ipynb

Jupyter notebook with:
- Package installation
- Configuration setup
- Download and deployment
- File uploads
- Post-deployment tasks
- Alternative approaches

## Key Features

### 1. Simple API
High-level methods abstract away complexity:
```python
launcher.download_and_deploy(repo_owner="org", repo_name="solution")
```

### 2. Fabric-Native
Designed for Fabric notebooks with notebookutils integration:
```python
launcher = FabricLauncher(notebookutils)
```

### 3. Flexible Deployment
- Staged deployment (data stores → compute)
- Selective item type deployment
- Custom deployment workflows

### 4. GitHub Integration
- Public and private repository support
- Folder extraction
- Direct file downloads

### 5. File Management
- Upload to Lakehouse Files area
- Pattern-based filtering
- GitHub to Lakehouse direct transfer

### 6. Notebook Orchestration
- Async and sync execution
- Parameter passing
- Job monitoring

## Installation

```bash
%pip install fabric-launcher
%pip install --upgrade azure-core azure-identity
notebookutils.session.restartPython()
```

## Basic Usage Pattern

```python
import notebookutils
from fabric_launcher import FabricLauncher

# 1. Initialize
launcher = FabricLauncher(notebookutils, environment="PROD")

# 2. Deploy
launcher.download_and_deploy(
    repo_owner="myorg",
    repo_name="my-solution",
    folder_to_extract="workspace"
)

# 3. Upload files
launcher.upload_files_to_lakehouse(
    lakehouse_name="DataLH",
    source_directory="./data",
    target_folder="reference"
)

# 4. Execute notebook
result = launcher.run_notebook(
    notebook_name="Initialize",
    parameters={"env": "prod"}
)
```

## Dependencies

- **fabric-cicd**: Core deployment library
- **azure-core**: Azure SDK core functionality
- **azure-identity**: Azure authentication
- **requests**: HTTP library for GitHub API
- **sempy**: Semantic link for Fabric operations

## Design Principles

1. **Simplicity**: High-level API hides complexity
2. **Composability**: Can use individual components
3. **Flexibility**: Multiple deployment approaches
4. **Safety**: Staged deployment for dependencies
5. **Visibility**: Clear progress indicators and logging

## Typical Workflow

1. **Install** package in Fabric notebook
2. **Configure** repository and deployment settings
3. **Initialize** FabricLauncher with notebookutils
4. **Download** solution from GitHub
5. **Deploy** Fabric items (staged or selective)
6. **Upload** reference data files
7. **Execute** post-deployment notebooks
8. **Verify** deployment success

## Extension Points

The package is designed to be extended:
- Add custom authentication methods
- Implement custom deployment strategies
- Add support for additional Fabric item types
- Integrate with CI/CD pipelines

## Related Projects

- [fabric-cicd](https://github.com/microsoft/fabriccicd) - Underlying deployment library

## License

MIT License
