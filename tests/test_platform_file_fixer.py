"""
Unit tests for PlatformFileFixer module.
"""

import json
import tempfile
import unittest
from pathlib import Path

from fabric_launcher.platform_file_fixer import PlatformFileFixer


class TestPlatformFileFixer(unittest.TestCase):
    """Test cases for PlatformFileFixer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.zero_guid = "00000000-0000-0000-0000-000000000000"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def create_platform_file(self, filename: str, logical_id: str) -> str:
        """Helper to create a .platform file with specified logicalId."""
        file_path = str(Path(self.temp_dir) / filename)

        # Create directory if needed
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        platform_data = {
            "config": {"version": "1.0", "logicalId": logical_id},
            "metadata": {"displayName": "Test Item"},
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(platform_data, f, indent=2)

        return file_path

    def test_initialization(self):
        """Test PlatformFileFixer initialization."""
        fixer = PlatformFileFixer(self.temp_dir)
        self.assertEqual(fixer.repository_directory, self.temp_dir)
        self.assertEqual(fixer.ZERO_GUID, self.zero_guid)

    def test_find_platform_files_empty(self):
        """Test finding platform files in empty directory."""
        fixer = PlatformFileFixer(self.temp_dir)
        files = fixer.find_platform_files()
        self.assertEqual(len(files), 0)

    def test_find_platform_files(self):
        """Test finding platform files."""
        # Create some .platform files
        self.create_platform_file("item1.platform", "valid-guid-1")
        self.create_platform_file("subdir/item2.platform", "valid-guid-2")

        fixer = PlatformFileFixer(self.temp_dir)
        files = fixer.find_platform_files()

        self.assertEqual(len(files), 2)
        # Verify both files are found
        file_names = [Path(f).name for f in files]
        self.assertIn("item1.platform", file_names)
        self.assertIn("item2.platform", file_names)

    def test_check_platform_file_with_zero_guid(self):
        """Test checking a platform file with zero GUID."""
        file_path = self.create_platform_file("test.platform", self.zero_guid)

        fixer = PlatformFileFixer(self.temp_dir)
        has_zero_guid, data = fixer.check_platform_file(file_path)

        self.assertTrue(has_zero_guid)
        self.assertEqual(data["config"]["logicalId"], self.zero_guid)

    def test_check_platform_file_with_valid_guid(self):
        """Test checking a platform file with valid GUID."""
        valid_guid = "12345678-1234-1234-1234-123456789012"
        file_path = self.create_platform_file("test.platform", valid_guid)

        fixer = PlatformFileFixer(self.temp_dir)
        has_zero_guid, data = fixer.check_platform_file(file_path)

        self.assertFalse(has_zero_guid)
        self.assertEqual(data["config"]["logicalId"], valid_guid)

    def test_fix_platform_file_with_zero_guid(self):
        """Test fixing a platform file with zero GUID."""
        file_path = self.create_platform_file("test.platform", self.zero_guid)

        fixer = PlatformFileFixer(self.temp_dir)
        result = fixer.fix_platform_file(file_path, dry_run=False)

        self.assertTrue(result)

        # Verify the file was updated
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        new_guid = data["config"]["logicalId"]
        self.assertNotEqual(new_guid, self.zero_guid)
        # Verify it's a valid GUID format (has dashes in right places)
        self.assertEqual(len(new_guid), 36)
        self.assertEqual(new_guid.count("-"), 4)

    def test_fix_platform_file_dry_run(self):
        """Test fixing a platform file in dry run mode."""
        file_path = self.create_platform_file("test.platform", self.zero_guid)

        fixer = PlatformFileFixer(self.temp_dir)
        result = fixer.fix_platform_file(file_path, dry_run=True)

        self.assertTrue(result)

        # Verify the file was NOT updated
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["config"]["logicalId"], self.zero_guid)

    def test_fix_platform_file_with_valid_guid(self):
        """Test fixing a platform file with valid GUID (should not change)."""
        valid_guid = "12345678-1234-1234-1234-123456789012"
        file_path = self.create_platform_file("test.platform", valid_guid)

        fixer = PlatformFileFixer(self.temp_dir)
        result = fixer.fix_platform_file(file_path, dry_run=False)

        self.assertFalse(result)

        # Verify the file was not changed
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["config"]["logicalId"], valid_guid)

    def test_scan_and_fix_all_no_files(self):
        """Test scan_and_fix_all with no platform files."""
        fixer = PlatformFileFixer(self.temp_dir)
        results = fixer.scan_and_fix_all()

        self.assertEqual(results["total_files"], 0)
        self.assertEqual(results["files_with_zero_guid"], 0)
        self.assertEqual(results["files_fixed"], 0)
        self.assertEqual(len(results["fixed_files"]), 0)

    def test_scan_and_fix_all_with_valid_files(self):
        """Test scan_and_fix_all with only valid GUIDs."""
        self.create_platform_file("item1.platform", "valid-guid-1")
        self.create_platform_file("item2.platform", "valid-guid-2")

        fixer = PlatformFileFixer(self.temp_dir)
        results = fixer.scan_and_fix_all()

        self.assertEqual(results["total_files"], 2)
        self.assertEqual(results["files_with_zero_guid"], 0)
        self.assertEqual(results["files_fixed"], 0)
        self.assertEqual(len(results["fixed_files"]), 0)

    def test_scan_and_fix_all_with_zero_guids(self):
        """Test scan_and_fix_all with some zero GUIDs."""
        self.create_platform_file("item1.platform", self.zero_guid)
        self.create_platform_file("item2.platform", "valid-guid")
        self.create_platform_file("subdir/item3.platform", self.zero_guid)

        fixer = PlatformFileFixer(self.temp_dir)
        results = fixer.scan_and_fix_all()

        self.assertEqual(results["total_files"], 3)
        self.assertEqual(results["files_with_zero_guid"], 2)
        self.assertEqual(results["files_fixed"], 2)
        self.assertEqual(len(results["fixed_files"]), 2)

        # Verify the files were actually fixed
        for filename in ["item1.platform", "subdir/item3.platform"]:
            file_path = str(Path(self.temp_dir) / filename)
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            self.assertNotEqual(data["config"]["logicalId"], self.zero_guid)

    def test_scan_and_fix_all_dry_run(self):
        """Test scan_and_fix_all in dry run mode."""
        self.create_platform_file("item1.platform", self.zero_guid)
        self.create_platform_file("item2.platform", "valid-guid")

        fixer = PlatformFileFixer(self.temp_dir)
        results = fixer.scan_and_fix_all(dry_run=True)

        self.assertEqual(results["total_files"], 2)
        self.assertEqual(results["files_with_zero_guid"], 1)
        self.assertEqual(results["files_fixed"], 1)

        # Verify the file was NOT changed
        file_path = str(Path(self.temp_dir) / "item1.platform")
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["config"]["logicalId"], self.zero_guid)

    def test_invalid_json_file(self):
        """Test handling of invalid JSON in platform file."""
        file_path = str(Path(self.temp_dir) / "invalid.platform")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("not valid json {")

        fixer = PlatformFileFixer(self.temp_dir)
        has_zero_guid, data = fixer.check_platform_file(file_path)

        self.assertFalse(has_zero_guid)
        self.assertEqual(data, {})


if __name__ == "__main__":
    unittest.main()
