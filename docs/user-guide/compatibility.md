# Zarr v2/v3 Compatibility

zarr-utils provides seamless compatibility between Zarr v2 and v3 through a dedicated compatibility layer. This ensures your code works regardless of which Zarr version is installed.

## Overview

The compatibility module (`zarr_utils.compat`) automatically detects your Zarr version and adjusts API calls accordingly. This handles:

- Metadata consolidation differences
- Array creation API changes
- Storage options handling
- Store access patterns
- Compressor property access

## Version Detection

```python
from zarr_utils.compat import IS_ZARR_V3, ZARR_VERSION

print(f"Zarr version: {ZARR_VERSION}")
print(f"Using Zarr v3: {IS_ZARR_V3}")
```

## Key Compatibility Functions

### consolidate_metadata

Handles the `metadata_key` parameter difference:

```python
from zarr_utils.compat import consolidate_metadata

# Works with both v2 and v3
consolidate_metadata(store_or_mapper)

# v2: Uses metadata_key='.zmetadata' 
# v3: Doesn't accept metadata_key parameter
```

### create_array_compat

Unified array creation API:

```python
from zarr_utils.compat import create_array_compat
import zarr

store = zarr.open_group("data.zarr", mode="w")

# With data
arr = create_array_compat(
    store, 
    name="array1",
    data=np.random.rand(100, 200),
    chunks=(50, 100)
)

# Without data
arr = create_array_compat(
    store,
    name="array2", 
    shape=(100, 200),
    dtype=np.float32,
    chunks=(50, 100)
)
```

### Storage Options Handling

Both v2 and v3 only accept storage_options for remote stores:

```python
from zarr_utils.compat import open_array_with_storage_options

# Local path - storage_options ignored
arr = open_array_with_storage_options(
    "local_data.zarr",
    mode="r",
    storage_options={"some": "option"}  # Ignored
)

# Remote path - storage_options used
arr = open_array_with_storage_options(
    "s3://bucket/data.zarr",
    mode="r", 
    storage_options={"anon": True}  # Applied
)
```

### Compressor Access

```python
from zarr_utils.compat import get_array_compressor

# Works with both versions
compressor = get_array_compressor(array)
# v2: Returns codec_id from array.compressor
# v3: Returns class name from array.compressors[0]
```

### Store Access

```python
from zarr_utils.compat import access_store_item, store_contains

# Check if item exists
if store_contains(store, ".zmetadata"):
    # Access item
    metadata = access_store_item(store, ".zmetadata")
```

## Migration Guide

### Updating Existing Code

Replace version-specific code with compatibility functions:

```python
# Old v2-specific code
if '.zmetadata' in store:
    metadata = store['.zmetadata']
    
# New compatible code
from zarr_utils.compat import store_contains, access_store_item
if store_contains(store, '.zmetadata'):
    metadata = access_store_item(store, '.zmetadata')
```

### Array Creation

```python
# Old v2 code
arr = group.create_dataset('data', data=data, chunks=chunks)

# Old v3 code  
arr = group.create_array('data', shape=data.shape, dtype=data.dtype)
arr[:] = data

# New compatible code
from zarr_utils.compat import create_array_compat
arr = create_array_compat(group, 'data', data=data, chunks=chunks)
```

## Version-Specific Behavior

### Metadata Consolidation

```python
# v2 behavior
zarr.consolidate_metadata(store, metadata_key='.zmetadata')

# v3 behavior
zarr.consolidate_metadata(store)  # No metadata_key parameter

# Compatible approach
from zarr_utils.compat import consolidate_metadata
consolidate_metadata(store)  # Handles both versions
```

### Store Types

```python
# v2: Various store types (DirectoryStore, FSStore, etc.)
# v3: New store API (LocalStore, RemoteStore, etc.)

# Compatible store access
from zarr_utils.compat import get_store_from_mapper
store = get_store_from_mapper(mapper)
```

## Testing Compatibility

### Running Tests with Different Versions

```bash
# Test with Zarr v2
pip install "zarr<3"
pytest tests/

# Test with Zarr v3
pip install "zarr>=3.0.0"
pytest tests/
```

### Writing Compatible Tests

```python
import pytest
from zarr_utils.compat import IS_ZARR_V3, create_array_compat

def test_array_creation():
    """Test that works with both Zarr versions."""
    store = zarr.open_group("test.zarr", mode="w")
    
    # Use compatibility function
    arr = create_array_compat(
        store, 
        "test",
        shape=(10, 10),
        dtype=np.float32
    )
    
    assert arr.shape == (10, 10)
    assert arr.dtype == np.float32
    
    # Version-specific assertions
    if IS_ZARR_V3:
        assert hasattr(arr, 'compressors')
    else:
        assert hasattr(arr, 'compressor')
```

## Common Compatibility Issues

### Issue 1: KeyError with Compressor

```python
# Problem: v3 doesn't have array.compressor
try:
    comp = array.compressor  # Fails in v3
except AttributeError:
    comp = None

# Solution: Use compatibility function
from zarr_utils.compat import get_array_compressor
comp = get_array_compressor(array)
```

### Issue 2: Store Subscripting

```python
# Problem: v3 stores might not support [] operator
try:
    data = store['.zmetadata']  # Might fail in v3
except TypeError:
    data = None

# Solution: Use compatibility function
from zarr_utils.compat import access_store_item
data = access_store_item(store, '.zmetadata')
```

### Issue 3: Array Creation Parameters

```python
# Problem: v3 requires shape and dtype
try:
    # v2 style
    arr = group.create_dataset('data', data=data)
except TypeError:
    # v3 style
    arr = group.create_array('data', shape=data.shape, dtype=data.dtype)
    arr[:] = data

# Solution: Use compatibility function
from zarr_utils.compat import create_array_compat
arr = create_array_compat(group, 'data', data=data)
```

## Best Practices

1. **Always use compatibility functions** for cross-version code
2. **Test with both versions** in CI/CD pipelines
3. **Document version requirements** if using version-specific features
4. **Avoid direct store access** - use compatibility wrappers
5. **Check IS_ZARR_V3** only when absolutely necessary

## Future Compatibility

As Zarr evolves, the compatibility layer will be updated to handle new changes. To prepare:

1. Use zarr-utils functions instead of direct Zarr calls where possible
2. Pin Zarr version in production environments
3. Test thoroughly when upgrading Zarr versions
4. Report compatibility issues to zarr-utils repository

## Examples

### Creating Compatible Stores

```python
from zarr_utils.compat import create_array_compat
import zarr
import numpy as np

def create_compatible_store(path):
    """Create a store that works with both v2 and v3."""
    store = zarr.open_group(path, mode='w')
    
    # Add metadata
    store.attrs['created_with'] = 'zarr-utils'
    store.attrs['zarr_version'] = zarr.__version__
    
    # Create arrays using compatibility layer
    data1 = np.random.rand(100, 200)
    arr1 = create_array_compat(
        store,
        'array1',
        data=data1,
        chunks=(50, 100)
    )
    arr1.attrs['description'] = 'Test array 1'
    
    # Create group with array
    subgroup = store.create_group('analysis')
    data2 = np.zeros((50, 50))
    arr2 = create_array_compat(
        subgroup,
        'results',
        data=data2
    )
    
    # Consolidate metadata
    from zarr_utils import consolidate_metadata
    consolidate_metadata(path)
    
    return store
```

### Reading Version-Agnostic

```python
from zarr_utils.compat import (
    store_contains,
    access_store_item,
    get_array_compressor
)

def read_store_info(store_path):
    """Read store information regardless of version."""
    import fsspec
    import json
    
    mapper = fsspec.get_mapper(store_path)
    
    # Check for consolidated metadata
    has_consolidated = store_contains(mapper, '.zmetadata')
    
    if has_consolidated:
        # Read metadata
        metadata_bytes = access_store_item(mapper, '.zmetadata')
        if metadata_bytes:
            metadata = json.loads(metadata_bytes.decode())
            print("Consolidated metadata found")
    
    # Open store
    if has_consolidated:
        store = zarr.open_consolidated(mapper, mode='r')
    else:
        store = zarr.open_group(mapper, mode='r')
    
    # Inspect arrays
    for name, arr in store.arrays():
        compressor = get_array_compressor(arr)
        print(f"{name}: {arr.shape}, {arr.dtype}, compressor={compressor}")
    
    return store
```