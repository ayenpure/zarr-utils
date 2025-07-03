# Working with Xarray

zarr-utils provides seamless integration between Zarr and xarray, making it easy to work with labeled arrays and physical coordinates.

## Overview

The `open_xarray` function opens Zarr arrays as xarray Datasets with:
- Proper dimension labels (x, y, z, c)
- Physical coordinates (converted from metadata)
- Preserved attributes
- Chunk information

## Basic Usage

### Opening a Zarr Array

```python
from zarr_utils import open_xarray

# Basic usage
ds = open_xarray("data.zarr", "array_name")

# With physical coordinates
ds = open_xarray("microscopy.zarr", "raw/channel0", with_coords=True)

# With custom variable name
ds = open_xarray("data.zarr", "raw", var_name="intensity")
```

### Understanding the Output

```python
print(ds)
# <xarray.Dataset>
# Dimensions:  (z: 100, y: 512, x: 512)
# Coordinates:
#   * z        (z) float64 0.0 2e-06 4e-06 ... 0.000198
#   * y        (y) float64 0.0 5e-07 1e-06 ... 0.000256
#   * x        (x) float64 0.0 5e-07 1e-06 ... 0.000256
# Data variables:
#     values   (z, y, x) float32 ...
# Attributes:
#     source_url: microscopy.zarr
#     voxel_spacing_nm: (2000.0, 500.0, 500.0)
```

## Voxel Spacing

zarr-utils automatically extracts voxel spacing from various metadata formats:

```python
from zarr_utils import get_voxel_spacing

# Standard formats supported:
# - pixelResolution.dimensions
# - spacing
# - voxelSize
# - scale
# - resolution

spacing = get_voxel_spacing(zarr_array)
# Returns (z, y, x) spacing in nanometers
```

### Metadata Formats

```python
# Format 1: pixelResolution (common in EM data)
array.attrs['pixelResolution'] = {
    'dimensions': [40.0, 4.0, 4.0],  # z, y, x in nm
    'unit': 'nm'
}

# Format 2: Direct spacing
array.attrs['spacing'] = [2.0, 0.5, 0.5]  # micrometers

# Format 3: Individual axes
array.attrs['z_spacing'] = 2.0
array.attrs['y_spacing'] = 0.5
array.attrs['x_spacing'] = 0.5
```

## Working with Coordinates

### Physical Units

Coordinates are automatically converted to meters (SI units):

```python
# Open with coordinates
ds = open_xarray("data.zarr", "volume", with_coords=True)

# Coordinates are in meters
print(ds.z.values)  # [0.0, 2e-6, 4e-6, ...]

# Convert to micrometers for display
z_um = ds.z.values * 1e6
print(f"Z range: {z_um.min():.1f} - {z_um.max():.1f} μm")
```

### Selecting Data by Physical Position

```python
# Select slice at 50 micrometers depth
z_position = 50e-6  # 50 μm in meters
slice_data = ds.values.sel(z=z_position, method='nearest')

# Select region of interest
roi = ds.values.sel(
    x=slice(100e-6, 200e-6),  # 100-200 μm
    y=slice(100e-6, 200e-6),
    z=50e-6
)
```

## Multi-dimensional Data

### 3D Data (Z, Y, X)

```python
# Standard 3D microscopy data
ds = open_xarray("volume.zarr", "")
assert list(ds.values.dims) == ['z', 'y', 'x']

# Compute MIP (Maximum Intensity Projection)
mip_xy = ds.values.max(dim='z')
mip_xz = ds.values.max(dim='y')
mip_yz = ds.values.max(dim='x')
```

### 2D Data

2D arrays are automatically expanded with a singleton Z dimension:

```python
# 2D array
ds = open_xarray("image.zarr", "")
print(ds.values.shape)  # (1, 1024, 1024)
print(ds.values.dims)   # ('z', 'y', 'x')

# Extract 2D data
image = ds.values.squeeze('z')
```

### 4D Data (C, Z, Y, X)

```python
# Multi-channel data
ds = open_xarray("multichannel.zarr", "")
assert list(ds.values.dims) == ['c', 'z', 'y', 'x']

# Select specific channel
channel0 = ds.values.sel(c=0)
channel1 = ds.values.sel(c=1)

# Process each channel
for c in range(ds.dims['c']):
    channel_data = ds.values.sel(c=c)
    # Process channel...
```

## Integration with Analysis

### Basic Statistics

```python
# Compute statistics over spatial dimensions
mean_intensity = ds.values.mean(dim=['y', 'x'])
mean_intensity.plot()
plt.xlabel('Z position (m)')
plt.ylabel('Mean intensity')

# Profile along axis
center_y = ds.dims['y'] // 2
center_x = ds.dims['x'] // 2
z_profile = ds.values.isel(y=center_y, x=center_x)
```

### Resampling

```python
# Downsample by factor of 2
downsampled = ds.values.coarsen(
    x=2, y=2, z=2, boundary='trim'
).mean()

# Interpolate to regular grid
regular_z = np.linspace(0, 100e-6, 50)
regular_y = np.linspace(0, 100e-6, 256) 
regular_x = np.linspace(0, 100e-6, 256)

interpolated = ds.values.interp(
    z=regular_z, y=regular_y, x=regular_x
)
```

### Region Analysis

```python
import numpy as np
from scipy import ndimage

# Extract region
roi = ds.values.sel(
    x=slice(50e-6, 150e-6),
    y=slice(50e-6, 150e-6)
)

# Apply threshold
threshold = roi.mean() + 2 * roi.std()
binary = roi > threshold

# Label connected components
labels, num_features = ndimage.label(binary)
print(f"Found {num_features} objects")
```

## Performance Tips

### Chunked Operations

```python
# Work with chunks for large data
ds = open_xarray("large_data.zarr", "volume")

# Check chunk sizes
print(f"Zarr chunks: {ds.values.attrs['zarr_chunks']}")

# Process chunk by chunk
for z_chunk in range(0, ds.dims['z'], 64):
    chunk = ds.values.isel(z=slice(z_chunk, z_chunk + 64))
    # Process chunk...
```

### Lazy Loading

```python
# Data is loaded lazily
ds = open_xarray("huge_dataset.zarr", "data")

# This doesn't load data yet
subset = ds.values[::2, ::2, ::2]  # Every other pixel

# Data loads when computed
result = subset.mean().compute()  # Now data is loaded
```

### Caching

```python
# Cache frequently accessed data
ds = open_xarray("data.zarr", "volume")

# Persist in memory
ds_cached = ds.persist()

# Now operations are faster
mean1 = ds_cached.values.mean()
std1 = ds_cached.values.std()
```

## Export and Visualization

### Save as NetCDF

```python
# Export to NetCDF
ds.to_netcdf("data.nc")

# With compression
ds.to_netcdf("data_compressed.nc", 
             encoding={'values': {'zlib': True, 'complevel': 6}})
```

### Quick Visualization

```python
import matplotlib.pyplot as plt

# 2D visualization
ds.values.isel(z=50).plot(cmap='viridis', robust=True)
plt.title('XY slice at Z=50')

# 3D orthogonal views
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# XY view (top-down)
ds.values.max(dim='z').plot(ax=axes[0], cmap='gray')
axes[0].set_title('XY projection')

# XZ view (side)
ds.values.max(dim='y').plot(ax=axes[1], cmap='gray')
axes[1].set_title('XZ projection')

# YZ view (front)
ds.values.max(dim='x').plot(ax=axes[2], cmap='gray')
axes[2].set_title('YZ projection')

plt.tight_layout()
```

## Advanced Usage

### Custom Coordinate Systems

```python
# Override automatic coordinates
ds = open_xarray("data.zarr", "array", with_coords=False)

# Add custom coordinates
ds = ds.assign_coords({
    'z': np.linspace(0, 100, ds.dims['z']),  # 0-100 μm
    'y': np.linspace(0, 50, ds.dims['y']),   # 0-50 μm  
    'x': np.linspace(0, 50, ds.dims['x'])    # 0-50 μm
})
```

### Multi-store Datasets

```python
# Combine multiple Zarr stores
datasets = []
for i, path in enumerate(zarr_paths):
    ds = open_xarray(path, "data")
    ds = ds.assign_coords(time=i)
    datasets.append(ds)

# Concatenate along time dimension
combined = xr.concat(datasets, dim='time')
```

### Metadata Preservation

```python
# Original Zarr attributes are preserved
ds = open_xarray("annotated.zarr", "segmentation")

# Access original attributes
print(ds.values.attrs)  # Contains all Zarr array attributes
print(ds.attrs)        # Contains store-level metadata

# Add analysis metadata
ds.attrs['analysis_date'] = '2024-01-01'
ds.attrs['processed_by'] = 'zarr-utils'
```

## Troubleshooting

### Memory Issues

```python
# For very large arrays, work in chunks
def process_large_array(zarr_path, array_name, chunk_size=64):
    """Process large array in chunks."""
    ds = open_xarray(zarr_path, array_name)
    
    results = []
    for z in range(0, ds.dims['z'], chunk_size):
        chunk = ds.values.isel(z=slice(z, z + chunk_size))
        result = chunk.mean(dim=['y', 'x']).compute()
        results.append(result)
    
    return xr.concat(results, dim='z')
```

### Coordinate Errors

```python
# If coordinates are wrong, check metadata
import zarr
arr = zarr.open_array("data.zarr/array")
print("Array attributes:", dict(arr.attrs))

# Fix spacing if needed
from zarr_utils import get_voxel_spacing
spacing = get_voxel_spacing(arr, default=(1.0, 1.0, 1.0))
print(f"Detected spacing: {spacing}")
```