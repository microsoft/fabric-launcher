"""GitHub Repository Downloader Module

This module provides functionality to download and extract folders from GitHub repositories.
"""

__all__ = ["GitHubDownloader"]

import re
import shutil
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

import requests


class GitHubDownloader:
    """Handler for downloading and extracting GitHub repository content."""

    def __init__(self, repo_owner: str, repo_name: str, branch: str = "main", github_token: Optional[str] = None):
        """
        Initialize the GitHub downloader.

        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            branch: Git branch to download (default: "main")
            github_token: GitHub personal access token (optional, for private repos)
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.github_token = github_token

    def download_and_extract_folder(
        self, extract_to: str, folder_to_extract: str = "", remove_folder_prefix: str = ""
    ) -> None:
        """
        Download a GitHub repository and extract a specific folder directly to disk.

        Args:
            extract_to: Local directory to extract files to
            folder_to_extract: Folder path within the repo to extract (empty for entire repo)
            remove_folder_prefix: Prefix to remove from extracted file paths

        Raises:
            Exception: If download or extraction fails
        """
        try:
            # Construct the URL for the GitHub API to download the repository as a zip file
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/zipball/{self.branch}"

            # Set up headers for authentication if a token is provided
            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
                headers["Accept"] = "application/vnd.github.v3+json"

            print(f"📥 Downloading {self.repo_name} from {self.repo_owner}/{self.repo_name}:{self.branch}")

            # Make a request to the GitHub API
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # Delete target directory if exists
            extract_path = Path(extract_to)
            if extract_path.exists() and extract_path.is_dir():
                shutil.rmtree(extract_to)
                print(f"🗑️ Deleted existing directory: {extract_to}")

            # Ensure the extraction directory exists
            extract_path.mkdir(parents=True, exist_ok=True)

            # Process the zip file directly from memory
            with zipfile.ZipFile(BytesIO(response.content)) as zipf:
                for file_info in zipf.infolist():
                    # Normalize the path
                    normalized_path = re.sub(r"^.*?/", "/", file_info.filename)

                    # If folder_to_extract is specified, only extract files from that folder
                    if folder_to_extract and not normalized_path.startswith(f"/{folder_to_extract}"):
                        continue

                    # Calculate the output path
                    parts = file_info.filename.split("/")
                    relative_path = "/".join(parts[1:])  # Remove repo root folder

                    # Remove the specified prefix if provided
                    if remove_folder_prefix:
                        relative_path = relative_path.replace(remove_folder_prefix, "", 1)

                    output_path = Path(extract_to) / relative_path

                    # Skip if it's a directory entry
                    if file_info.filename.endswith("/"):
                        output_path.mkdir(parents=True, exist_ok=True)
                        continue

                    # Ensure the directory for the file exists
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    # Extract and write the file
                    with zipf.open(file_info) as source_file, open(str(output_path), "wb") as target_file:
                        target_file.write(source_file.read())

            folder_desc = f"'{folder_to_extract}' folder" if folder_to_extract else "repository"
            print(f"✅ Successfully extracted {folder_desc} to {extract_to}")

        except Exception as e:
            error_msg = (
                f"A {type(e).__name__} error occurred while downloading from GitHub. "
                f"This error may be intermittent. Error: {str(e)}"
            )
            print(f"❌ {error_msg}")
            raise

    def download_file(self, file_path: str, target_directory: str) -> str:
        """
        Download a single file from a GitHub repository.

        Args:
            file_path: File path within the repo to download
            target_directory: Directory where to save the file

        Returns:
            Path to the downloaded file

        Raises:
            Exception: If download fails
        """
        file_url = (
            f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/refs/heads/{self.branch}/{file_path}"
        )
        file_name = file_url.split("/")[-1]

        try:
            # Create target directory if it doesn't exist
            Path(target_directory).mkdir(parents=True, exist_ok=True)

            # Set up headers for authentication if a token is provided
            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
                headers["Accept"] = "application/vnd.github.v3+json"

            # Download the file
            print(f"📥 Downloading file from {file_url}")
            response = requests.get(file_url, headers=headers)
            response.raise_for_status()

            # Save to target directory
            target_path = str(Path(target_directory) / file_name)
            with open(target_path, "wb") as f:
                f.write(response.content)

            print(f"✅ File saved successfully to {target_path}")
            return target_path

        except requests.RequestException as e:
            print(f"❌ Error downloading file: {e}")
            raise
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            raise
