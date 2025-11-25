"""
Tests for the LakehouseFileManager class in file_operations module.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from fabric_launcher.file_operations import LakehouseFileManager


class TestLakehouseFileManagerInit:
    """Tests for LakehouseFileManager initialization."""

    def test_initialization(self):
        """Test basic initialization."""
        mock_notebookutils = MagicMock()
        manager = LakehouseFileManager(mock_notebookutils)
        assert manager.notebookutils == mock_notebookutils


class TestMatchesPattern:
    """Tests for the _matches_pattern static method."""

    def test_matches_json_pattern(self):
        """Test matching .json files."""
        assert LakehouseFileManager._matches_pattern("data.json", "*.json") is True
        assert LakehouseFileManager._matches_pattern("data.csv", "*.json") is False

    def test_matches_csv_pattern(self):
        """Test matching .csv files."""
        assert LakehouseFileManager._matches_pattern("report.csv", "*.csv") is True
        assert LakehouseFileManager._matches_pattern("report.json", "*.csv") is False

    def test_matches_wildcard(self):
        """Test matching with wildcard pattern."""
        assert LakehouseFileManager._matches_pattern("any_file.txt", "*") is True
        assert LakehouseFileManager._matches_pattern("test_file.py", "test_*") is True
        assert LakehouseFileManager._matches_pattern("main_file.py", "test_*") is False

    def test_matches_exact_name(self):
        """Test matching exact filename."""
        assert LakehouseFileManager._matches_pattern("config.yaml", "config.yaml") is True
        assert LakehouseFileManager._matches_pattern("other.yaml", "config.yaml") is False


class TestUploadFilesToLakehouse:
    """Tests for upload_files_to_lakehouse method."""

    def test_upload_files_error_handling(self):
        """Test error handling during upload."""
        mock_notebookutils = MagicMock()
        mock_notebookutils.lakehouse.getWithProperties.side_effect = Exception("Lakehouse not found")

        manager = LakehouseFileManager(mock_notebookutils)

        with pytest.raises(Exception, match="Lakehouse not found"):
            manager.upload_files_to_lakehouse(
                lakehouse_name="NonExistent",
                source_directory="/fake/path",
                target_folder="data"
            )


class TestUploadFileToLakehouse:
    """Tests for upload_file_to_lakehouse method."""

    def test_upload_single_file_success(self):
        """Test successful single file upload."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "single.json"
            test_file.write_text('{"single": true}')

            # Create mock
            mock_notebookutils = MagicMock()
            mock_notebookutils.lakehouse.getWithProperties.return_value.properties = {
                "abfsPath": "abfss://container@storage.dfs.core.windows.net/"
            }
            mock_notebookutils.fs.getMountPath.return_value = temp_dir

            manager = LakehouseFileManager(mock_notebookutils)

            # Create target directory
            target_dir = Path(temp_dir) / "Files" / "data"
            target_dir.mkdir(parents=True, exist_ok=True)

            # Execute
            manager.upload_file_to_lakehouse(
                lakehouse_name="TestLakehouse",
                file_path=str(test_file),
                target_folder="data"
            )

            # Verify
            mock_notebookutils.fs.mount.assert_called_once()

    def test_upload_single_file_not_found(self):
        """Test error when file doesn't exist."""
        mock_notebookutils = MagicMock()
        manager = LakehouseFileManager(mock_notebookutils)

        with pytest.raises(FileNotFoundError, match="File not found"):
            manager.upload_file_to_lakehouse(
                lakehouse_name="TestLakehouse",
                file_path="/nonexistent/file.json",
                target_folder="data"
            )


class TestCopyFolderToLakehouse:
    """Tests for copy_folder_to_lakehouse method."""

    def test_copy_folder_recursive(self):
        """Test recursive folder copy."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source structure
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            (source_dir / "root.json").write_text('{"root": true}')

            subdir = source_dir / "subdir"
            subdir.mkdir()
            (subdir / "nested.json").write_text('{"nested": true}')

            # Create mock
            mock_notebookutils = MagicMock()
            mock_notebookutils.lakehouse.getWithProperties.return_value.properties = {
                "abfsPath": "abfss://container@storage.dfs.core.windows.net/"
            }
            mock_notebookutils.fs.getMountPath.return_value = temp_dir

            manager = LakehouseFileManager(mock_notebookutils)

            # Create target directory
            target_dir = Path(temp_dir) / "Files" / "data"
            target_dir.mkdir(parents=True, exist_ok=True)

            # Execute
            manager.copy_folder_to_lakehouse(
                lakehouse_name="TestLakehouse",
                source_folder=str(source_dir),
                target_folder="data",
                recursive=True
            )

            # Verify
            mock_notebookutils.fs.mount.assert_called_once()

    def test_copy_folder_non_recursive(self):
        """Test non-recursive folder copy."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source structure
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            (source_dir / "root.json").write_text('{"root": true}')

            subdir = source_dir / "subdir"
            subdir.mkdir()
            (subdir / "nested.json").write_text('{"nested": true}')

            # Create mock
            mock_notebookutils = MagicMock()
            mock_notebookutils.lakehouse.getWithProperties.return_value.properties = {
                "abfsPath": "abfss://container@storage.dfs.core.windows.net/"
            }
            mock_notebookutils.fs.getMountPath.return_value = temp_dir

            manager = LakehouseFileManager(mock_notebookutils)

            # Create target directory
            target_dir = Path(temp_dir) / "Files" / "data"
            target_dir.mkdir(parents=True, exist_ok=True)

            # Execute
            manager.copy_folder_to_lakehouse(
                lakehouse_name="TestLakehouse",
                source_folder=str(source_dir),
                target_folder="data",
                recursive=False
            )

            # Only root level files should be copied (not subdir contents)
            mock_notebookutils.fs.mount.assert_called_once()

    def test_copy_folder_not_found(self):
        """Test error when source folder doesn't exist."""
        mock_notebookutils = MagicMock()
        manager = LakehouseFileManager(mock_notebookutils)

        with pytest.raises(FileNotFoundError, match="Source folder not found"):
            manager.copy_folder_to_lakehouse(
                lakehouse_name="TestLakehouse",
                source_folder="/nonexistent/folder",
                target_folder="data"
            )


class TestCopyMultipleFoldersToLakehouse:
    """Tests for copy_multiple_folders_to_lakehouse method."""

    def test_copy_multiple_folders_success(self):
        """Test copying multiple folders."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source folders
            folder1 = Path(temp_dir) / "folder1"
            folder1.mkdir()
            (folder1 / "file1.json").write_text('{"folder": 1}')

            folder2 = Path(temp_dir) / "folder2"
            folder2.mkdir()
            (folder2 / "file2.json").write_text('{"folder": 2}')

            # Create mock
            mock_notebookutils = MagicMock()
            mock_notebookutils.lakehouse.getWithProperties.return_value.properties = {
                "abfsPath": "abfss://container@storage.dfs.core.windows.net/"
            }
            mock_notebookutils.fs.getMountPath.return_value = temp_dir

            manager = LakehouseFileManager(mock_notebookutils)

            # Create target directories
            (Path(temp_dir) / "Files" / "target1").mkdir(parents=True, exist_ok=True)
            (Path(temp_dir) / "Files" / "target2").mkdir(parents=True, exist_ok=True)

            # Execute
            folder_mappings = {
                str(folder1): "target1",
                str(folder2): "target2"
            }

            manager.copy_multiple_folders_to_lakehouse(
                lakehouse_name="TestLakehouse",
                folder_mappings=folder_mappings
            )

            # Verify mount was called multiple times
            assert mock_notebookutils.fs.mount.call_count == 2

    def test_copy_multiple_folders_skip_missing(self):
        """Test that missing folders are skipped with warning."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create only one folder
            folder1 = Path(temp_dir) / "folder1"
            folder1.mkdir()
            (folder1 / "file1.json").write_text('{"folder": 1}')

            # Create mock
            mock_notebookutils = MagicMock()
            mock_notebookutils.lakehouse.getWithProperties.return_value.properties = {
                "abfsPath": "abfss://container@storage.dfs.core.windows.net/"
            }
            mock_notebookutils.fs.getMountPath.return_value = temp_dir

            manager = LakehouseFileManager(mock_notebookutils)

            # Create target directory
            (Path(temp_dir) / "Files" / "target1").mkdir(parents=True, exist_ok=True)

            # Execute with one missing folder
            folder_mappings = {
                str(folder1): "target1",
                "/nonexistent/folder": "target2"  # This doesn't exist
            }

            # Should not raise, just skip the missing folder
            manager.copy_multiple_folders_to_lakehouse(
                lakehouse_name="TestLakehouse",
                folder_mappings=folder_mappings
            )


class TestDownloadAndCopyFoldersToLakehouse:
    """Tests for download_and_copy_folders_to_lakehouse method."""

    def test_download_and_copy_success(self):
        """Test download and copy workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create repository structure
            repo_base = Path(temp_dir) / "repo"
            repo_base.mkdir()

            data_folder = repo_base / "data"
            data_folder.mkdir()
            (data_folder / "data.json").write_text('{"data": true}')

            # Create mock
            mock_notebookutils = MagicMock()
            mock_notebookutils.lakehouse.getWithProperties.return_value.properties = {
                "abfsPath": "abfss://container@storage.dfs.core.windows.net/"
            }
            mock_notebookutils.fs.getMountPath.return_value = temp_dir

            mock_github_downloader = MagicMock()

            manager = LakehouseFileManager(mock_notebookutils)

            # Create target directory
            (Path(temp_dir) / "Files" / "lakehouse-data").mkdir(parents=True, exist_ok=True)

            # Execute
            folder_mappings = {"data": "lakehouse-data"}

            manager.download_and_copy_folders_to_lakehouse(
                lakehouse_name="TestLakehouse",
                github_downloader=mock_github_downloader,
                repository_base_path=str(repo_base),
                folder_mappings=folder_mappings
            )

            # Verify
            mock_notebookutils.fs.mount.assert_called_once()
