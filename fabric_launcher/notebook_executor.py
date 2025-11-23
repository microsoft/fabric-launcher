"""
Notebook Executor Module

This module provides functionality to trigger execution of Fabric notebooks.
"""

from typing import Any, Optional

import sempy.fabric as fabric


class NotebookExecutor:
    """
    Handler for executing Fabric notebooks.

    This class provides methods to trigger and monitor notebook execution
    in a Fabric workspace.
    """

    def __init__(self, notebookutils):
        """
        Initialize the notebook executor.

        Args:
            notebookutils: The notebookutils module from Fabric notebook environment
        """
        self.notebookutils = notebookutils
        self.client = fabric.FabricRestClient()
        self.workspace_id = fabric.get_workspace_id()

    def run_notebook(
        self,
        notebook_name: str,
        workspace_id: Optional[str] = None,
        parameters: Optional[dict[str, Any]] = None,
        timeout_seconds: int = 3600,
    ) -> dict[str, Any]:
        """
        Trigger execution of a Fabric notebook.

        Args:
            notebook_name: Name of the notebook to execute
            workspace_id: Target workspace ID (uses current workspace if None)
            parameters: Dictionary of parameters to pass to the notebook
            timeout_seconds: Timeout for notebook execution (default: 3600)

        Returns:
            Dictionary with execution result information

        Raises:
            Exception: If notebook execution fails
        """
        try:
            target_workspace_id = workspace_id or self.workspace_id

            print(f"🚀 Triggering execution of notebook: {notebook_name}")
            print(f"📍 Workspace ID: {target_workspace_id}")

            # Resolve notebook ID
            notebook_id = fabric.resolve_item_id(notebook_name, "Notebook")
            print(f"📓 Notebook ID: {notebook_id}")

            # Prepare execution payload
            execution_payload = {}
            if parameters:
                print(f"📝 Parameters: {parameters}")
                execution_payload["parameters"] = parameters

            # Trigger notebook execution
            url = f"v1/workspaces/{target_workspace_id}/notebooks/{notebook_id}/jobs/instances?jobType=RunNotebook"

            response = self.client.post(url, json=execution_payload)

            if response.status_code in [200, 201, 202]:
                result = response.json()
                job_id = result.get("id", "Unknown")
                print("✅ Notebook execution triggered successfully")
                print(f"🆔 Job ID: {job_id}")

                return {
                    "success": True,
                    "job_id": job_id,
                    "notebook_id": notebook_id,
                    "notebook_name": notebook_name,
                    "workspace_id": target_workspace_id,
                }
            error_msg = f"Failed to trigger notebook execution: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)

        except Exception as e:
            print(f"❌ Error executing notebook: {e}")
            raise

    def run_notebook_synchronous(
        self, notebook_path: str, parameters: Optional[dict[str, Any]] = None, timeout_seconds: int = 3600
    ) -> dict[str, Any]:
        """
        Run a notebook synchronously using notebookutils (blocks until completion).

        Args:
            notebook_path: Path to the notebook (can be relative or absolute)
            parameters: Dictionary of parameters to pass to the notebook
            timeout_seconds: Timeout for notebook execution (default: 3600)

        Returns:
            Dictionary with execution result information

        Raises:
            Exception: If notebook execution fails
        """
        try:
            print(f"🚀 Running notebook synchronously: {notebook_path}")

            if parameters:
                print(f"📝 Parameters: {parameters}")
                result = self.notebookutils.notebook.run(notebook_path, timeout_seconds, parameters)
            else:
                result = self.notebookutils.notebook.run(notebook_path, timeout_seconds)

            print("✅ Notebook execution completed successfully")

            return {"success": True, "result": result, "notebook_path": notebook_path}

        except Exception as e:
            print(f"❌ Error running notebook: {e}")
            raise

    def get_job_status(self, notebook_id: str, job_id: str, workspace_id: Optional[str] = None) -> dict[str, Any]:
        """
        Get the status of a notebook job.

        Args:
            notebook_id: ID of the notebook
            job_id: ID of the job
            workspace_id: Target workspace ID (uses current workspace if None)

        Returns:
            Dictionary with job status information
        """
        try:
            target_workspace_id = workspace_id or self.workspace_id

            url = f"v1/workspaces/{target_workspace_id}/notebooks/{notebook_id}/jobs/instances/{job_id}"
            response = self.client.get(url)

            if response.status_code == 200:
                return response.json()
            raise Exception(f"Failed to get job status: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Error getting job status: {e}")
            raise

    def cancel_job(self, notebook_id: str, job_id: str, workspace_id: Optional[str] = None) -> bool:
        """
        Cancel a running notebook job.

        Args:
            notebook_id: ID of the notebook
            job_id: ID of the job
            workspace_id: Target workspace ID (uses current workspace if None)

        Returns:
            True if cancellation was successful
        """
        try:
            target_workspace_id = workspace_id or self.workspace_id

            print(f"🛑 Cancelling job: {job_id}")
            url = f"v1/workspaces/{target_workspace_id}/notebooks/{notebook_id}/jobs/instances/{job_id}/cancel"
            response = self.client.post(url, json={})

            if response.status_code in [200, 202]:
                print("✅ Job cancellation requested successfully")
                return True
            print(f"⚠️ Failed to cancel job: {response.status_code}")
            return False

        except Exception as e:
            print(f"❌ Error cancelling job: {e}")
            raise
