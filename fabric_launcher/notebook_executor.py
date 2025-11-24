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
                # Extract job ID from Location header (standard for 202 responses)
                job_id = "Unknown"
                location = response.headers.get("Location", "")

                if location:
                    # Location format: https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/items/{itemId}/jobs/instances/{jobId}
                    # Extract the job ID from the last segment
                    try:
                        job_id = location.rstrip("/").split("/")[-1]
                    except Exception:
                        job_id = "Unknown"

                # Fallback: try to parse JSON response if available
                if job_id == "Unknown" and response.text and response.text.strip():
                    try:
                        result = response.json()
                        job_id = result.get("id", "Unknown")
                    except Exception:
                        pass

                print("✅ Notebook execution triggered successfully")
                if job_id != "Unknown":
                    print(f"🆔 Job ID: {job_id}")
                else:
                    print("ℹ️ Job accepted - check notebook for execution status")

                return {
                    "success": True,
                    "job_id": job_id,
                    "notebook_id": notebook_id,
                    "notebook_name": notebook_name,
                    "workspace_id": target_workspace_id,
                    "location": location,
                }
            error_msg = f"Failed to trigger notebook execution: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)

        except Exception as e:
            print(f"❌ Error executing notebook: {e}")
            raise

    def run_notebook_synchronous(
        self, notebook_name: str, parameters: Optional[dict[str, Any]] = None, timeout_seconds: int = 3600
    ) -> dict[str, Any]:
        """
        Run a notebook synchronously (blocks until completion).

        Uses run_notebook to trigger execution and polls status until terminal state.

        Args:
            notebook_name: Name of the notebook to execute
            parameters: Dictionary of parameters to pass to the notebook
            timeout_seconds: Timeout for notebook execution (default: 3600)

        Returns:
            Dictionary with execution result information including final status

        Raises:
            Exception: If notebook execution fails or times out
        """
        import time

        try:
            print(f"🚀 Running notebook synchronously: {notebook_name}")

            # Trigger notebook execution
            result = self.run_notebook(
                notebook_name=notebook_name,
                parameters=parameters,
                timeout_seconds=timeout_seconds
            )

            job_id = result.get("job_id")
            notebook_id = result.get("notebook_id")
            location = result.get("location")

            if not job_id or job_id == "Unknown" or not location or not notebook_id:
                raise Exception("Could not retrieve job ID or notebook ID from notebook execution")

            # Monitor job status until terminal state
            terminal_statuses = ["Completed", "Failed", "Cancelled", "Canceled"]
            poll_interval = 5  # seconds
            elapsed_time = 0

            print(f"\n⏳ Monitoring job status (polling every {poll_interval} seconds)...")

            while elapsed_time < timeout_seconds:
                time.sleep(poll_interval)
                elapsed_time += poll_interval

                try:
                    status_data = self.get_job_status(
                        notebook_id=notebook_id,
                        job_id=job_id
                    )

                    current_status = status_data.get("status", "Unknown")
                    print(f"📊 Status: {current_status} (elapsed: {elapsed_time}s)")

                    # Check if job reached terminal status
                    if current_status in terminal_statuses:
                        print(f"\n🎯 Job reached terminal status: {current_status}")

                        # Display additional details
                        if "startTimeUtc" in status_data:
                            print(f"🕒 Start Time: {status_data['startTimeUtc']}")

                        # Show end time or current time if not available
                        end_time = status_data.get("endTimeUtc")
                        if end_time:
                            print(f"🕒 End Time: {end_time}")
                        else:
                            from datetime import datetime
                            current_time = datetime.utcnow().isoformat() + "Z"
                            print(f"🕒 End Time: {current_time} (estimated)")

                        if current_status == "Completed":
                            print("✅ Notebook execution completed successfully!")
                            return {
                                "success": True,
                                "status": current_status,
                                "notebook_name": notebook_name,
                                "job_id": job_id,
                                "status_data": status_data
                            }
                        # Failed, Cancelled, or Canceled
                        failure_reason = status_data.get("failureReason", "No reason provided")
                        print(f"❌ Failure Reason: {failure_reason}")
                        raise Exception(f"Notebook execution {current_status.lower()}: {failure_reason}")

                except Exception as status_error:
                    if "terminal status" in str(status_error) or "execution" in str(status_error):
                        # Re-raise execution failures
                        raise
                    # Log but continue on status check errors
                    print(f"⚠️ Error checking status: {status_error}")
                    continue

            # Timeout reached
            raise Exception(
                f"Notebook execution timed out after {timeout_seconds} seconds. "
                f"Job ID: {job_id}. Check status manually using get_job_status()."
            )

        except Exception as e:
            print(f"❌ Error running notebook synchronously: {e}")
            raise

    def get_job_status(self, notebook_id: str, job_id: str, workspace_id: Optional[str] = None) -> dict[str, Any]:
        """
        Get the status of a notebook job.

        Args:
            notebook_id: ID of the notebook (item ID)
            job_id: ID of the job instance
            workspace_id: Target workspace ID (uses current workspace if None)

        Returns:
            Dictionary with job status information
        """
        try:
            target_workspace_id = workspace_id or self.workspace_id

            # Use the item job instance endpoint (generic for all item types)
            url = f"v1/workspaces/{target_workspace_id}/items/{notebook_id}/jobs/instances/{job_id}"
            response = self.client.get(url)

            if response.status_code == 200:
                return response.json()
            raise Exception(f"Failed to get job status: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Error getting job status: {e}")
            raise


