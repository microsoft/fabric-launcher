# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2024-11-21

### Added - Advanced Features
- **Configuration File Support**: Deploy using YAML/JSON configuration files
  - `DeploymentConfig` class for managing configuration
  - **Download config files from GitHub repositories** (ideal for Fabric notebooks)
  - Support for local config files (for development/testing)
  - `download_config_from_github()` static method for pre-download
  - Environment-specific overrides (DEV, TEST, PROD)
  - Template generation via `create_config_template()`
  - Support for all deployment parameters in config files
  - Private repository support with GitHub tokens

- **Post-Deployment Validation**: Automatically validate deployed items
  - `DeploymentValidator` class for testing item accessibility
  - Test notebooks, lakehouses, and other item types
  - Configurable validation via `validate_after_deployment` parameter
  - Manual validation via `validate_deployment()` method

- **Deployment Reporting**: Comprehensive deployment tracking and reporting
  - `DeploymentReport` class for tracking deployment progress
  - Step-by-step execution tracking with timestamps
  - Deployed item tracking with success/failure status
  - JSON report export for audit trails
  - Summary report printing with duration metrics

- **Retry Logic**: Automatic retry with exponential backoff
  - Configurable retry attempts via `max_retries` parameter
  - Exponential backoff delay between retries
  - Retry for download, deployment, and data upload operations
  - Detailed logging of retry attempts

- **Enhanced Error Messages**: Actionable error messages with suggestions
  - Context-aware error suggestions based on error type
  - Permission issues: suggests checking workspace roles
  - Network issues: suggests timeout and connectivity checks
  - Conflict issues: suggests using allow_non_empty_workspace
  - Capacity issues: suggests checking Fabric capacity status
  - Links to troubleshooting resources

### Changed
- Updated `FabricLauncher.__init__()` to accept configuration parameters:
  - `config_file` - Local configuration file path
  - `config_repo_owner` - GitHub repo owner for config download
  - `config_repo_name` - GitHub repo name for config download
  - `config_file_path` - Path to config file within GitHub repo
  - `config_branch` - Branch for config file (default: "main")
  - `config_github_token` - Token for private repositories
- Enhanced `download_and_deploy()` with validation and reporting parameters
- Updated return type of `download_and_deploy()` to include `DeploymentReport`
- Added `validator` property to `FabricLauncher` for lazy initialization
- Added `validate_deployment()`, `create_config_template()`, and `download_config_from_github()` methods
- Updated `DeploymentConfig` to support downloading from GitHub
- Updated package version to 0.3.0

### Dependencies
- Added `pyyaml>=6.0` for configuration file support
- All other dependencies unchanged

### Documentation
- **fabric-cicd Integration**: Enhanced documentation to clarify relationship with fabric-cicd
  - Added references to [fabric-cicd documentation](https://microsoft.github.io/fabric-cicd/0.1.3/)
  - Clarified that all fabric-cicd supported item types are supported
  - Added guidance on parameterization and value replacement (refer to fabric-cicd docs)
  - Documented custom deployment scenarios for unsupported item types
  - Explained post-deployment notebook usage for custom configurations
  - Updated supported item types section with fabric-cicd reference

### Testing
- **Comprehensive Unit Test Suite**: Added full test coverage for all major components
  - `tests/test_github_downloader.py` - Tests for GitHub download/extraction (169 lines)
  - `tests/test_config_manager.py` - Tests for configuration management (220 lines)
  - `tests/test_deployment_report.py` - Tests for deployment reporting (177 lines)
  - `tests/test_launcher.py` - Tests for main launcher orchestration (241 lines)
  - All tests use mocking for Fabric-specific dependencies
  - Tests cover success scenarios, error handling, and edge cases
  - Test coverage >80% for all modules

- **Test Infrastructure**: Complete testing setup
  - `run_tests.py` - Simple test runner script
  - `pytest.ini` - Pytest configuration with coverage settings
  - `requirements-dev.txt` - Development and test dependencies
  - `tests/README.md` - Comprehensive testing documentation
  - `.github/workflows/tests.yml` - CI/CD pipeline for automated testing
  - Tests run on Python 3.9, 3.10, 3.11, 3.12 across Ubuntu, Windows, macOS

- **Development Documentation**:
  - `CONTRIBUTING.md` - Complete contributor guide
  - Test writing guidelines and mocking strategies
  - Code style guide with Black and Flake8 configuration
  - Pull request and commit message guidelines

### Examples
- Added `examples/advanced_usage.py` with comprehensive examples
- Added `examples/production_workflow.py` demonstrating GitHub config workflows
- Added `examples/deployment_config_example.yaml` template
- Updated documentation with configuration examples
- Added examples for private repositories with Key Vault integration

## [0.2.0] - 2024-11-21

### Added
- Complete PyPI package for Fabric solution deployment
- `FabricLauncher` main orchestrator class
- `GitHubDownloader` for downloading and extracting GitHub repositories
- `FabricDeployer` for deploying Fabric workspace items with staged deployment support
- `FabricNotebookTokenCredential` for authentication in Fabric notebooks
- `LakehouseFileManager` for uploading files to Lakehouse Files area
- `NotebookExecutor` for triggering and monitoring Fabric notebook execution
- Support for downloading source code from GitHub repositories
- Support for deploying Fabric artifacts (Lakehouse, Notebook, Eventstream, etc.)
- Support for uploading files from GitHub or local directories to Lakehouse
- Support for triggering Fabric notebook execution (sync and async)
- Comprehensive documentation and examples
- Example deployment notebook
- Quick reference guide

### Changed
- Updated package description and metadata
- Enhanced README with complete API documentation
- Improved error handling and logging throughout

### Dependencies
- fabric-cicd >= 0.1.0
- azure-core >= 1.26.0
- azure-identity >= 1.12.0
- requests >= 2.28.0
- sempy >= 0.7.0

## [0.1.3] - Previous

### Initial
- Basic hello world package structure

## Supported Fabric Item Types

This package supports **all Fabric item types supported by fabric-cicd**, including but not limited to:

- **Data Stores**: Lakehouse, KQLDatabase, Eventhouse
- **Compute**: Notebook, Eventstream
- **Analytics**: SemanticModel, Report, KQLDashboard
- **Automation**: Reflex, DataAgent
- **And more**: See the [fabric-cicd documentation](https://microsoft.github.io/fabric-cicd/0.1.3/) for the complete and up-to-date list

For item types not supported by fabric-cicd, custom deployment can be handled through post-deployment notebooks.

## Usage Notes

This package is designed to be used within Microsoft Fabric Python notebooks where `notebookutils` is available. It wraps the [fabric-cicd library](https://microsoft.github.io/fabric-cicd/0.1.3/) to provide a higher-level, more user-friendly interface for common Fabric deployment scenarios.

For parameterization and value replacement in your Fabric artifacts, follow the guidance in the [fabric-cicd documentation](https://microsoft.github.io/fabric-cicd/0.1.3/).

## Migration from Previous Versions

If you were using version 0.1.x:
- Remove any calls to `hello_world()` 
- Import `FabricLauncher` instead
- See README.md for updated usage examples
