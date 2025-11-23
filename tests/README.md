# fabric-launcher Tests

This directory contains unit tests for the fabric-launcher package.

## Test Structure

```
tests/
├── __init__.py                      # Test package initialization
├── test_github_downloader.py        # Tests for GitHub download functionality
├── test_config_manager.py           # Tests for configuration management
├── test_deployment_report.py        # Tests for deployment reporting
└── test_launcher.py                 # Tests for main launcher orchestration
```

## Running Tests

### Using unittest (no additional dependencies)

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_github_downloader

# Run specific test class
python -m unittest tests.test_github_downloader.TestGitHubDownloader

# Run specific test method
python -m unittest tests.test_github_downloader.TestGitHubDownloader.test_initialization
```

### Using pytest (recommended, requires pytest)

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=fabric_launcher --cov-report=html

# Run specific test file
pytest tests/test_github_downloader.py

# Run tests matching pattern
pytest tests/ -k "test_download"

# Run with verbose output
pytest tests/ -v

# Run and stop at first failure
pytest tests/ -x
```

### Using the test runner script

```bash
python run_tests.py
```

## Test Coverage

Current test coverage includes:

### GitHubDownloader (`test_github_downloader.py`)
- ✅ Initialization with and without token
- ✅ Repository download success and failure cases
- ✅ Authentication with GitHub token
- ✅ 404 error handling
- ✅ Folder path filtering during extraction
- ✅ Integration workflow testing

### DeploymentConfig (`test_config_manager.py`)
- ✅ Loading YAML configuration files
- ✅ Loading JSON configuration files
- ✅ File not found error handling
- ✅ Unsupported format error handling
- ✅ Getting GitHub configuration
- ✅ Getting deployment configuration
- ✅ Getting data configuration
- ✅ Downloading config from GitHub
- ✅ GitHub 404 error handling
- ✅ Authentication with GitHub token
- ✅ Creating configuration template

### DeploymentReport (`test_deployment_report.py`)
- ✅ Initialization and session ID generation
- ✅ Adding steps to report
- ✅ Adding deployed items
- ✅ Duration calculation
- ✅ Saving report to JSON
- ✅ Directory creation for nested paths
- ✅ Printing report summary
- ✅ Converting report to dictionary
- ✅ Handling empty reports
- ✅ Handling special characters
- ✅ Handling None values

### FabricLauncher (`test_launcher.py`)
- ✅ Basic initialization
- ✅ Initialization with custom parameters
- ✅ Initialization with local config file
- ✅ Initialization with GitHub config
- ✅ Lazy-loaded property initialization
- ✅ Repository download method
- ✅ Artifact deployment method
- ✅ Static config download method
- ✅ Download and deploy workflow
- ✅ Parameter validation

## Mocking Strategy

Since fabric-launcher is designed for Fabric notebook environments, the tests mock:

- **notebookutils**: The Fabric notebook utilities module
- **sempy.fabric**: The Fabric workspace API
- **fabric-cicd**: The Fabric deployment library (when testing integration)

This allows tests to run in any Python environment without requiring actual Fabric workspace access.

## Writing New Tests

When adding new tests:

1. Follow the existing test structure
2. Use descriptive test names: `test_<method>_<scenario>`
3. Mock external dependencies (notebookutils, fabric, network calls)
4. Test both success and error cases
5. Include docstrings explaining what the test validates

Example:

```python
def test_new_feature_success(self):
    """Test successful execution of new feature."""
    # Arrange
    mock_dependency = Mock()
    
    # Act
    result = function_under_test(mock_dependency)
    
    # Assert
    self.assertEqual(result, expected_value)
```

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install pytest pytest-cov
    pytest tests/ --cov=fabric_launcher --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Test Dependencies

- **unittest**: Built-in Python testing framework (no installation needed)
- **pytest** (optional but recommended): Enhanced testing framework
- **pytest-cov** (optional): Coverage reporting
- **pytest-mock** (optional): Enhanced mocking capabilities

Install test dependencies:
```bash
pip install -r requirements-dev.txt
```

## Known Limitations

- Integration tests with actual Fabric workspaces are not included (would require live environment)
- Some fabric-cicd specific behavior is mocked and may not reflect actual runtime behavior
- File system operations are tested but may behave differently across OSes

## Future Improvements

- [ ] Add integration tests for live Fabric environment (optional, for CI)
- [ ] Add performance/load tests
- [ ] Add tests for FabricDeployer retry logic
- [ ] Add tests for DeploymentValidator
- [ ] Increase coverage to >90%
- [ ] Add mutation testing
