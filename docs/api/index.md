# API Reference

This section contains the complete API reference for zarr-utils.

## Modules

- [**zarr_utils.inspect**](inspect.md) - Tools for exploring Zarr stores
- [**zarr_utils.xarray**](xarray.md) - Integration with xarray
- [**zarr_utils.visualization**](visualization.md) - VTK export and visualization
- [**zarr_utils.metadata**](metadata.md) - Metadata management utilities
- [**zarr_utils.debug**](debug.md) - Debugging and diagnostic tools
- [**zarr_utils.compat**](compat.md) - Zarr v2/v3 compatibility layer

## Quick Reference

### Most Common Functions

```python
from zarr_utils import (
    # Inspection
    list_zarr_arrays,
    inspect_zarr_store,
    
    # Metadata
    consolidate_metadata,
    validate_metadata,
    repair_metadata,
    
    # Xarray integration
    open_xarray,
    
    # Debugging
    diagnose_zarr_store,
    explain_zarr_error,
)
```

### Basic Workflow

```python
import zarr_utils as zu

# 1. Explore a store
arrays = zu.list_zarr_arrays("data.zarr")

# 2. Fix metadata issues
zu.consolidate_metadata("data.zarr")

# 3. Open as xarray
ds = zu.open_xarray("data.zarr", "array_name")

# 4. Debug issues
diagnosis = zu.diagnose_zarr_store("data.zarr")
```

## Package Constants

```python
# Version information
__version__ = "0.1.0"

# Supported Zarr versions
ZARR_V2_SUPPORTED = True
ZARR_V3_SUPPORTED = True
```

## Type Annotations

zarr-utils uses type hints throughout. Common types:

```python
from typing import Union, Optional, Any

# Store path can be local or remote
StorePath = Union[str, Path]

# Storage options for fsspec
StorageOptions = Optional[dict[str, Any]]

# Array information dictionary
ArrayInfo = dict[str, Union[str, tuple[int, ...], int]]
```

## Error Handling

All functions raise standard Python exceptions:

- `ValueError` - Invalid parameters or data
- `KeyError` - Missing metadata or arrays
- `FileNotFoundError` - Store doesn't exist
- `PermissionError` - Access denied
- `RuntimeError` - Unexpected errors

Use `explain_zarr_error()` for user-friendly error messages.

## Thread Safety

Most zarr-utils functions are thread-safe for read operations. Write operations (consolidate_metadata, repair_metadata) should be synchronized by the caller.

## Performance Considerations

- Always use consolidated metadata for remote stores
- Cache results when possible
- Use storage_options for authentication
- Consider chunking for large arrays