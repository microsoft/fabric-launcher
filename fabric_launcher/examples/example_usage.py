"""Example usage of fabric-launcher package in a Fabric notebook."""

# Cell 1: Package Installation
print("📦 Installing fabric-launcher package...")
# %pip install fabric-launcher --quiet
# %pip install --upgrade azure-core azure-identity --quiet

# Cell 2: Restart Kernel
# print("⚠️ Restarting Python kernel for installed packages to take effect")
# notebookutils.session.restartPython()

# Cell 3: Configuration
# Define your deployment configuration
REPO_OWNER = "myorg"
REPO_NAME = "my-fabric-solution"
BRANCH = "main"
FOLDER_TO_EXTRACT = "workspace"
ENVIRONMENT = "DEV"
DEBUG = False

# Optional: GitHub token for private repositories
GITHUB_TOKEN = ""

# Cell 4: Import and Initialize
import notebookutils

from fabric_launcher import FabricLauncher

# Initialize the launcher
# By default, deployment is only allowed to empty workspaces
launcher = FabricLauncher(
    notebookutils,
    environment=ENVIRONMENT,
    debug=DEBUG,
    allow_non_empty_workspace=False,  # Set to True to deploy to non-empty workspace
)

print("✅ Launcher initialized")
print(f"📍 Workspace ID: {launcher.workspace_id}")
print(f"🏷️ Environment: {launcher.environment}")

# Cell 5: Option A - All-in-One Deployment with Data Upload
# Download and deploy in one operation, including data folders
print("=" * 60)
print("🚀 Starting All-in-One Deployment")
print("=" * 60)

launcher.download_and_deploy(
    repo_owner=REPO_OWNER,
    repo_name=REPO_NAME,
    workspace_folder=FOLDER_TO_EXTRACT,
    branch=BRANCH,
    github_token=GITHUB_TOKEN if GITHUB_TOKEN else None,
    staged_deployment=True,  # Deploy data stores first, then compute
    data_folders={"data": "reference-data", "samples": "sample-data"},
    lakehouse_name="ReferenceDataLH",
    data_file_patterns=["*.json", "*.csv", "*.geojson"],
)

print("✅ Deployment completed!")

# Cell 6: Option B - Step-by-Step Deployment (Alternative to Cell 5)
# Step 1: Download from GitHub
print("\n📥 Step 1: Downloading from GitHub...")
launcher.download_repository(
    repo_owner=REPO_OWNER,
    repo_name=REPO_NAME,
    extract_to=".lakehouse/default/Files/src",
    folder_to_extract=FOLDER_TO_EXTRACT,
    branch=BRANCH,
    github_token=GITHUB_TOKEN if GITHUB_TOKEN else None,
)

# Step 2: Deploy artifacts
print("\n🚀 Step 2: Deploying artifacts...")
import os

repository_directory = os.path.join(".lakehouse/default/Files/src", FOLDER_TO_EXTRACT)

launcher.deploy_artifacts(
    repository_directory=repository_directory
    # item_types=["Lakehouse", "Notebook"]  # Optional: specify item types
)

print("✅ Deployment completed!")

# Cell 7: Upload Reference Data from Local Files
# Upload files from a local directory to Lakehouse
launcher.upload_files_to_lakehouse(
    lakehouse_name="ReferenceDataLH",
    source_directory="./local-data",
    target_folder="reference-data",
    file_patterns=["*.json", "*.csv"],  # Optional: filter by pattern
)

# Cell 8: Copy Data Folders to Lakehouse
# Copy data folders from the downloaded repository to Lakehouse
import os

repository_base_path = os.path.join(".lakehouse/default/Files/src")

launcher.copy_data_folders_to_lakehouse(
    lakehouse_name="ReferenceDataLH",
    repository_base_path=repository_base_path,
    folder_mappings={"data": "reference-data", "samples": "sample-data"},
    file_patterns=["*.json", "*.geojson", "*.csv"],
    recursive=True,
)

# Cell 9: Execute Post-Deployment Notebook (Asynchronous)
# Trigger a notebook to run asynchronously
result = launcher.run_notebook(
    notebook_name="Initialize-Reference-Data", parameters={"environment": ENVIRONMENT, "data_folder": "reference-data"}
)

print("✅ Notebook execution triggered")
print(f"🆔 Job ID: {result['job_id']}")
print(f"📓 Notebook ID: {result['notebook_id']}")

# Cell 10: Execute Notebook Synchronously (Alternative to Cell 9)
# Run a notebook and wait for completion
result = launcher.run_notebook_sync(
    notebook_path="Initialize-Reference-Data",
    parameters={"environment": ENVIRONMENT, "data_folder": "reference-data"},
    timeout_seconds=3600,
)

print("✅ Notebook execution completed")
print(f"📊 Result: {result['result']}")

# Cell 11: Check Notebook Job Status
# Check the status of an asynchronous notebook job
if "job_id" in result and "notebook_id" in result:
    status = launcher.get_notebook_job_status(notebook_id=result["notebook_id"], job_id=result["job_id"])
    print(f"Job Status: {status}")

# Cell 12: Advanced - Using Individual Components
# You can also use individual components directly for more control

from fabric_launcher import FabricDeployer, GitHubDownloader, LakehouseFileManager, NotebookExecutor

# GitHub operations
downloader = GitHubDownloader(REPO_OWNER, REPO_NAME, branch=BRANCH)
downloader.download_and_extract_folder(extract_to="./src", folder_to_extract=FOLDER_TO_EXTRACT)

# Fabric deployment
deployer = FabricDeployer(
    workspace_id=launcher.workspace_id,
    repository_directory="./src/workspace",
    notebookutils=notebookutils,
    environment=ENVIRONMENT,
)
deployer.deploy_all_in_stages()

# File operations
file_mgr = LakehouseFileManager(notebookutils)
file_mgr.upload_files_to_lakehouse(lakehouse_name="MyLH", source_directory="./data", target_folder="raw")

# Notebook execution
executor = NotebookExecutor(notebookutils)
result = executor.run_notebook("MyNotebook")

print("✅ Advanced deployment completed!")
