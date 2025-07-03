# Quick Start

This guide will help you get started with zarr-utils in just a few minutes.

## Basic Usage

### Listing Arrays in a Zarr Store

```python
from zarr_utils import list_zarr_arrays

# List arrays in a local store
arrays = list_zarr_arrays("data.zarr")
for array in arrays:
    print(f"{array['path']}: shape={array['shape']}, dtype={array['dtype']}")

# List arrays in a remote S3 store
arrays = list_zarr_arrays("s3://bucket/dataset.zarr", 
                         storage_options={'anon': True})
```

### Inspecting a Zarr Store

```python
from zarr_utils import inspect_zarr_store

# Get detailed information about a store
info = inspect_zarr_store("data.zarr", summarize=True)
# This prints a summary and returns a dictionary with array details
```

### Fixing Missing Metadata

One of the most common Zarr errors is missing consolidated metadata:

```python
from zarr_utils import consolidate_metadata

# Fix KeyError: '.zmetadata'
consolidate_metadata("data.zarr")
```

### Opening Zarr as Xarray

```python
from zarr_utils import open_xarray

# Open a Zarr array as an xarray Dataset
ds = open_xarray("data.zarr", "array_name")

# With physical coordinates (automatically converts from metadata)
ds = open_xarray("microscopy_data.zarr", "raw", with_coords=True)
print(ds.coords)  # Shows physical coordinates in meters
```

## Complete Example

Here's a complete example that demonstrates the main features:

```python
import zarr_utils as zu

# 1. Explore a Zarr store
store_path = "example_data.zarr"
print("Arrays in store:")
arrays = zu.list_zarr_arrays(store_path)
for arr in arrays:
    print(f"  {arr['path']}: {arr['shape']} ({arr['dtype']})")

# 2. Fix any metadata issues
zu.consolidate_metadata(store_path)

# 3. Validate the metadata
report = zu.validate_metadata(store_path)
if not report['valid']:
    print("Issues found:")
    for issue in report['issues']:
        print(f"  - {issue}")
    # Attempt repair
    zu.repair_metadata(store_path)

# 4. Open as xarray for analysis
ds = zu.open_xarray(store_path, arrays[0]['path'])
print(f"\nDataset info:")
print(ds)

# 5. Diagnose any issues
diagnosis = zu.diagnose_zarr_store(store_path)
if diagnosis['issues']:
    print("\nStore diagnostics:")
    for issue in diagnosis['issues']:
        print(f"  ⚠️  {issue}")
```

## Working with Remote Data

zarr-utils makes it easy to work with remote Zarr stores:

```python
# Public S3 data (no credentials needed)
arrays = zu.list_zarr_arrays(
    "s3://janelia-cosem-datasets/jrc_hela-2/jrc_hela-2.zarr",
    storage_options={'anon': True}
)

# Private S3 data (uses your AWS credentials)
arrays = zu.list_zarr_arrays("s3://my-bucket/data.zarr")

# Google Cloud Storage
arrays = zu.list_zarr_arrays("gs://bucket/data.zarr")

# HTTP/HTTPS
arrays = zu.list_zarr_arrays("https://example.com/data.zarr")
```

## Error Handling

zarr-utils provides helpful error messages:

```python
from zarr_utils import explain_zarr_error
import zarr

try:
    store = zarr.open_consolidated("data.zarr")
except Exception as e:
    # Get a helpful explanation
    print(explain_zarr_error(e))
    # Output might be:
    # ❌ Error: KeyError: '.zmetadata'
    # 
    # 💡 What this means:
    #    The Zarr store is missing consolidated metadata.
    # 
    # 🔧 Suggestions:
    #    • Run: zarr_utils.consolidate_metadata('data.zarr')
    #    • Or open without consolidation: zarr.open_group(store, mode='r')
```

## Next Steps

- Explore [detailed examples](examples.md)
- Learn about [inspecting Zarr stores](../user-guide/inspect.md) in depth
- Understand [metadata management](../user-guide/metadata.md)
- Set up [debugging tools](../user-guide/debug.md) for development