# Metadata Management

Zarr metadata management is crucial for performance and data integrity. This guide covers how to use zarr-utils to manage, validate, and repair Zarr metadata.

## Understanding Zarr Metadata

### What is Consolidated Metadata?

Zarr stores metadata about arrays (shape, dtype, chunks, etc.) in separate files. For remote stores, accessing these files individually is slow. Consolidated metadata (`.zmetadata` file) combines all metadata into a single file for efficient access.

### Why is it Important?

- **Performance**: One read instead of potentially hundreds
- **Reliability**: Ensures metadata consistency
- **Compatibility**: Required by some tools and libraries

## Core Functions

### consolidate_metadata

Creates or updates consolidated metadata for a Zarr store.

```python
from zarr_utils import consolidate_metadata

# Basic usage
consolidate_metadata("data.zarr")

# With storage options for remote stores
consolidate_metadata(
    "s3://bucket/data.zarr",
    storage_options={'anon': True}
)

# Dry run to see what would be done
metadata = consolidate_metadata("data.zarr", dry_run=True)
```

### validate_metadata

Checks the integrity and completeness of store metadata.

```python
from zarr_utils import validate_metadata

report = validate_metadata("data.zarr")

# Report contains:
# - valid: bool - Overall validity
# - has_consolidated: bool - Whether .zmetadata exists
# - issues: list - Any problems found
# - arrays: dict - Information about each array
# - groups: dict - Information about each group
```

### repair_metadata

Attempts to fix common metadata issues.

```python
from zarr_utils import repair_metadata

# Basic repair
repair_metadata("data.zarr")

# Also add missing attributes
repair_metadata("data.zarr", add_missing_attrs=True)
```

## Common Scenarios

### Fixing "KeyError: '.zmetadata'"

This is the most common Zarr error:

```python
import zarr
import zarr_utils as zu

# This might fail with KeyError: '.zmetadata'
try:
    store = zarr.open_consolidated("data.zarr")
except KeyError:
    # Fix it
    zu.consolidate_metadata("data.zarr")
    # Now it works
    store = zarr.open_consolidated("data.zarr")
```

### Validating Store Health

Regular validation helps catch issues early:

```python
# Full validation workflow
report = zu.validate_metadata("data.zarr")

if not report['valid']:
    print("Issues found:")
    for issue in report['issues']:
        print(f"  - {issue}")
    
    # Attempt automatic repair
    zu.repair_metadata("data.zarr")
    
    # Re-validate
    report = zu.validate_metadata("data.zarr")
    if report['valid']:
        print("✓ All issues fixed!")
    else:
        print("⚠ Some issues remain - manual intervention needed")
```

### Migrating Stores

When moving Zarr stores between systems:

```python
import shutil
import zarr_utils as zu

# 1. Copy the store
shutil.copytree("old_location/data.zarr", "new_location/data.zarr")

# 2. Validate the copy
report = zu.validate_metadata("new_location/data.zarr")
if not report['valid']:
    print("Issues detected during migration")
    
# 3. Reconsolidate metadata (recommended)
zu.consolidate_metadata("new_location/data.zarr")

# 4. Final validation
report = zu.validate_metadata("new_location/data.zarr")
assert report['valid'], "Migration validation failed"
```

## Understanding Validation Reports

### Report Structure

```python
{
    'valid': True,
    'has_consolidated': True,
    'issues': [],
    'arrays': {
        'data': {
            'shape': (100, 200, 300),
            'dtype': 'float32',
            'chunks': (50, 100, 150),
            'compression': 'gzip',
            'issues': []
        }
    },
    'groups': {
        '/': {
            'attrs': {'description': 'Test data'},
            'issues': []
        }
    }
}
```

### Common Issues

1. **"Missing consolidated metadata (.zmetadata)"**
   - Solution: Run `consolidate_metadata()`

2. **"Root group has no attributes"**
   - Not critical, but good practice to add description
   - Solution: Add attrs or use `repair_metadata(add_missing_attrs=True)`

3. **"Array 'data': No units specified in attributes"**
   - Scientific data should specify units
   - Solution: Manually add units attribute

4. **"Invalid JSON in .zmetadata"**
   - Metadata file is corrupted
   - Solution: Delete .zmetadata and reconsolidate

## Advanced Usage

### Custom Metadata Validation

Extend validation with custom checks:

```python
def validate_scientific_metadata(store_path):
    """Custom validation for scientific datasets."""
    base_report = zu.validate_metadata(store_path)
    custom_issues = []
    
    # Check for required scientific metadata
    for array_path, info in base_report['arrays'].items():
        array = zarr.open_array(f"{store_path}/{array_path}", mode='r')
        
        # Check for units
        if 'units' not in array.attrs:
            custom_issues.append(f"{array_path}: Missing 'units' attribute")
            
        # Check for scale/resolution
        if 'scale' not in array.attrs and 'resolution' not in array.attrs:
            custom_issues.append(f"{array_path}: Missing scale information")
            
        # Check for data range
        if 'data_range' not in array.attrs:
            custom_issues.append(f"{array_path}: Missing data_range attribute")
    
    base_report['custom_issues'] = custom_issues
    if custom_issues:
        base_report['valid'] = False
        
    return base_report
```

### Batch Processing

Process multiple stores efficiently:

```python
from pathlib import Path
import concurrent.futures
import zarr_utils as zu

def process_store(zarr_path):
    """Process a single store."""
    try:
        # Consolidate if needed
        if not Path(f"{zarr_path}/.zmetadata").exists():
            zu.consolidate_metadata(str(zarr_path))
            
        # Validate
        report = zu.validate_metadata(str(zarr_path))
        
        # Repair if needed
        if not report['valid']:
            zu.repair_metadata(str(zarr_path))
            
        return zarr_path, "success", report
    except Exception as e:
        return zarr_path, "error", str(e)

# Process all stores in parallel
zarr_stores = list(Path("data").glob("*.zarr"))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_store, zarr_stores))

# Summary
for path, status, details in results:
    print(f"{path.name}: {status}")
```

### Metadata Backup

Always backup metadata before major operations:

```python
import json
import zarr_utils as zu
from datetime import datetime

def backup_metadata(store_path):
    """Backup store metadata before modifications."""
    # Read current metadata
    metadata = zu.consolidate_metadata(store_path, dry_run=True)
    
    # Create backup
    backup_name = f"{store_path}.metadata_backup_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(backup_name, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Metadata backed up to: {backup_name}")
    return backup_name
```

## Best Practices

1. **Always consolidate metadata for remote stores** before distribution
2. **Validate metadata after any store modifications**
3. **Include metadata management in CI/CD pipelines**
4. **Document required attributes** for your domain
5. **Regular metadata health checks** for production data

## Performance Tips

### Remote Store Optimization

```python
# Slow - multiple S3 requests
def slow_approach(s3_path):
    arrays = zu.list_zarr_arrays(s3_path)  # Many requests
    
# Fast - single S3 request
def fast_approach(s3_path):
    zu.consolidate_metadata(s3_path)  # One-time operation
    arrays = zu.list_zarr_arrays(s3_path)  # Single request
```

### Caching Metadata

```python
import json
import fsspec

# Cache metadata locally
def cache_remote_metadata(remote_path, cache_file):
    fs = fsspec.get_mapper(remote_path)
    metadata = json.loads(fs['.zmetadata'].decode())
    
    with open(cache_file, 'w') as f:
        json.dump(metadata, f)
    
    return metadata

# Use cached metadata
def read_cached_metadata(cache_file):
    with open(cache_file, 'r') as f:
        return json.load(f)
```

## Troubleshooting

### Metadata Corruption

If metadata is corrupted:

```python
# 1. Remove corrupted metadata
import os
os.remove("data.zarr/.zmetadata")

# 2. Recreate from scratch
zu.consolidate_metadata("data.zarr")

# 3. Validate
report = zu.validate_metadata("data.zarr")
```

### Version Compatibility

For Zarr v2/v3 compatibility:

```python
# The compatibility layer handles version differences automatically
zu.consolidate_metadata("data.zarr")  # Works with both v2 and v3
```