# fabric-launcher Examples

This directory contains example scripts demonstrating how to use fabric-launcher for deploying Microsoft Fabric solutions.

## Prerequisites

Before running these examples, ensure you have:

1. **Microsoft Fabric Workspace Access**: You need access to a Fabric workspace with appropriate permissions to create and manage items.

2. **Authentication**: These examples are designed to run in a Microsoft Fabric notebook environment where authentication is handled automatically through `sempy.fabric`.

3. **Required Python Packages**:
   ```bash
   pip install fabric-launcher
   ```

4. **Environment Setup**:
   - The examples assume you're running in a Fabric notebook with access to `notebookutils`
   - For `post_deployment_utils_examples.py`, ensure the repository has already been downloaded to the specified directory

## Example Files

### `accessing_launcher_properties_examples.py`
Demonstrates how to access deployment metadata, item lists, and workspace information after deployment.

**Prerequisites**: GitHub repository URL

### `advanced_deployment_examples.py`
Shows advanced features including custom configurations, error handling, and workspace recreation.

**Prerequisites**: GitHub repository URL, workspace access

### `basic_deployment_examples.py`
Simple deployment workflows and basic usage patterns.

**Prerequisites**: GitHub repository URL

### `staged_deployment_examples.py`
Demonstrates multi-stage deployments (dev → test → prod) with environment-specific configurations.

**Prerequisites**: GitHub repository URL, production workspace access

### `staged_deployment.py`
Demonstrates multi-stage deployments (dev → test → prod) with environment-specific configurations.

**Prerequisites**: GitHub repository URL, access to multiple workspaces

### `post_deployment_utils_examples.py`
Comprehensive examples of post-deployment utility functions including:
- Custom item deployments with logical ID replacement
- Item organization and folder management
- Eventhouse and KQL Database operations
- Creating shortcuts and accelerated external tables
- SQL endpoint queries and KQL command execution

**Prerequisites**: 
- Repository already downloaded to `/lakehouse/default/Files/src/workspace` (for basic examples)
- Fabric workspace with appropriate items and folders
- For Eventhouse/SQL examples: Eventhouse with KQL Database and Lakehouse
- `sempy.fabric` for authentication (available in Fabric notebooks)

### `deployment_config_example.yaml`
Sample YAML configuration file for deployment settings.

## Running the Examples

### In a Fabric Notebook

1. Copy the example code into a new notebook cell
2. Modify the configuration values (GitHub URL, directories, etc.)
3. Run the cell

Example:
```python
from fabric_launcher import FabricLauncher

launcher = FabricLauncher(
    github_url="https://github.com/your-org/your-repo",
    target_directory="/lakehouse/default/Files/src"
)

launcher.deploy()
```

### Logging Configuration

The library uses Python's standard logging module. Configure logging verbosity as needed:

```python
import logging

# Set to INFO for standard output
logging.basicConfig(level=logging.INFO)

# Set to DEBUG for detailed output
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Set to WARNING to minimize output
logging.basicConfig(level=logging.WARNING)
```

### Using Configuration Files

Create a YAML configuration file based on `deployment_config_example.yaml`:

```python
from fabric_launcher import FabricLauncher

launcher = FabricLauncher(config_file="my_deployment_config.yaml")
launcher.deploy()
```

## Common Issues

### Authentication Errors
- Ensure you're running in a Fabric notebook environment
- Verify workspace access permissions

### Path Errors
- Adjust `target_directory` to match your lakehouse structure
- Use absolute paths starting with `/lakehouse/default/Files/`

### Repository Not Found
- Verify the GitHub URL is publicly accessible or you have appropriate access
- Check branch names match (default is typically `main` or `master`)

## Additional Resources

- [Main Documentation](../docs/index.rst)
- [API Reference](../docs/api.rst)
- [Contributing Guide](../CONTRIBUTING.md)
- [Quick Start](../QUICKSTART.md)

## Support

For issues or questions:
- Open an issue on GitHub
- Check the documentation in the `docs/` directory
- Review the test files in `tests/` for additional usage patterns
