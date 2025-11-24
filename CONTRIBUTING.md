# Contributing to fabric-launcher

Thank you for your interest in contributing to fabric-launcher! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- A GitHub account (for contributing)

### Initial Setup

1. **Fork and clone the repository:**

```bash
git clone https://github.com/yourusername/fabric-launcher.git
cd fabric-launcher
```

2. **Create a virtual environment:**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install the package in development mode:**

```bash
# Install the package
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

This installs:
- Testing tools: pytest, pytest-cov, pytest-mock, coverage
- Code quality tools: flake8, black, mypy
- Documentation tools: sphinx, sphinx-rtd-theme

4. **Verify the installation:**

```bash
# Run tests to verify everything is working
pytest tests/ -v
```

## Running Tests

### Quick Test Run

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=fabric_launcher --cov-report=term

# Run specific test file
pytest tests/test_launcher.py -v
```

### Comprehensive Test Run

```bash
# Run all tests with detailed coverage report
pytest tests/ -v --cov=fabric_launcher --cov-report=html --cov-report=term

# Open coverage report in browser
# Windows: start htmlcov/index.html
# Mac: open htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
```

### Alternative Test Runners

You can also use unittest if needed:

```bash
# Run with unittest
python -m unittest discover tests -v
```

### Test Coverage Goals

- Aim for >80% code coverage for new features
- All critical paths must have tests
- Include both success and failure scenarios
- Test edge cases and error conditions

## Code Style

### Python Style Guide

This project follows [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines.

### Formatting with Black

We use [Black](https://black.readthedocs.io/) for code formatting:

```bash
# Format all code
black fabric_launcher/ tests/

# Check formatting without making changes
black --check fabric_launcher/ tests/
```

### Linting with Flake8

```bash
# Run flake8 on all code
flake8 fabric_launcher/ tests/

# Check for critical errors only
flake8 fabric_launcher/ tests/ --select=E9,F63,F7,F82
```

### Type Hints

- Use type hints for function parameters and return values
- Run mypy to check type correctness:

```bash
mypy fabric_launcher/
```

## Testing Guidelines

### Writing Tests

1. **Test file naming:**
   - Test files should be named `test_<module_name>.py`
   - Place in the `tests/` directory

2. **Test class naming:**
   - Use descriptive test class names: `TestFeatureName`
   - Group related tests in the same class

3. **Test method naming:**
   - Use pattern: `test_<method>_<scenario>`
   - Examples: `test_download_success`, `test_download_404_error`

4. **Test structure (Arrange-Act-Assert):**

```python
def test_feature_success(self):
    """Test successful execution of feature."""
    # Arrange - set up test data and mocks
    mock_dependency = Mock()
    expected_result = "expected"
    
    # Act - execute the code being tested
    result = function_under_test(mock_dependency)
    
    # Assert - verify the results
    self.assertEqual(result, expected_result)
    mock_dependency.method.assert_called_once()
```

### Mocking Strategy

Since fabric-launcher is designed for Fabric notebooks, tests mock:

- **notebookutils**: Fabric notebook utilities
- **sempy.fabric**: Fabric workspace API
- **fabric-cicd components**: Fabric deployment library
- **Network calls**: requests.get, requests.post

Example:

```python
from unittest.mock import Mock, patch

@patch('fabric_launcher.launcher.fabric.get_workspace_id')
def test_with_fabric_mock(self, mock_workspace_id):
    mock_workspace_id.return_value = "test-workspace-id"
    # ... rest of test
```

### Test Coverage Requirements

- New features must include tests
- Bug fixes should include regression tests
- Aim for >80% code coverage
- Critical paths require 100% coverage

## Submitting Changes

### Creating a Pull Request

1. **Create a feature branch:**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes:**
   - Write code following the style guide
   - Add tests for new functionality
   - Update documentation as needed

3. **Verify your changes:**

```bash
# Run tests
pytest tests/ -v --cov=fabric_launcher

# Check formatting
black --check fabric_launcher/ tests/

# Run linter
flake8 fabric_launcher/ tests/
```

4. **Commit your changes:**

```bash
git add .
git commit -m "Add feature: description of your feature"
```

5. **Push to your fork:**

```bash
git push origin feature/your-feature-name
```

6. **Create pull request:**
   - Go to the GitHub repository
   - Click "New Pull Request"
   - Select your feature branch
   - Provide a clear description of changes

### Pull Request Guidelines

- **Title**: Clear and concise description
- **Description**: 
  - What changes were made
  - Why the changes were necessary
  - How to test the changes
- **Tests**: Include test results or screenshots
- **Documentation**: Update README/docs if needed

### Commit Message Format

Follow the conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `style`: Formatting changes
- `chore`: Maintenance tasks

Example:
```
feat(launcher): add support for configuration files

- Added DeploymentConfig class for YAML/JSON configs
- Enhanced FabricLauncher with config_file parameter
- Updated documentation with config examples

Closes #123
```

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.
    
    More detailed description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: Description of when this is raised
    """
    pass
```

### README Updates

When adding features:
- Update the Features section
- Add usage examples
- Update the Quick Start if applicable

### Documentation

Update documentation in the `docs/` directory:
- `docs/README.md`: Main documentation overview
- `docs/QUICKSTART.md`: Quick start guide
- `docs/API.md`: API reference

Documentation is written in Markdown for easy reading on GitHub.

### Changelog

Add entry to `CHANGELOG.md` for significant changes:

```markdown
## [Version] - Date

### Added
- New feature description

### Fixed
- Bug fix description

### Changed
- Breaking change description
```

## CI/CD Pipeline

The repository uses GitHub Actions for continuous integration:

- **Tests**: Runs on Python 3.9, 3.10, 3.11, 3.12
- **Platforms**: Ubuntu, Windows, macOS
- **Coverage**: Reports uploaded to Codecov
- **Linting**: Black and Flake8 checks

All pull requests must pass CI checks before merging.

## Getting Help

- **Issues**: Open an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check the `docs/` directory for comprehensive documentation

## Code of Conduct

Be respectful and constructive in all interactions. We aim to create a welcoming environment for all contributors.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
