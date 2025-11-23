"""
File Operations Module

This module provides functionality to upload files to Fabric Lakehouse Files area.
Supports copying files from local repository folders to Lakehouse.
"""

import os
import shutil
from pathlib import Path
from typing import Optional


class LakehouseFileManager:
    """
    Handler for managing files in Fabric Lakehouse Files area.

    This class provides methods to upload files from a local directory
    or GitHub repository to a Lakehouse Files folder.
    """

    def __init__(self, notebookutils):
        """
        Initialize the file manager.

        Args:
            notebookutils: The notebookutils module from Fabric notebook environment
        """
        self.notebookutils = notebookutils

    def upload_files_to_lakehouse(
        self,
        lakehouse_name: str,
        source_directory: str,
        target_folder: str = "data",
        file_patterns: Optional[list[str]] = None,
    ) -> None:
        """
        Upload files from a local directory to a Lakehouse Files folder.

        Args:
            lakehouse_name: Name of the target Lakehouse
            source_directory: Local directory containing files to upload
            target_folder: Target folder path in Lakehouse Files area (default: "data")
            file_patterns: List of file patterns to match (e.g., ["*.json", "*.csv"])
                          If None, all files are uploaded
        """
        try:
            # Get abfs path to the lakehouse and mount it
            print(f"📁 Accessing Lakehouse: {lakehouse_name}")
            abfs_path = self.notebookutils.lakehouse.getWithProperties(lakehouse_name).properties["abfsPath"]
            mount_point = f"/{lakehouse_name}"

            # Mount the lakehouse
            self.notebookutils.fs.mount(abfs_path, mount_point)
            print(f"✅ Mounted Lakehouse to {mount_point}")

            # Construct target directory path
            target_directory = self.notebookutils.fs.getMountPath(mount_point) + f"/Files/{target_folder}/"

            # Create target directory if it doesn't exist
            Path(target_directory).mkdir(parents=True, exist_ok=True)
            print(f"📂 Target directory: {target_directory}")

            # Upload files
            uploaded_count = 0
            for root, _dirs, files in os.walk(source_directory):
                for file in files:
                    # Check if file matches any pattern (if patterns specified)
                    if file_patterns and not any(self._matches_pattern(file, pattern) for pattern in file_patterns):
                        continue

                    source_path = str(Path(root) / file)
                    target_path = str(Path(target_directory) / file)

                    # Copy file
                    shutil.copy2(source_path, target_path)
                    print(f"  ✓ Uploaded: {file}")
                    uploaded_count += 1

            print(f"✅ Successfully uploaded {uploaded_count} file(s) to {lakehouse_name}/Files/{target_folder}")

        except Exception as e:
            print(f"❌ Error uploading files to Lakehouse: {e}")
            raise

    def upload_file_to_lakehouse(self, lakehouse_name: str, file_path: str, target_folder: str = "data") -> None:
        """
        Upload a single file to a Lakehouse Files folder.

        Args:
            lakehouse_name: Name of the target Lakehouse
            file_path: Path to the file to upload
            target_folder: Target folder path in Lakehouse Files area (default: "data")
        """
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Get abfs path to the lakehouse and mount it
            print(f"📁 Accessing Lakehouse: {lakehouse_name}")
            abfs_path = self.notebookutils.lakehouse.getWithProperties(lakehouse_name).properties["abfsPath"]
            mount_point = f"/{lakehouse_name}"

            # Mount the lakehouse
            self.notebookutils.fs.mount(abfs_path, mount_point)

            # Construct target directory path
            target_directory = self.notebookutils.fs.getMountPath(mount_point) + f"/Files/{target_folder}/"

            # Create target directory if it doesn't exist
            Path(target_directory).mkdir(parents=True, exist_ok=True)

            # Get file name
            file_name = Path(file_path).name
            target_path = str(Path(target_directory) / file_name)

            # Copy file
            shutil.copy2(file_path, target_path)
            print(f"✅ File uploaded successfully: {file_name} -> {lakehouse_name}/Files/{target_folder}")

        except Exception as e:
            print(f"❌ Error uploading file to Lakehouse: {e}")
            raise

    def copy_folder_to_lakehouse(
        self,
        lakehouse_name: str,
        source_folder: str,
        target_folder: str = "data",
        file_patterns: Optional[list[str]] = None,
        recursive: bool = True,
    ) -> None:
        """
        Copy an entire folder structure from local repository to Lakehouse Files area.

        Args:
            lakehouse_name: Name of the target Lakehouse
            source_folder: Local folder path to copy from
            target_folder: Target folder path in Lakehouse Files area (default: "data")
            file_patterns: List of file patterns to match (e.g., ["*.json", "*.csv"])
                          If None, all files are copied
            recursive: Whether to copy subdirectories recursively
        """
        try:
            if not Path(source_folder).exists():
                raise FileNotFoundError(f"Source folder not found: {source_folder}")

            # Get abfs path to the lakehouse and mount it
            print(f"📁 Accessing Lakehouse: {lakehouse_name}")
            abfs_path = self.notebookutils.lakehouse.getWithProperties(lakehouse_name).properties["abfsPath"]
            mount_point = f"/{lakehouse_name}"

            # Mount the lakehouse
            self.notebookutils.fs.mount(abfs_path, mount_point)
            print(f"✅ Mounted Lakehouse to {mount_point}")

            # Construct target directory path
            target_directory = self.notebookutils.fs.getMountPath(mount_point) + f"/Files/{target_folder}/"

            # Create target directory if it doesn't exist
            Path(target_directory).mkdir(parents=True, exist_ok=True)
            print(f"📂 Target directory: {target_directory}")

            # Copy files and folders
            copied_count = 0

            if recursive:
                # Walk through all subdirectories
                for root, _dirs, files in os.walk(source_folder):
                    # Calculate relative path from source folder
                    rel_path = os.path.relpath(root, source_folder)

                    # Create corresponding directory in target
                    if rel_path != ".":
                        target_subdir = str(Path(target_directory) / rel_path)
                        Path(target_subdir).mkdir(parents=True, exist_ok=True)
                    else:
                        target_subdir = target_directory

                    # Copy files
                    for file in files:
                        # Check if file matches any pattern (if patterns specified)
                        if file_patterns and not any(self._matches_pattern(file, pattern) for pattern in file_patterns):
                            continue

                        source_path = str(Path(root) / file)
                        target_path = str(Path(target_subdir) / file)

                        # Copy file
                        shutil.copy2(source_path, target_path)

                        # Show relative path for clarity
                        rel_file_path = str(Path(rel_path) / file) if rel_path != "." else file
                        print(f"  ✓ Copied: {rel_file_path}")
                        copied_count += 1
            else:
                # Only copy files in the root of source folder
                for item in Path(source_folder).iterdir():
                    file_path = str(item)

                    # Skip directories
                    if item.is_dir():
                        continue

                    file = item.name

                    # Check if file matches any pattern (if patterns specified)
                    if file_patterns and not any(self._matches_pattern(file, pattern) for pattern in file_patterns):
                        continue

                    target_path = str(Path(target_directory) / file)

                    # Copy file
                    shutil.copy2(file_path, target_path)
                    print(f"  ✓ Copied: {file}")
                    copied_count += 1

            print(f"✅ Successfully copied {copied_count} file(s) to {lakehouse_name}/Files/{target_folder}")

        except Exception as e:
            print(f"❌ Error copying folder to Lakehouse: {e}")
            raise

    def copy_multiple_folders_to_lakehouse(
        self,
        lakehouse_name: str,
        folder_mappings: dict[str, str],
        file_patterns: Optional[list[str]] = None,
        recursive: bool = True,
    ) -> None:
        """
        Copy multiple folders from local repository to Lakehouse Files area.

        Args:
            lakehouse_name: Name of the target Lakehouse
            folder_mappings: Dictionary mapping source folders to target folders
                            e.g., {"./local/data1": "data1", "./local/data2": "data2"}
            file_patterns: List of file patterns to match (e.g., ["*.json", "*.csv"])
                          If None, all files are copied
            recursive: Whether to copy subdirectories recursively
        """
        print(f"📦 Copying {len(folder_mappings)} folder(s) to Lakehouse: {lakehouse_name}")
        print("=" * 60)

        for source_folder, target_folder in folder_mappings.items():
            print(f"\n📁 Processing: {source_folder} → {target_folder}")

            try:
                self.copy_folder_to_lakehouse(
                    lakehouse_name=lakehouse_name,
                    source_folder=source_folder,
                    target_folder=target_folder,
                    file_patterns=file_patterns,
                    recursive=recursive,
                )
            except FileNotFoundError as e:
                print(f"⚠️ Warning: {e}")
                print(f"   Skipping folder: {source_folder}")
                continue
            except Exception as e:
                print(f"❌ Error processing folder {source_folder}: {e}")
                raise

        print("\n" + "=" * 60)
        print(f"✅ Completed copying all folders to {lakehouse_name}")

    def download_and_copy_folders_to_lakehouse(
        self,
        lakehouse_name: str,
        github_downloader,
        repository_base_path: str,
        folder_mappings: dict[str, str],
        file_patterns: Optional[list[str]] = None,
        recursive: bool = True,
    ) -> None:
        """
        Download folders from GitHub repository and copy them to Lakehouse.

        This method assumes the repository has already been downloaded and extracted.
        It copies data folders from the local repository to the Lakehouse.

        Args:
            lakehouse_name: Name of the target Lakehouse
            github_downloader: Instance of GitHubDownloader (for consistency)
            repository_base_path: Base path where repository was extracted
            folder_mappings: Dictionary mapping repository folders to Lakehouse folders
                            e.g., {"data": "reference-data", "samples": "sample-data"}
                            Keys are relative to repository_base_path
            file_patterns: List of file patterns to match (e.g., ["*.json", "*.csv"])
            recursive: Whether to copy subdirectories recursively
        """
        print(f"📦 Copying data folders from repository to Lakehouse: {lakehouse_name}")
        print(f"📂 Repository base path: {repository_base_path}")
        print("=" * 60)

        # Build full source paths
        full_folder_mappings = {}
        for repo_folder, lakehouse_folder in folder_mappings.items():
            source_path = str(Path(repository_base_path) / repo_folder)
            full_folder_mappings[source_path] = lakehouse_folder

        # Copy all folders
        self.copy_multiple_folders_to_lakehouse(
            lakehouse_name=lakehouse_name,
            folder_mappings=full_folder_mappings,
            file_patterns=file_patterns,
            recursive=recursive,
        )

    @staticmethod
    def _matches_pattern(filename: str, pattern: str) -> bool:
        """
        Check if a filename matches a pattern.

        Args:
            filename: Name of the file
            pattern: Pattern to match (e.g., "*.json")

        Returns:
            True if filename matches pattern
        """
        import fnmatch

        return fnmatch.fnmatch(filename, pattern)
