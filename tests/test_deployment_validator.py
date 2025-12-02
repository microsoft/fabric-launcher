"""
Tests for the DeploymentValidator class in deployment_validator module.
"""

import json
import sys
from unittest.mock import MagicMock

# Import the mock DataFrame from conftest (loaded via sys.modules)
pd = sys.modules["pandas"]

from fabric_launcher.deployment_validator import DeploymentValidator  # noqa: E402


class TestDeploymentValidatorInit:
    """Tests for DeploymentValidator initialization."""

    def test_initialization(self):
        """Test basic initialization."""
        mock_notebookutils = MagicMock()
        validator = DeploymentValidator(workspace_id="test-workspace-id", notebookutils=mock_notebookutils)

        assert validator.workspace_id == "test-workspace-id"
        assert validator.notebookutils == mock_notebookutils
        assert validator.validation_results == {}


class TestSaveValidationReport:
    """Tests for save_validation_report method."""

    def test_save_report_success(self, tmp_path):
        """Test saving validation report to file."""
        mock_notebookutils = MagicMock()
        validator = DeploymentValidator(workspace_id="test-workspace-id", notebookutils=mock_notebookutils)

        # Set validation results
        validator.validation_results = {"timestamp": "2024-01-01T00:00:00", "validation_passed": True, "items": []}

        output_path = tmp_path / "validation_report.json"
        validator.save_validation_report(str(output_path))

        assert output_path.exists()

        with open(output_path) as f:
            saved_data = json.load(f)

        assert saved_data["validation_passed"] is True
        assert saved_data["timestamp"] == "2024-01-01T00:00:00"

    def test_save_report_error_handling(self):
        """Test save report handles errors gracefully."""
        mock_notebookutils = MagicMock()
        validator = DeploymentValidator(workspace_id="test-workspace-id", notebookutils=mock_notebookutils)

        validator.validation_results = {"test": "data"}

        # Try to save to invalid path - should not raise
        validator.save_validation_report("/invalid/path/report.json")
