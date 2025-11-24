# fabric-launcher Documentation

Documentation for fabric-launcher - a wrapper around fabric-cicd for deploying Microsoft Fabric solutions from GitHub repositories.

## Contents

- [Quick Start Guide](QUICKSTART.md) - Get started in minutes
- [API Reference](API.md) - Complete API documentation
- [Examples](../examples/README.md) - Usage examples and patterns

## Overview

fabric-launcher simplifies the deployment of Microsoft Fabric solutions by:

- **Downloading** GitHub repositories directly into Fabric notebooks
- **Deploying** Fabric items (Lakehouses, Notebooks, Reports, etc.) to workspaces
- **Managing** staged deployments with dependency ordering
- **Uploading** data files to Lakehouses
- **Validating** deployments with built-in checks
- **Supporting** environment-specific configurations (DEV, TEST, PROD)

## Prerequisites

- Python 3.9 or higher
- Microsoft Fabric workspace with appropriate permissions
- Running in a Fabric notebook environment
- Access to GitHub repositories (public or authenticated)

## Installation

```python
%pip install fabric-launcher
notebookutils.session.restartPython()
```

## Quick Example

```python
import notebookutils
from fabric_launcher import FabricLauncher

launcher = FabricLauncher(notebookutils)
launcher.download_and_deploy(
    repo_owner="your-org",
    repo_name="your-repo",
    workspace_folder="workspace",
    item_type_stages=[
        ["Lakehouse"],
        ["Notebook"],
        ["SemanticModel", "Report"]
    ]
)
```

## Key Features

### GitHub Integration

- Download public or private repositories
- Support for specific branches and folders
- Automatic extraction and cleanup

### Flexible Deployment

- Deploy all items or filter by type
- Staged deployment for dependencies
- Support for all Fabric item types

### Data Management

- Upload reference data to Lakehouses
- Pattern-based file selection
- Folder mapping for organization

### Configuration Management

- YAML-based configuration files
- Environment-specific settings
- Local or GitHub-hosted configs

### Post-Deployment

- Execute notebooks with parameters
- Validate deployed items
- Generate deployment reports
- Custom post-deployment utilities

## Supported Item Types

All [fabric-cicd](https://microsoft.github.io/fabric-cicd/) item types are supported:

**Data:**
- Lakehouse
- KQLDatabase
- Eventhouse

**Compute:**
- Notebook
- Eventstream
- DataPipeline

**Analytics:**
- SemanticModel
- Report
- KQLDashboard

**Other:**
- Reflex
- DataAgent
- MLExperiment
- MLModel
- and more...

## Documentation Structure

```
docs/
├── README.md       # This file - overview and navigation
├── QUICKSTART.md   # Quick start guide with examples
└── API.md          # Complete API reference
```

## Getting Help

- **Examples**: Check the [examples/](../examples/) directory for comprehensive examples
- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/microsoft/fabric-launcher/issues)
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines

## Related Projects

- [fabric-cicd](https://github.com/microsoft/fabric-cicd) - Underlying deployment library
- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)

## License

MIT License - see [LICENSE](../LICENSE) file for details.
