"""
Unit tests for DeploymentReport module.
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
import json
from datetime import datetime

from fabric_launcher.deployment_report import DeploymentReport


class TestDeploymentReport(unittest.TestCase):
    """Test cases for DeploymentReport class."""

    def setUp(self):
        """Set up test fixtures."""
        self.report = DeploymentReport()

    def test_initialization(self):
        """Test DeploymentReport initialization."""
        self.assertIsNotNone(self.report.session_id)
        self.assertIsNotNone(self.report.timestamp)
        self.assertIsNotNone(self.report.start_time)
        self.assertEqual(len(self.report.steps), 0)
        self.assertEqual(len(self.report.deployed_items), 0)

    def test_session_id_format(self):
        """Test session ID format."""
        # Session ID should be in format YYYYMMDD_HHMMSS
        self.assertRegex(self.report.session_id, r"\d{8}_\d{6}")

    def test_add_step(self):
        """Test adding a step to the report."""
        self.report.add_step("Test Step", "Started", "Test details")

        self.assertEqual(len(self.report.steps), 1)
        step = self.report.steps[0]
        self.assertEqual(step["step_name"], "Test Step")
        self.assertEqual(step["status"], "Started")
        self.assertEqual(step["details"], "Test details")
        self.assertIn("timestamp", step)

    def test_add_multiple_steps(self):
        """Test adding multiple steps."""
        self.report.add_step("Step 1", "Started", "Details 1")
        self.report.add_step("Step 2", "Completed", "Details 2")
        self.report.add_step("Step 3", "Failed", "Details 3")

        self.assertEqual(len(self.report.steps), 3)
        self.assertEqual(self.report.steps[0]["step_name"], "Step 1")
        self.assertEqual(self.report.steps[1]["step_name"], "Step 2")
        self.assertEqual(self.report.steps[2]["step_name"], "Step 3")

    def test_add_deployed_item(self):
        """Test adding a deployed item to the report."""
        self.report.add_deployed_item(item_name="TestLakehouse", item_type="Lakehouse", status="Success")

        self.assertEqual(len(self.report.deployed_items), 1)
        item = self.report.deployed_items[0]
        self.assertEqual(item["name"], "TestLakehouse")
        self.assertEqual(item["type"], "Lakehouse")
        self.assertEqual(item["status"], "Success")
        self.assertIn("timestamp", item)

    def test_add_deployed_item_with_details(self):
        """Test adding deployed item with details."""
        self.report.add_deployed_item(
            item_name="TestNotebook", item_type="Notebook", status="Failed", details="Connection timeout"
        )

        item = self.report.deployed_items[0]
        self.assertEqual(item["details"], "Connection timeout")

    def test_duration_seconds(self):
        """Test duration calculation."""
        import time

        # Wait a small amount to ensure duration > 0
        time.sleep(0.1)

        duration = self.report.duration_seconds
        self.assertGreater(duration, 0)
        self.assertIsInstance(duration, float)

    def test_save_report(self):
        """Test saving report to JSON file."""
        self.report.add_step("Test Step", "Completed", "Test details")
        self.report.add_deployed_item(item_name="TestItem", item_type="Notebook", status="Success")

        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "test_report.json")
            self.report.save_report(report_path)

            # Verify file was created
            self.assertTrue(os.path.exists(report_path))

            # Verify content is valid JSON
            with open(report_path, "r") as f:
                saved_data = json.load(f)

            self.assertEqual(saved_data["session_id"], self.report.session_id)
            self.assertEqual(len(saved_data["steps"]), 1)
            self.assertEqual(len(saved_data["items_deployed"]), 1)

    def test_save_report_creates_directory(self):
        """Test that save_report creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "subdir", "report.json")
            self.report.save_report(nested_path)

            # Verify file was created in nested directory
            self.assertTrue(os.path.exists(nested_path))

    @patch("builtins.print")
    def test_print_report(self, mock_print):
        """Test printing report summary."""
        self.report.add_step("Download", "Completed", "Downloaded successfully")
        self.report.add_step("Deployment", "Started", "Deploying items")
        self.report.add_deployed_item("TestLH", "Lakehouse", status="Success")

        self.report.print_report()

        # Verify print was called
        self.assertTrue(mock_print.called)

        # Check that key information was printed
        printed_text = " ".join([str(call[0][0]) for call in mock_print.call_args_list])
        self.assertIn("DEPLOYMENT REPORT", printed_text)
        # Note: session_id is not printed in the current implementation

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        self.report.add_step("Test Step", "Completed", "Details")
        self.report.add_deployed_item("Item", "Type", status="Success")

        report_dict = self.report.to_dict()

        self.assertIn("session_id", report_dict)
        self.assertIn("timestamp", report_dict)
        self.assertIn("deployment_duration_seconds", report_dict)
        self.assertIn("steps", report_dict)
        self.assertIn("items_deployed", report_dict)
        self.assertEqual(len(report_dict["steps"]), 1)
        self.assertEqual(len(report_dict["items_deployed"]), 1)


class TestDeploymentReportEdgeCases(unittest.TestCase):
    """Test edge cases for DeploymentReport."""

    def test_empty_report(self):
        """Test report with no steps or items."""
        report = DeploymentReport()

        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "empty_report.json")
            report.save_report(report_path)

            with open(report_path, "r") as f:
                saved_data = json.load(f)

            self.assertEqual(len(saved_data["steps"]), 0)
            self.assertEqual(len(saved_data["items_deployed"]), 0)

    def test_special_characters_in_details(self):
        """Test handling special characters in step details."""
        report = DeploymentReport()

        special_details = "Error: File 'test.json' not found!\nPath: C:\\Users\\test"
        report.add_step("Test", "Failed", special_details)

        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "report.json")
            report.save_report(report_path)

            # Verify it can be loaded back
            with open(report_path, "r") as f:
                saved_data = json.load(f)

            self.assertEqual(saved_data["steps"][0]["details"], special_details)

    def test_none_details(self):
        """Test adding items with None details."""
        report = DeploymentReport()
        report.add_deployed_item("Item", "Type", status="Success", details=None)

        item = report.deployed_items[0]
        self.assertIsNone(item["details"])


if __name__ == "__main__":
    unittest.main()
