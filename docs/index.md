# zarr-utils

**Python utilities for working with Zarr datasets**

[![Python Version](https://img.shields.io/pypi/pyversions/zarr-utils.svg)](https://pypi.org/project/zarr-utils/)
[![License](https://img.shields.io/pypi/l/zarr-utils.svg)](https://github.com/yourusername/zarr-utils/blob/main/LICENSE)

## Overview

zarr-utils is a collection of utilities designed to make working with [Zarr](https://zarr.dev/) datasets easier and more efficient. It provides tools for:

- 📊 **Inspecting** Zarr stores and arrays
- 🏷️ **Managing metadata** including consolidation and validation
- 🔍 **Debugging** common Zarr issues with helpful error messages
- 📈 **Integration** with xarray for labeled arrays
- 🎨 **Visualization** support via VTK export
- 🔄 **Compatibility** with both Zarr v2 and v3

## Key Features

### 🚀 Easy Inspection
Quickly explore Zarr stores (local or remote) to understand their structure and contents.

```python
from zarr_utils import list_zarr_arrays, inspect_zarr_store

# List all arrays in a store
arrays = list_zarr_arrays("s3://bucket/dataset.zarr")

# Get detailed information
info = inspect_zarr_store("data.zarr", summarize=True)
```

### 🛠️ Metadata Management
Solve the common `.zmetadata` missing error and optimize performance.

```python
from zarr_utils import consolidate_metadata, validate_metadata

# Fix missing consolidated metadata
consolidate_metadata("data.zarr")

# Validate and repair metadata
validate_metadata("data.zarr")
```

### 🐛 Better Error Messages
Get helpful explanations and solutions for common Zarr errors.

```python
from zarr_utils import explain_zarr_error, diagnose_zarr_store

try:
    # Your Zarr operation
    pass
except Exception as e:
    print(explain_zarr_error(e))
```

### 📊 Xarray Integration
Open Zarr arrays as xarray datasets with proper coordinates and metadata.

```python
from zarr_utils import open_xarray

# Open with physical coordinates
ds = open_xarray("data.zarr", "array_name")
```

## Why zarr-utils?

Working with Zarr can be challenging, especially when dealing with:

- Large remote datasets
- Missing or corrupted metadata
- Compatibility between Zarr versions
- Integration with scientific Python tools

zarr-utils addresses these pain points by providing:

- **Robust error handling** with actionable error messages
- **Performance optimizations** for remote data access
- **Seamless compatibility** between Zarr v2 and v3
- **Scientific computing integrations** with xarray and VTK

## Quick Example

```python
import zarr_utils as zu

# Inspect a remote Zarr store
arrays = zu.list_zarr_arrays("s3://janelia-cosem-datasets/jrc_hela-1/jrc_hela-1.zarr")
for array in arrays:
    print(f"{array['path']}: {array['shape']} ({array['size_bytes']:,} bytes)")

# Fix common metadata issues
zu.consolidate_metadata("local_data.zarr")

# Open as xarray with coordinates
ds = zu.open_xarray("local_data.zarr", "volume")
print(ds)
```

## Installation

```bash
pip install zarr-utils
```

For development installation:
```bash
pip install -e ".[dev]"
```

## Next Steps

- [Get Started](getting-started/quickstart.md) with zarr-utils
- Browse [Examples](getting-started/examples.md)
- Read the [User Guide](user-guide/inspect.md)
- Explore the [API Reference](api/index.md)