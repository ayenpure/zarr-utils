# Examples

This page provides comprehensive examples of using zarr-utils in various scenarios.

## Example 1: Exploring a Scientific Dataset

```python
import zarr_utils as zu
import numpy as np

# Open a public electron microscopy dataset
url = "s3://janelia-cosem-datasets/jrc_hela-3/jrc_hela-3.zarr"
storage_options = {'anon': True}

# List all arrays
arrays = zu.list_zarr_arrays(url, storage_options=storage_options)
print(f"Found {len(arrays)} arrays in the dataset")

# Inspect the largest array
largest = max(arrays, key=lambda x: x['size_bytes'])
print(f"\nLargest array: {largest['path']}")
print(f"Shape: {largest['shape']}")
print(f"Chunks: {largest['chunks']}")
print(f"Size: {largest['size_bytes'] / 1e9:.2f} GB")

# Get detailed store information
info = zu.inspect_zarr_store(url, storage_options=storage_options, 
                             summarize=True)
```

## Example 2: Metadata Management Workflow

```python
import zarr_utils as zu
import zarr

# Create a test dataset
store_path = "test_data.zarr"
root = zarr.open_group(store_path, mode='w')
root.attrs['description'] = 'Test microscopy data'

# Add some arrays
data1 = np.random.rand(100, 200, 300).astype('float32')
arr1 = root.create_dataset('raw', data=data1, chunks=(50, 100, 150))
arr1.attrs['units'] = 'intensity'
arr1.attrs['scale'] = [1.0, 0.5, 0.5]  # z, y, x in micrometers

# Create a subgroup with processed data
processed = root.create_group('processed')
data2 = np.random.rand(50, 100, 150).astype('float32')
arr2 = processed.create_dataset('downsampled', data=data2, chunks=(25, 50, 75))
arr2.attrs['units'] = 'intensity'
arr2.attrs['downsampling_factor'] = 2

# Now use zarr-utils to manage metadata
# 1. Consolidate metadata for faster access
zu.consolidate_metadata(store_path)

# 2. Validate the metadata
report = zu.validate_metadata(store_path)
print(f"Metadata valid: {report['valid']}")
print(f"Arrays found: {len(report['arrays'])}")
print(f"Groups found: {len(report['groups'])}")

# 3. If there are issues, repair them
if not report['valid']:
    zu.repair_metadata(store_path)
```

## Example 3: Xarray Integration for Analysis

```python
import zarr_utils as zu
import matplotlib.pyplot as plt

# Open a 3D microscopy dataset
ds = zu.open_xarray("microscopy.zarr", "raw/channel0", with_coords=True)

# The dataset now has physical coordinates
print(ds)
# <xarray.Dataset>
# Dimensions:  (z: 100, y: 512, x: 512)
# Coordinates:
#   * z        (z) float64 0.0 2e-06 4e-06 ... 0.000196 0.000198
#   * y        (y) float64 0.0 5e-07 1e-06 ... 0.0002555 0.000256
#   * x        (x) float64 0.0 5e-07 1e-06 ... 0.0002555 0.000256
# Data variables:
#     values   (z, y, x) float32 ...

# Extract a slice at a specific depth
slice_um = 50  # micrometers
z_index = abs(ds.z - slice_um * 1e-6).argmin()
xy_slice = ds.values.isel(z=z_index)

# Plot with physical coordinates
fig, ax = plt.subplots(figsize=(8, 8))
xy_slice.plot(x='x', y='y', ax=ax, cmap='gray')
ax.set_xlabel('X (meters)')
ax.set_ylabel('Y (meters)')
ax.set_title(f'XY slice at Z = {slice_um} μm')
plt.show()

# Compute statistics over regions
mean_intensity = ds.values.mean(dim=['y', 'x'])
mean_intensity.plot()
plt.xlabel('Z (meters)')
plt.ylabel('Mean Intensity')
plt.show()
```

## Example 4: Debugging and Error Handling

```python
import zarr_utils as zu
from zarr_utils.debug import ZarrDebugger, enable_debug_mode

# Enable debug mode for detailed operation tracking
enable_debug_mode()

# Use the debugger context manager
debugger = ZarrDebugger(verbose=True)

with debugger.operation("Loading remote dataset"):
    try:
        arrays = zu.list_zarr_arrays("s3://bucket/data.zarr")
    except Exception as e:
        explanation = zu.explain_zarr_error(e)
        print(explanation)

# Diagnose store issues
diagnosis = zu.diagnose_zarr_store("problematic_data.zarr", detailed=True)

print("\nStore Diagnosis:")
print(f"Accessible: {diagnosis['accessible']}")
print(f"Store type: {diagnosis['store_type']}")
print(f"Has consolidated metadata: {diagnosis['has_consolidated_metadata']}")

if diagnosis['issues']:
    print("\nIssues found:")
    for issue in diagnosis['issues']:
        print(f"  - {issue}")
        
if diagnosis['suggestions']:
    print("\nSuggestions:")
    for suggestion in diagnosis['suggestions']:
        print(f"  • {suggestion}")

# Get performance metrics
print(f"\nPerformance:")
print(f"  Small read time: {diagnosis['performance']['small_read_time']:.3f}s")
print(f"  Read bandwidth: {diagnosis['performance']['read_bandwidth_mbps']:.1f} MB/s")

# View operation summary
debugger.summarize()
```

## Example 5: Batch Processing Multiple Stores

```python
import zarr_utils as zu
from pathlib import Path
import pandas as pd

# Process all Zarr stores in a directory
data_dir = Path("datasets")
results = []

for zarr_path in data_dir.glob("*.zarr"):
    print(f"Processing {zarr_path.name}...")
    
    try:
        # Consolidate metadata if needed
        zu.consolidate_metadata(str(zarr_path), dry_run=False)
        
        # Get store information
        arrays = zu.list_zarr_arrays(str(zarr_path))
        
        # Collect statistics
        total_size = sum(arr['size_bytes'] for arr in arrays)
        total_elements = sum(np.prod(arr['shape']) for arr in arrays)
        
        results.append({
            'store': zarr_path.name,
            'num_arrays': len(arrays),
            'total_size_gb': total_size / 1e9,
            'total_elements': total_elements,
            'valid_metadata': zu.validate_metadata(str(zarr_path))['valid']
        })
        
    except Exception as e:
        print(f"  Error: {e}")
        results.append({
            'store': zarr_path.name,
            'error': str(e)
        })

# Create summary report
df = pd.DataFrame(results)
print("\nSummary Report:")
print(df.to_string())

# Save report
df.to_csv("zarr_stores_report.csv", index=False)
```

## Example 6: Creating Compatible Zarr Stores

```python
import zarr_utils as zu
from zarr_utils.compat import create_array_compat
import zarr
import numpy as np

# Create a store that works with both Zarr v2 and v3
store_path = "compatible_store.zarr"
store = zarr.open_group(store_path, mode='w')
store.attrs['created_with'] = 'zarr-utils'
store.attrs['zarr_version'] = zarr.__version__

# Use compatibility layer for array creation
data = np.random.rand(1000, 2000).astype('float32')
arr = create_array_compat(
    store, 
    name='data',
    data=data,
    chunks=(100, 200),
    compressor=zarr.Zlib(level=6)
)

# Add metadata
arr.attrs.update({
    'units': 'arbitrary',
    'description': 'Random test data',
    'created': '2024-01-01'
})

# Create hierarchical structure
group1 = store.create_group('analysis')
results = create_array_compat(
    group1,
    name='results',
    shape=(100,),
    dtype='float64',
    chunks=(10,)
)

# Consolidate metadata for performance
zu.consolidate_metadata(store_path)

# Verify compatibility
print(f"Store created successfully")
print(f"Compatible with Zarr {zarr.__version__}")
arrays = zu.list_zarr_arrays(store_path)
for arr in arrays:
    print(f"  {arr['path']}: {arr['shape']} ({arr['dtype']})")
```

## Running the Examples

To run these examples:

1. Install zarr-utils: `pip install zarr-utils`
2. For remote data examples, install: `pip install s3fs`
3. For visualization examples, install: `pip install matplotlib`
4. For batch processing, install: `pip install pandas`

Some examples use public datasets that don't require authentication. For private S3 data, ensure your AWS credentials are configured.