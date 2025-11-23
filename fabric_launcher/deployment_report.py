"""
Deployment Report Module

This module provides functionality to generate comprehensive deployment reports.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class DeploymentReport:
    """
    Handler for generating deployment reports.

    Tracks deployment activities and generates summary reports.
    """

    def __init__(self):
        """Initialize the deployment report."""
        now = datetime.now()
        self.session_id = now.strftime("%Y%m%d_%H%M%S")
        self.timestamp = now.isoformat()
        self.start_time = now
        self.steps: List[Dict[str, Any]] = []
        self.deployed_items: List[Dict[str, Any]] = []

        self.report_data: Dict[str, Any] = {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "deployment_start": self.timestamp,
            "deployment_end": None,
            "deployment_duration_seconds": 0,
            "steps": self.steps,
            "items_deployed": self.deployed_items,
            "files_uploaded": [],
            "notebooks_executed": [],
            "errors": [],
            "warnings": [],
            "success": False,
        }

    def start_deployment(self, **kwargs) -> None:
        """Mark the start of deployment."""
        self.start_time = datetime.now()
        self.report_data["deployment_start"] = self.start_time.isoformat()
        self.report_data["config"] = kwargs

    def end_deployment(self, success: bool = True) -> None:
        """
        Mark the end of deployment.

        Args:
            success: Whether deployment was successful
        """
        end_time = datetime.now()
        self.report_data["deployment_end"] = end_time.isoformat()
        self.report_data["success"] = success

        duration = (end_time - self.start_time).total_seconds()
        self.report_data["deployment_duration_seconds"] = round(duration, 2)

    @property
    def duration_seconds(self) -> float:
        """Get deployment duration in seconds."""
        if self.report_data["deployment_end"]:
            return self.report_data["deployment_duration_seconds"]
        # Calculate current duration if deployment hasn't ended
        return round((datetime.now() - self.start_time).total_seconds(), 2)

    def add_step(self, step_name: str, status: str, details: Optional[str] = None) -> None:
        """
        Add a deployment step to the report.

        Args:
            step_name: Name of the step
            status: Status (success, warning, error)
            details: Optional details about the step
        """
        step = {
            "step_name": step_name,
            "name": step_name,  # Keep both for compatibility
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.steps.append(step)
        self.report_data["steps"] = self.steps

    def add_deployed_item(self, item_name: str, item_type: str, **kwargs) -> None:
        """
        Add a deployed item to the report.

        Args:
            item_name: Name of the item
            item_type: Type of the item
            **kwargs: Additional item details
        """
        item = {"name": item_name, "type": item_type, "timestamp": datetime.now().isoformat(), **kwargs}
        self.deployed_items.append(item)
        self.report_data["items_deployed"] = self.deployed_items

    def add_uploaded_files(self, lakehouse: str, folder: str, file_count: int) -> None:
        """
        Add uploaded files information to the report.

        Args:
            lakehouse: Lakehouse name
            folder: Target folder
            file_count: Number of files uploaded
        """
        self.report_data["files_uploaded"].append(
            {
                "lakehouse": lakehouse,
                "folder": folder,
                "file_count": file_count,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def add_notebook_execution(self, notebook_name: str, job_id: str, status: str = "triggered") -> None:
        """
        Add notebook execution information to the report.

        Args:
            notebook_name: Name of the notebook
            job_id: Job ID
            status: Execution status
        """
        self.report_data["notebooks_executed"].append(
            {"notebook": notebook_name, "job_id": job_id, "status": status, "timestamp": datetime.now().isoformat()}
        )

    def add_error(self, error: str, step: Optional[str] = None) -> None:
        """
        Add an error to the report.

        Args:
            error: Error message
            step: Optional step where error occurred
        """
        self.report_data["errors"].append({"message": error, "step": step, "timestamp": datetime.now().isoformat()})

    def add_warning(self, warning: str, step: Optional[str] = None) -> None:
        """
        Add a warning to the report.

        Args:
            warning: Warning message
            step: Optional step where warning occurred
        """
        self.report_data["warnings"].append({"message": warning, "step": step, "timestamp": datetime.now().isoformat()})

    def get_summary(self) -> Dict[str, Any]:
        """
        Get deployment summary.

        Returns:
            Dictionary with summary statistics
        """
        items_by_type = {}
        for item in self.report_data["items_deployed"]:
            item_type = item["type"]
            items_by_type[item_type] = items_by_type.get(item_type, 0) + 1

        total_files = sum(f["file_count"] for f in self.report_data["files_uploaded"])

        return {
            "success": self.report_data["success"],
            "duration_seconds": self.report_data["deployment_duration_seconds"],
            "total_items_deployed": len(self.report_data["items_deployed"]),
            "items_by_type": items_by_type,
            "total_files_uploaded": total_files,
            "notebooks_executed": len(self.report_data["notebooks_executed"]),
            "errors": len(self.report_data["errors"]),
            "warnings": len(self.report_data["warnings"]),
        }

    def print_report(self) -> None:
        """Print a formatted deployment report."""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT REPORT")
        print("=" * 60)

        # Status
        status_icon = "✅" if summary["success"] else "❌"
        status_text = "SUCCESS" if summary["success"] else "FAILED"
        print(f"\n{status_icon} Status: {status_text}")

        # Duration
        duration = summary["duration_seconds"]
        if duration >= 60:
            mins = int(duration // 60)
            secs = int(duration % 60)
            print(f"⏱️ Duration: {mins}m {secs}s")
        else:
            print(f"⏱️ Duration: {duration}s")

        # Items deployed
        if summary["total_items_deployed"] > 0:
            print(f"\n📦 Items Deployed: {summary['total_items_deployed']}")
            for item_type, count in summary["items_by_type"].items():
                print(f"  • {item_type}: {count}")

        # Files uploaded
        if summary["total_files_uploaded"] > 0:
            print(f"\n📁 Files Uploaded: {summary['total_files_uploaded']}")
            for file_info in self.report_data["files_uploaded"]:
                print(f"  • {file_info['lakehouse']}/Files/{file_info['folder']}: {file_info['file_count']} file(s)")

        # Notebooks executed
        if summary["notebooks_executed"] > 0:
            print(f"\n▶️ Notebooks Executed: {summary['notebooks_executed']}")
            for nb in self.report_data["notebooks_executed"]:
                print(f"  • {nb['notebook']} (Job ID: {nb['job_id']})")

        # Errors
        if summary["errors"] > 0:
            print(f"\n❌ Errors: {summary['errors']}")
            for error in self.report_data["errors"]:
                step_info = f" [{error['step']}]" if error["step"] else ""
                print(f"  • {error['message']}{step_info}")

        # Warnings
        if summary["warnings"] > 0:
            print(f"\n⚠️ Warnings: {summary['warnings']}")
            for warning in self.report_data["warnings"]:
                step_info = f" [{warning['step']}]" if warning["step"] else ""
                print(f"  • {warning['message']}{step_info}")

        # Steps
        if self.report_data["steps"]:
            print("\n📋 Deployment Steps:")
            for step in self.report_data["steps"]:
                icon = "✅" if step["status"] == "success" else "⚠️" if step["status"] == "warning" else "❌"
                print(f"  {icon} {step['name']}")
                if step["details"]:
                    print(f"      {step['details']}")

        print("\n" + "=" * 60)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report to dictionary.

        Returns:
            Dictionary representation of the report
        """
        return self.report_data.copy()

    def save_report(self, output_path: Optional[str] = None, format: str = "json") -> str:
        """
        Save the deployment report to a file.

        Args:
            output_path: Path to save the report (default: deployment_report_{session_id}.json)
            format: Output format ('json' or 'text')

        Returns:
            Path where report was saved
        """
        if output_path is None:
            ext = "json" if format == "json" else "txt"
            output_path = f"deployment_report_{self.session_id}.{ext}"

        try:
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            if format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(self.report_data, f, indent=2)
                print(f"✅ Deployment report saved to {output_path}")

            elif format == "text":
                with open(output_path, "w", encoding="utf-8") as f:
                    summary = self.get_summary()

                    f.write("=" * 60 + "\n")
                    f.write("DEPLOYMENT REPORT\n")
                    f.write("=" * 60 + "\n\n")

                    status_text = "SUCCESS" if summary["success"] else "FAILED"
                    f.write(f"Status: {status_text}\n")
                    f.write(f"Duration: {summary['duration_seconds']}s\n")
                    f.write(f"Items Deployed: {summary['total_items_deployed']}\n")
                    f.write(f"Files Uploaded: {summary['total_files_uploaded']}\n")
                    f.write(f"Notebooks Executed: {summary['notebooks_executed']}\n")
                    f.write(f"Errors: {summary['errors']}\n")
                    f.write(f"Warnings: {summary['warnings']}\n\n")

                    if summary["items_by_type"]:
                        f.write("Items by Type:\n")
                        for item_type, count in summary["items_by_type"].items():
                            f.write(f"  {item_type}: {count}\n")

                    f.write("\n" + "=" * 60 + "\n")

                print(f"✅ Deployment report saved to {output_path}")

            else:
                raise ValueError(f"Unsupported format: {format}")

            return output_path

        except Exception as e:
            print(f"❌ Error saving deployment report: {e}")
            raise
