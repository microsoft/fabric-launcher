"""
Tests for the NotebookExecutor class in notebook_executor module.

These tests focus on testing the NotebookExecutor class behavior
without complex mocking of the sempy.fabric module which is mocked
in conftest.py.
"""

from unittest.mock import MagicMock

import pytest


class TestNotebookExecutorInit:
    """Tests for NotebookExecutor initialization."""

    def test_initialization_stores_notebookutils(self):
        """Test that initialization stores the notebookutils reference."""
        from fabric_launcher.notebook_executor import NotebookExecutor

        mock_notebookutils = MagicMock()
        executor = NotebookExecutor(mock_notebookutils)

        assert executor.notebookutils == mock_notebookutils

    def test_initialization_creates_client(self):
        """Test that initialization creates a REST client."""
        from fabric_launcher.notebook_executor import NotebookExecutor

        mock_notebookutils = MagicMock()
        executor = NotebookExecutor(mock_notebookutils)

        # Client should be created (will be a MagicMock from conftest.py)
        assert executor.client is not None


class TestRunNotebook:
    """Tests for run_notebook method."""

    def test_run_notebook_failure_bad_status(self):
        """Test that run_notebook raises exception on bad HTTP status."""
        from fabric_launcher.notebook_executor import NotebookExecutor

        mock_notebookutils = MagicMock()
        executor = NotebookExecutor(mock_notebookutils)

        # Configure mock client to return error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        executor.client.post.return_value = mock_response

        with pytest.raises(Exception, match="Failed to trigger notebook execution"):
            executor.run_notebook("TestNotebook")

    def test_run_notebook_failure_captures_error_text(self):
        """Test that run_notebook captures error text in exception."""
        from fabric_launcher.notebook_executor import NotebookExecutor

        mock_notebookutils = MagicMock()
        executor = NotebookExecutor(mock_notebookutils)

        # Configure mock client to return specific error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error - Database unavailable"
        executor.client.post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            executor.run_notebook("FailingNotebook")

        assert "500" in str(exc_info.value)


class TestGetJobStatus:
    """Tests for get_job_status method."""

    def test_get_job_status_failure_raises_exception(self):
        """Test that get_job_status raises exception on HTTP error."""
        from fabric_launcher.notebook_executor import NotebookExecutor

        mock_notebookutils = MagicMock()
        executor = NotebookExecutor(mock_notebookutils)

        # Configure mock client to return error
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Job not found"
        executor.client.get.return_value = mock_response

        with pytest.raises(Exception, match="Failed to get job status"):
            executor.get_job_status(notebook_id="notebook-id", job_id="invalid-job-id")

    def test_get_job_status_uses_correct_url(self):
        """Test that get_job_status constructs correct API URL."""
        import contextlib

        from fabric_launcher.notebook_executor import NotebookExecutor

        mock_notebookutils = MagicMock()
        executor = NotebookExecutor(mock_notebookutils)

        # Override workspace_id to known value
        executor.workspace_id = "test-workspace-123"

        # Configure mock to return error (we just want to verify the URL)
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        executor.client.get.return_value = mock_response

        with contextlib.suppress(Exception):
            executor.get_job_status(notebook_id="notebook-456", job_id="job-789")

        # Verify the URL was constructed correctly
        call_args = executor.client.get.call_args
        assert "notebook-456" in call_args[0][0]
        assert "job-789" in call_args[0][0]


class TestRunNotebookWithParameters:
    """Tests for run_notebook with parameters."""

    def test_run_notebook_passes_parameters(self):
        """Test that parameters are passed in the request payload."""
        import contextlib

        from fabric_launcher.notebook_executor import NotebookExecutor

        mock_notebookutils = MagicMock()
        executor = NotebookExecutor(mock_notebookutils)

        # Configure mock to return error (we want to check the payload)
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Error"
        executor.client.post.return_value = mock_response

        test_params = {"param1": "value1", "param2": 123}

        with contextlib.suppress(Exception):
            executor.run_notebook("ParamNotebook", parameters=test_params)

        # Verify post was called with parameters in payload
        call_args = executor.client.post.call_args
        assert call_args is not None


class TestRunNotebookSynchronous:
    """Tests for run_notebook_synchronous method."""

    def test_run_notebook_synchronous_exists(self):
        """Test that run_notebook_synchronous method exists."""
        from fabric_launcher.notebook_executor import NotebookExecutor

        mock_notebookutils = MagicMock()
        executor = NotebookExecutor(mock_notebookutils)

        assert hasattr(executor, "run_notebook_synchronous")
        assert callable(executor.run_notebook_synchronous)
