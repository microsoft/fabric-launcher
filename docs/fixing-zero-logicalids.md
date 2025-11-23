# Fixing Zero GUID LogicalIds in .platform Files

## Problem

When deploying Fabric items, you may encounter the following error:

```
FailedPublishedItemStatusError: Duplicate logicalId '00000000-0000-0000-0000-000000000000'
```

This error occurs when `.platform` files contain zero GUIDs (`00000000-0000-0000-0000-000000000000`) as their `logicalId`. Each Fabric item must have a unique `logicalId`, and zero GUIDs are treated as duplicates.

## Solution

The `fabric-launcher` package now includes automatic detection and fixing of zero GUID logicalIds. This feature is **enabled by default** and will automatically replace any zero GUIDs with unique identifiers before deployment.

## Configuration

### Option 1: Using Configuration Files

Add the `fix_zero_logical_ids` parameter to your deployment configuration:

**YAML Configuration:**
```yaml
deployment:
  environment: "DEV"
  staged_deployment: true
  fix_zero_logical_ids: true  # Default: true
  allow_non_empty_workspace: false
```

**JSON Configuration:**
```json
{
  "deployment": {
    "environment": "DEV",
    "staged_deployment": true,
    "fix_zero_logical_ids": true,
    "allow_non_empty_workspace": false
  }
}
```

### Option 2: Direct Initialization

When initializing `FabricLauncher`:

```python
from fabric_launcher import FabricLauncher

# Enable automatic fixing (default behavior)
launcher = FabricLauncher(
    notebookutils=notebookutils,
    fix_zero_logical_ids=True  # This is the default
)

# Disable automatic fixing (not recommended)
launcher = FabricLauncher(
    notebookutils=notebookutils,
    fix_zero_logical_ids=False
)
```

### Option 3: Direct FabricDeployer Usage

If you're using `FabricDeployer` directly:

```python
from fabric_launcher.fabric_deployer import FabricDeployer

deployer = FabricDeployer(
    workspace_id="your-workspace-id",
    repository_directory="/path/to/workspace",
    notebookutils=notebookutils,
    fix_zero_logical_ids=True  # Default: True
)

deployer.deploy_items()
```

## How It Works

1. **Before Deployment**: The system scans all `.platform` files in your repository
2. **Detection**: Identifies any files with `logicalId` set to `00000000-0000-0000-0000-000000000000`
3. **Replacement**: Automatically generates unique GUIDs for each duplicate
4. **Logging**: Reports which files were fixed

### Example Output

```
🔧 Checking for zero GUID logicalIds in .platform files...
📂 Repository directory: /lakehouse/default/Files/workspace
📋 Found 5 .platform file(s)

⚠️ Found 2 file(s) with zero GUID logicalId:
  • MyLakehouse.Lakehouse/.platform
  • MyNotebook.Notebook/.platform

🔧 Fixing 2 file(s)...
  ✅ Fixed MyLakehouse.Lakehouse/.platform
    Old logicalId: 00000000-0000-0000-0000-000000000000
    New logicalId: a1b2c3d4-5678-90ab-cdef-1234567890ab
  ✅ Fixed MyNotebook.Notebook/.platform
    Old logicalId: 00000000-0000-0000-0000-000000000000
    New logicalId: e5f6g7h8-9012-34ij-klmn-5678901234op

✅ Fixed 2 .platform file(s) with zero GUID logicalIds
```

## Manual Inspection

If you want to inspect files without modifying them, use the standalone fixer with dry-run mode:

```python
from fabric_launcher.platform_file_fixer import PlatformFileFixer

# Initialize fixer
fixer = PlatformFileFixer("/path/to/workspace")

# Scan without making changes
results = fixer.scan_and_fix_all(dry_run=True)

print(f"Total files: {results['total_files']}")
print(f"Files with zero GUID: {results['files_with_zero_guid']}")
print(f"Files that would be fixed: {results['files_fixed']}")
```

## Disabling the Feature

If you need to disable automatic fixing (not recommended):

```python
# Via FabricLauncher
launcher = FabricLauncher(
    notebookutils=notebookutils,
    fix_zero_logical_ids=False
)

# Via configuration file
# deployment:
#   fix_zero_logical_ids: false
```

When disabled, you'll see:
```
⚠️ Skipping logicalId validation (fix_zero_logical_ids=False)
```

## Best Practices

1. **Keep Enabled (Default)**: Leave `fix_zero_logical_ids=True` to prevent deployment errors
2. **Version Control**: Commit the fixed `.platform` files to prevent future issues
3. **Review Changes**: After first fix, review the updated files to ensure GUIDs are unique
4. **Team Coordination**: Ensure team members understand why `.platform` files may be modified

## Troubleshooting

### Issue: Files are being fixed on every deployment

**Solution**: Commit the fixed `.platform` files to your repository. The fixer only modifies files with zero GUIDs, so once fixed and committed, they won't be modified again.

### Issue: Still getting logicalId errors

**Possible causes**:
1. Feature is disabled - ensure `fix_zero_logical_ids=True`
2. Files are readonly - check file permissions
3. Invalid `.platform` file format - check JSON syntax

**Debug steps**:
```python
# Enable debug logging
launcher = FabricLauncher(
    notebookutils=notebookutils,
    debug=True,
    fix_zero_logical_ids=True
)
```

## Technical Details

### .platform File Structure

A typical `.platform` file contains:
```json
{
  "config": {
    "version": "1.0",
    "logicalId": "12345678-1234-1234-1234-123456789012"
  },
  "metadata": {
    "displayName": "My Lakehouse"
  }
}
```

The `logicalId` must be:
- A valid UUID/GUID format
- Unique across all items in the workspace
- Not `00000000-0000-0000-0000-000000000000`

### Why Zero GUIDs Occur

Zero GUIDs can appear in `.platform` files due to:
- Template generation tools
- Copy-paste operations
- Manual file creation
- Export/import processes

The automatic fixer ensures these are replaced before deployment.
