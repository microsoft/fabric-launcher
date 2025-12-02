"""
Platform File Fixer Module

This module provides functionality to fix duplicate logicalIds in .platform files
for Fabric items before deployment. Replaces zero GUIDs with unique identifiers.
"""

import json
import os
import uuid
from pathlib import Path
from typing import Any

__all__ = ["PlatformFileFixer"]


class PlatformFileFixer:
    """
    Handler for fixing duplicate logicalIds in Fabric .platform files.

    Fabric .platform files can sometimes contain duplicate logicalIds with all zeros
    (00000000-0000-0000-0000-000000000000), which causes deployment errors.
    This class scans for these files and replaces zero GUIDs with unique identifiers.
    """

    ZERO_GUID = "00000000-0000-0000-0000-000000000000"

    def __init__(self, repository_directory: str):
        """
        Initialize the platform file fixer.

        Args:
            repository_directory: Root directory containing Fabric item definitions
        """
        self.repository_directory = repository_directory

    def find_platform_files(self) -> list[str]:
        """
        Find all .platform files in the repository directory.

        Returns:
            List of absolute paths to .platform files
        """
        platform_files = []
        repo_path = Path(self.repository_directory)

        # Recursively find all .platform files
        for platform_file in repo_path.rglob("*.platform"):
            platform_files.append(str(platform_file.absolute()))

        return platform_files

    def check_platform_file(self, file_path: str) -> tuple[bool, dict]:
        """
        Check if a .platform file contains a zero GUID logicalId.

        Args:
            file_path: Path to the .platform file

        Returns:
            Tuple of (has_zero_guid, file_data)
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Check if logicalId exists and is a zero GUID
            logical_id = data.get("config", {}).get("logicalId")
            has_zero_guid = logical_id == self.ZERO_GUID

            return has_zero_guid, data

        except json.JSONDecodeError as e:
            print(f"⚠️ Warning: Failed to parse {file_path}: {e}")
            return False, {}
        except Exception as e:
            print(f"⚠️ Warning: Failed to read {file_path}: {e}")
            return False, {}

    def fix_platform_file(self, file_path: str, dry_run: bool = False) -> bool:
        """
        Fix a .platform file by replacing zero GUID with a unique GUID.

        Args:
            file_path: Path to the .platform file
            dry_run: If True, only report what would be changed without modifying files

        Returns:
            True if file was fixed (or would be fixed in dry_run), False otherwise
        """
        has_zero_guid, data = self.check_platform_file(file_path)

        if not has_zero_guid:
            return False

        # Generate a new unique GUID
        new_guid = str(uuid.uuid4())

        if dry_run:
            print(f"  [DRY RUN] Would replace logicalId in {file_path}")
            print(f"    Old: {self.ZERO_GUID}")
            print(f"    New: {new_guid}")
            return True

        # Replace the logicalId
        data["config"]["logicalId"] = new_guid

        try:
            # Write back to file with proper formatting
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")  # Add trailing newline

            print(f"  ✅ Fixed {file_path}")
            print(f"    Old logicalId: {self.ZERO_GUID}")
            print(f"    New logicalId: {new_guid}")
            return True

        except Exception as e:
            print(f"  ❌ Failed to fix {file_path}: {e}")
            return False

    def scan_and_fix_all(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Scan all .platform files and fix any with zero GUIDs.

        Args:
            dry_run: If True, only report what would be changed without modifying files

        Returns:
            Dictionary with scan results including:
            - total_files: Total number of .platform files found
            - files_with_zero_guid: Number of files with zero GUID
            - files_fixed: Number of files successfully fixed
            - fixed_files: List of file paths that were fixed
        """
        print("🔍 Scanning for .platform files with duplicate logicalIds...")
        print(f"📂 Repository directory: {self.repository_directory}")

        # Find all .platform files
        platform_files = self.find_platform_files()
        print(f"📋 Found {len(platform_files)} .platform file(s)")

        if not platform_files:
            print("✅ No .platform files found")
            return {
                "total_files": 0,
                "files_with_zero_guid": 0,
                "files_fixed": 0,
                "fixed_files": [],
            }

        # Check each file for zero GUIDs
        files_with_zero_guid = []
        for file_path in platform_files:
            has_zero_guid, _ = self.check_platform_file(file_path)
            if has_zero_guid:
                files_with_zero_guid.append(file_path)

        if not files_with_zero_guid:
            print("✅ All .platform files have valid logicalIds")
            return {
                "total_files": len(platform_files),
                "files_with_zero_guid": 0,
                "files_fixed": 0,
                "fixed_files": [],
            }

        # Report findings
        print(f"\n⚠️ Found {len(files_with_zero_guid)} file(s) with zero GUID logicalId:")
        for file_path in files_with_zero_guid:
            rel_path = os.path.relpath(file_path, self.repository_directory)
            print(f"  • {rel_path}")

        if dry_run:
            print(f"\n[DRY RUN MODE] Would fix {len(files_with_zero_guid)} file(s)")
        else:
            print(f"\n🔧 Fixing {len(files_with_zero_guid)} file(s)...")

        # Fix the files
        fixed_files = []
        for file_path in files_with_zero_guid:
            rel_path = os.path.relpath(file_path, self.repository_directory)
            if self.fix_platform_file(file_path, dry_run=dry_run):
                fixed_files.append(rel_path)

        # Summary
        if not dry_run:
            print(f"\n✅ Fixed {len(fixed_files)} out of {len(files_with_zero_guid)} file(s)")
        else:
            print(f"\n[DRY RUN] Would have fixed {len(fixed_files)} file(s)")

        return {
            "total_files": len(platform_files),
            "files_with_zero_guid": len(files_with_zero_guid),
            "files_fixed": len(fixed_files),
            "fixed_files": fixed_files,
        }
