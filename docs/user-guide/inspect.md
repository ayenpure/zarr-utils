# Inspecting Zarr Stores

The inspection module provides tools to explore and understand Zarr stores, whether they're stored locally or on remote cloud storage.

## Core Functions

### list_zarr_arrays

Lists all arrays in a Zarr store with their metadata.

```python
from zarr_utils import list_zarr_arrays

# List arrays in local store
arrays = list_zarr_arrays("data.zarr")

# List arrays in S3 store
arrays = list_zarr_arrays(
    "s3://bucket/dataset.zarr",
    storage_options={'anon': True}  # For public data
)

# Each array entry contains:
# - path: Full path within the store
# - shape: Array dimensions
# - chunks: Chunk dimensions
# - dtype: Data type
# - size_bytes: Total size in bytes
```

### inspect_zarr_store

Provides detailed information about a Zarr store and optionally prints a summary.

```python
from zarr_utils import inspect_zarr_store

# Get detailed information
info = inspect_zarr_store("data.zarr", summarize=True)

# Returns a dictionary with array details
# Also prints a formatted summary if summarize=True
```

## Understanding the Output

### Array Information

Each array in the store is described with:

- **Path**: Location within the store hierarchy (e.g., "raw/channel0")
- **Shape**: Dimensions of the array (e.g., (100, 512, 512))
- **Chunks**: How the array is divided for storage (e.g., (10, 256, 256))
- **Data Type**: NumPy dtype (e.g., float32, uint16)
- **Size**: Total size in bytes

### Store Summary

When using `inspect_zarr_store` with `summarize=True`, you get:

```
Inspecting Zarr store: data.zarr
=====================================
 Array                                                     |        Shape |       Chunks | Type       |       Size  
-----------------------------------------------------------------------------------------------------------------------
 raw/channel0                                              | 512×1024×2048 |  64×256×256 | float32    | 3.9 GB
 segmentation/cells                                        | 512×1024×2048 |  64×256×256 | uint32     | 3.9 GB
 analysis/measurements                                     |        10000 |        1000 | float64    | 78.1 KB
-----------------------------------------------------------------------------------------------------------------------
Total arrays: 3                                                                           Total size:    7.8 GB
```

## Working with Hierarchical Stores

Zarr stores can have a hierarchical structure similar to a filesystem:

```python
# Example hierarchical store structure:
# store.zarr/
#   ├── raw/
#   │   ├── channel0  (array)
#   │   └── channel1  (array)
#   ├── processed/
#   │   ├── denoised  (array)
#   │   └── normalized  (array)
#   └── metadata.json

arrays = list_zarr_arrays("store.zarr")
# Returns all arrays with their full paths:
# [
#   {'path': 'raw/channel0', ...},
#   {'path': 'raw/channel1', ...},
#   {'path': 'processed/denoised', ...},
#   {'path': 'processed/normalized', ...}
# ]
```

## Performance Considerations

### Consolidated Metadata

For remote stores, using consolidated metadata significantly improves performance:

```python
# Slow - requires multiple requests to S3
arrays = list_zarr_arrays("s3://bucket/large-dataset.zarr")

# Fast - reads from consolidated .zmetadata file
import zarr_utils as zu
zu.consolidate_metadata("s3://bucket/large-dataset.zarr")
arrays = zu.list_zarr_arrays("s3://bucket/large-dataset.zarr")
```

### Caching

For repeated access, consider caching the results:

```python
import functools

@functools.lru_cache(maxsize=128)
def get_array_info(store_path):
    return list_zarr_arrays(store_path)

# Subsequent calls with same path are cached
info1 = get_array_info("data.zarr")  # Reads from store
info2 = get_array_info("data.zarr")  # Returns cached result
```

## Advanced Usage

### Custom Storage Options

Pass storage-specific options for authentication or configuration:

```python
# AWS S3 with specific credentials
arrays = list_zarr_arrays(
    "s3://private-bucket/data.zarr",
    storage_options={
        'key': 'YOUR_ACCESS_KEY',
        'secret': 'YOUR_SECRET_KEY',
        'region_name': 'us-east-1'
    }
)

# Google Cloud Storage
arrays = list_zarr_arrays(
    "gs://bucket/data.zarr",
    storage_options={
        'token': 'path/to/service-account.json'
    }
)

# HTTP with authentication
arrays = list_zarr_arrays(
    "https://data.example.com/dataset.zarr",
    storage_options={
        'headers': {'Authorization': 'Bearer TOKEN'}
    }
)
```

### Filtering Arrays

Filter arrays based on criteria:

```python
# Get all arrays
all_arrays = list_zarr_arrays("data.zarr")

# Filter large arrays (> 1GB)
large_arrays = [
    arr for arr in all_arrays 
    if arr['size_bytes'] > 1e9
]

# Filter by data type
float_arrays = [
    arr for arr in all_arrays 
    if 'float' in arr['dtype']
]

# Filter by path pattern
raw_arrays = [
    arr for arr in all_arrays 
    if arr['path'].startswith('raw/')
]
```

### Parallel Inspection

For multiple stores, use parallel processing:

```python
from concurrent.futures import ThreadPoolExecutor
import zarr_utils as zu

store_urls = [
    "s3://bucket/dataset1.zarr",
    "s3://bucket/dataset2.zarr",
    "s3://bucket/dataset3.zarr",
]

def inspect_store(url):
    try:
        return url, zu.list_zarr_arrays(url, storage_options={'anon': True})
    except Exception as e:
        return url, f"Error: {e}"

# Inspect multiple stores in parallel
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(inspect_store, store_urls))

for url, result in results:
    if isinstance(result, list):
        print(f"{url}: {len(result)} arrays found")
    else:
        print(f"{url}: {result}")
```

## Best Practices

1. **Always use consolidated metadata for remote stores** - It's much faster
2. **Handle errors gracefully** - Network issues can occur with remote data
3. **Consider array sizes** - Some arrays might be too large to load entirely
4. **Use appropriate storage options** - Different cloud providers have different requirements
5. **Cache results when possible** - Avoid repeated metadata queries

## Troubleshooting

### Common Issues

**"Cannot open store"**
- Check the path/URL is correct
- Verify you have read permissions
- For S3, ensure credentials are configured

**"Slow performance"**
- Use consolidated metadata
- Check your internet connection
- Consider using a cloud compute instance in the same region

**"Memory errors"**
- You're likely trying to load too much data
- Use chunked access instead of loading entire arrays

### Getting Help

If you encounter issues:

```python
from zarr_utils import diagnose_zarr_store

# Get detailed diagnostics
diagnosis = diagnose_zarr_store("problematic.zarr", detailed=True)
print(diagnosis)
```