# Code Quality with Ruff

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and code formatting. Ruff is an extremely fast Python linter and formatter, written in Rust, that combines the functionality of multiple tools (Flake8, isort, Black, and more).

## Installation

Ruff is included in the development dependencies:

```bash
pip install -r requirements-dev.txt
```

Or install it separately:

```bash
pip install ruff
```

## VS Code Setup

The project includes VS Code settings (`.vscode/settings.json`) that automatically:
- Use Ruff as the default Python formatter
- Format code on save
- Organize imports on save
- Run linting checks

To enable these features, install the [Ruff VS Code extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff):

```
code --install-extension charliermarsh.ruff
```

## Usage

### Check for Issues

```bash
# Check all files
ruff check fabric_launcher/

# Check specific file
ruff check fabric_launcher/launcher.py

# Show statistics
ruff check fabric_launcher/ --statistics
```

### Auto-fix Issues

```bash
# Fix safe issues
ruff check --fix fabric_launcher/

# Fix unsafe issues too (use with caution)
ruff check --fix --unsafe-fixes fabric_launcher/
```

### Format Code

```bash
# Format all files
ruff format fabric_launcher/

# Check formatting without making changes
ruff format --check fabric_launcher/
```

## Configuration

Ruff configuration is in `pyproject.toml` under `[tool.ruff]`. Current configuration:

- **Target Python version**: 3.9+
- **Line length**: 120 characters
- **Enabled rules**:
  - `E`, `W`: pycodestyle errors and warnings
  - `F`: Pyflakes
  - `I`: isort (import sorting)
  - `N`: pep8-naming
  - `UP`: pyupgrade (modern Python syntax)
  - `B`: flake8-bugbear
  - `C4`: flake8-comprehensions
  - `SIM`: flake8-simplify
  - `RET`: flake8-return
  - `ARG`: flake8-unused-arguments
  - `PTH`: flake8-use-pathlib

- **Ignored rules**:
  - `E501`: Line too long (handled by formatter)
  - `B008`: Function calls in argument defaults
  - `ARG002`: Unused method arguments (common in overrides)
  - `PTH123`: pathlib for notebookutils compatibility

## Pre-commit Integration

You can add Ruff to your pre-commit hooks by creating `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
```

Then install:

```bash
pip install pre-commit
pre-commit install
```

## CI/CD

Ruff runs automatically in GitHub Actions on every push and pull request. See `.github/workflows/tests.yml` for configuration.

## Migration from Previous Tools

This project previously used:
- **Flake8** → Now using Ruff (compatible rules enabled)
- **Black** → Now using Ruff formatter (Black-compatible)
- **isort** → Now using Ruff's import sorting

Ruff provides all this functionality in a single tool that's 10-100x faster.

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Ruff Rule Reference](https://docs.astral.sh/ruff/rules/)
- [Ruff Settings](https://docs.astral.sh/ruff/settings/)
