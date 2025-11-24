"""
Example: Accessing FabricLauncher Internal Properties

This example demonstrates how to access internal properties of the FabricLauncher
object for post-deployment activities like custom validation, data processing,
or integration with other tools.
"""

from fabric_launcher import FabricLauncher

# Initialize the launcher (in Fabric, notebookutils would be available)
# For this example, we'll use None as a placeholder
notebookutils = None  # In Fabric notebooks, this is automatically available

launcher = FabricLauncher(
    notebookutils=notebookutils,
    workspace_id="your-workspace-id",
    environment="dev",
    config_file="deployment_config.yaml",
)

# Download and deploy artifacts
# launcher.download_and_deploy(
#     repo_owner="your-org",
#     repo_name="your-repo",
#     branch="main"
# )

# ============================================================================
# Accessing Internal Properties After Deployment
# ============================================================================

# 1. Get the path where the repository was extracted
print("\n📂 Repository Path:")
if launcher.repository_path:
    print(f"   Repository extracted to: {launcher.repository_path}")

    # Use this for custom file operations
    from pathlib import Path

    repo_path = Path(launcher.repository_path)

    # Example: Check if a specific file exists
    readme_path = repo_path / "README.md"
    if readme_path.exists():
        print(f"   ✅ Found README at: {readme_path}")
else:
    print("   ⚠️  Repository not yet downloaded")

# 2. Get the workspace directory path
print("\n📁 Workspace Directory:")
if launcher.workspace_directory:
    print(f"   Workspace artifacts in: {launcher.workspace_directory}")

    # Use this to access deployed artifact definitions
    from pathlib import Path

    workspace_path = Path(launcher.workspace_directory)

    # Example: List all notebook definitions
    notebooks_path = workspace_path / "Notebooks"
    if notebooks_path.exists():
        notebook_files = list(notebooks_path.glob("*.Notebook"))
        print(f"   Found {len(notebook_files)} notebook definitions")
else:
    print("   ⚠️  Workspace not yet deployed")

# 3. Get deployment configuration
print("\n⚙️  Deployment Configuration:")
config = launcher.deployment_config
if config:
    print(f"   GitHub: {config.get('github', {})}")
    print(f"   Deployment settings: {config.get('deployment', {})}")
    print(f"   Data configuration: {config.get('data', {})}")

    # Use configuration for custom validation
    github_config = config.get("github", {})
    if github_config:
        repo = f"{github_config.get('repo_owner')}/{github_config.get('repo_name')}"
        print(f"   Source repository: {repo}")
else:
    print("   ⚠️  No configuration loaded")

# 4. Access specific data folder paths
print("\n📊 Data Folder Paths:")
data_folder = launcher.get_data_folder_path("data")
if data_folder:
    print(f"   Data folder: {data_folder}")

    # Use this for custom data processing
    from pathlib import Path

    data_path = Path(data_folder)

    # Example: Count CSV files
    csv_files = list(data_path.glob("**/*.csv"))
    print(f"   Found {len(csv_files)} CSV files")
else:
    print("   ⚠️  Data folder not found")

# 5. List all folders in the repository
print("\n📋 Repository Folders:")
folders = launcher.list_data_folders()
if folders:
    print(f"   Available folders: {', '.join(folders)}")

    # Use this to discover available data or configuration directories
    for folder in folders:
        folder_path = launcher.get_data_folder_path(folder)
        if folder_path:
            print(f"   - {folder}: {folder_path}")
else:
    print("   ⚠️  No folders found")

# ============================================================================
# Use Cases for Post-Deployment Activities
# ============================================================================

print("\n\n🎯 Example Use Cases:")
print("""
1. Custom Data Validation:
   - Access repository_path to read raw data files
   - Validate data quality before processing
   - Generate custom validation reports

2. Integration with External Tools:
   - Export workspace_directory path to CI/CD systems
   - Trigger external data pipelines
   - Archive deployment artifacts

3. Custom Reporting:
   - Read deployment_config to generate deployment summaries
   - Track which repository version was deployed
   - Compare configurations across environments

4. Data Processing:
   - Use get_data_folder_path() to access downloaded data
   - Process files before loading to lakehouses
   - Apply transformations or enrichment

5. Advanced Workflows:
   - Chain multiple deployments
   - Implement custom rollback logic
   - Build deployment orchestration systems
""")
