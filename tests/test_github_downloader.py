"""
Unit tests for GitHubDownloader module.
"""

import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from fabric_launcher.github_downloader import GitHubDownloader


class TestGitHubDownloader(unittest.TestCase):
    """Test cases for GitHubDownloader class."""

    def setUp(self):
        """Set up test fixtures."""
        self.repo_owner = "test-owner"
        self.repo_name = "test-repo"
        self.branch = "main"
        self.github_token = "test-token"

    def test_initialization(self):
        """Test GitHubDownloader initialization."""
        downloader = GitHubDownloader(
            repo_owner=self.repo_owner, repo_name=self.repo_name, branch=self.branch, github_token=self.github_token
        )

        self.assertEqual(downloader.repo_owner, self.repo_owner)
        self.assertEqual(downloader.repo_name, self.repo_name)
        self.assertEqual(downloader.branch, self.branch)
        self.assertEqual(downloader.github_token, self.github_token)

    def test_initialization_without_token(self):
        """Test GitHubDownloader initialization without token."""
        downloader = GitHubDownloader(repo_owner=self.repo_owner, repo_name=self.repo_name)

        self.assertEqual(downloader.repo_owner, self.repo_owner)
        self.assertEqual(downloader.repo_name, self.repo_name)
        self.assertEqual(downloader.branch, "main")
        self.assertIsNone(downloader.github_token)

    @patch("fabric_launcher.github_downloader.requests.get")
    def test_download_repository_success(self, mock_get):
        """Test successful repository download."""
        # Create a valid zip file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            zipf.writestr("test-repo-main/test_file.txt", "test content")

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = zip_buffer.getvalue()
        mock_get.return_value = mock_response

        downloader = GitHubDownloader(repo_owner=self.repo_owner, repo_name=self.repo_name)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Use public API method
            downloader.download_and_extract_folder(temp_dir)

            # Verify the download was called with correct URL
            expected_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/zipball/main"
            mock_get.assert_called_once()
            call_args_str = str(mock_get.call_args)
            self.assertIn(expected_url, call_args_str)

            # Verify extraction occurred (directory exists and file was extracted)
            self.assertTrue(Path(temp_dir).exists())
            self.assertTrue((Path(temp_dir) / "test_file.txt").exists())

    @patch("fabric_launcher.github_downloader.requests.get")
    def test_download_repository_with_token(self, mock_get):
        """Test repository download with authentication token."""
        # Create a valid zip file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            zipf.writestr("test-repo-main/test_file.txt", "test content")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = zip_buffer.getvalue()
        mock_get.return_value = mock_response

        downloader = GitHubDownloader(
            repo_owner=self.repo_owner, repo_name=self.repo_name, github_token=self.github_token
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            downloader.download_and_extract_folder(temp_dir)

            # Verify token was included in headers
            call_kwargs = mock_get.call_args.kwargs
            self.assertIn("headers", call_kwargs)
            self.assertEqual(call_kwargs["headers"]["Authorization"], f"token {self.github_token}")

    @patch("fabric_launcher.github_downloader.requests.get")
    def test_download_repository_404_error(self, mock_get):
        """Test repository download with 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        downloader = GitHubDownloader(repo_owner=self.repo_owner, repo_name=self.repo_name)

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(Exception) as context:
                downloader.download_and_extract_folder(temp_dir)

            self.assertIn("404", str(context.exception))

    @patch("fabric_launcher.github_downloader.requests.get")
    def test_extract_folder_path_filtering(self, mock_get):
        """Test extraction with folder path filtering."""
        downloader = GitHubDownloader(repo_owner=self.repo_owner, repo_name=self.repo_name)

        # Create a mock zip file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            zipf.writestr("test-repo-main/workspace/file1.txt", "content1")
            zipf.writestr("test-repo-main/workspace/file2.txt", "content2")
            zipf.writestr("test-repo-main/data/file3.txt", "content3")

        # Mock the response with the zip content
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = zip_buffer.getvalue()
        mock_get.return_value = mock_response

        # Extract only workspace folder using public API
        with tempfile.TemporaryDirectory() as extract_to:
            downloader.download_and_extract_folder(extract_to=extract_to, folder_to_extract="workspace")

            # Verify only workspace files were extracted
            # The public API removes the repo prefix, so files should be at workspace/file1.txt
            self.assertTrue((Path(extract_to) / "workspace" / "file1.txt").exists())
            self.assertTrue((Path(extract_to) / "workspace" / "file2.txt").exists())
            self.assertFalse((Path(extract_to) / "data").exists())


class TestGitHubDownloaderIntegration(unittest.TestCase):
    """Integration tests for GitHubDownloader."""

    @patch("fabric_launcher.github_downloader.requests.get")
    @patch("fabric_launcher.github_downloader.zipfile.ZipFile")
    def test_download_and_extract_workflow(self, mock_zipfile, mock_get):
        """Test complete download and extract workflow."""
        # Mock successful download
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake zip content"
        mock_get.return_value = mock_response

        # Mock zip extraction
        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
        mock_zip_instance.namelist.return_value = [
            "test-repo-main/workspace/file1.txt",
            "test-repo-main/workspace/subdir/file2.txt",
        ]

        downloader = GitHubDownloader(repo_owner="test-owner", repo_name="test-repo")

        with tempfile.TemporaryDirectory() as temp_dir:
            downloader.download_and_extract_folder(extract_to=temp_dir, folder_to_extract="workspace")

            # Verify download was called
            mock_get.assert_called_once()

            # Verify extraction was attempted
            mock_zipfile.assert_called()


if __name__ == "__main__":
    unittest.main()
