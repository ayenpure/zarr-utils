# Visualization

zarr-utils provides tools for exporting Zarr data to visualization formats, particularly VTK for 3D scientific visualization.

## Overview

The visualization module enables:
- Export to VTK format (.vti files)
- Integration with PyVista for interactive visualization
- Preservation of physical coordinates and metadata
- Support for multi-channel data

## VTK Export

### Basic Export

```python
from zarr_utils.visualization import to_vti

# Export Zarr array to VTK ImageData
to_vti("data.zarr", "volume", "output.vti")

# With specific spacing (in micrometers)
to_vti("data.zarr", "volume", "output.vti", 
       spacing=(2.0, 0.5, 0.5))
```

### Understanding VTK ImageData

VTK ImageData (.vti) format:
- Regular grid structure (matches Zarr arrays)
- Supports physical spacing
- Can store multiple scalar/vector fields
- Compatible with ParaView, VTK, PyVista

## PyVista Integration

### Interactive Visualization

```python
from zarr_utils.visualization import wrap_vtk
import pyvista as pv

# Load Zarr data as PyVista object
image_data = wrap_vtk("data.zarr", "volume")

# Create visualization
plotter = pv.Plotter()
plotter.add_volume(
    image_data,
    cmap="viridis",
    opacity="sigmoid"
)
plotter.show()
```

### Orthogonal Slices

```python
# Create orthogonal slices
image_data = wrap_vtk("data.zarr", "volume")

plotter = pv.Plotter()

# Add orthogonal slices
slices = image_data.slice_orthogonal()
plotter.add_mesh(slices[0], cmap="gray")  # YZ plane
plotter.add_mesh(slices[1], cmap="gray")  # XZ plane
plotter.add_mesh(slices[2], cmap="gray")  # XY plane

plotter.show()
```

### Volume Rendering

```python
# Advanced volume rendering
image_data = wrap_vtk("microscopy.zarr", "raw")

# Create custom opacity function
opacity = [
    [0, 0.0],      # Transparent background
    [50, 0.0],     # 
    [100, 0.1],    # Semi-transparent
    [200, 0.9],    # Nearly opaque
    [255, 1.0]     # Fully opaque
]

plotter = pv.Plotter()
plotter.add_volume(
    image_data,
    cmap="hot",
    opacity=opacity,
    shade=True
)
plotter.show()
```

## Working with Large Data

### Downsampling for Visualization

```python
import numpy as np
from zarr_utils.visualization import wrap_vtk

def visualize_downsampled(zarr_path, array_name, factor=4):
    """Downsample large data for visualization."""
    # Load with zarr
    import zarr
    arr = zarr.open_array(f"{zarr_path}/{array_name}", mode='r')
    
    # Downsample
    downsampled = arr[::factor, ::factor, ::factor]
    
    # Create temporary array
    temp_arr = zarr.open_array(
        "temp_vis.zarr", 
        mode='w', 
        shape=downsampled.shape,
        chunks=(64, 64, 64)
    )
    temp_arr[:] = downsampled
    temp_arr.attrs['spacing'] = [s * factor for s in arr.attrs.get('spacing', [1, 1, 1])]
    
    # Visualize
    return wrap_vtk("temp_vis.zarr", "")
```

### Cropping Regions

```python
def visualize_roi(zarr_path, array_name, roi):
    """Visualize a region of interest."""
    z_start, z_end, y_start, y_end, x_start, x_end = roi
    
    # Load region
    arr = zarr.open_array(f"{zarr_path}/{array_name}")
    roi_data = arr[z_start:z_end, y_start:y_end, x_start:x_end]
    
    # Create VTK object
    import vtk
    from vtk.util import numpy_support
    
    vtk_data = vtk.vtkImageData()
    vtk_data.SetDimensions(roi_data.shape[::-1])
    vtk_data.SetSpacing(arr.attrs.get('spacing', [1, 1, 1])[::-1])
    
    flat_data = roi_data.flatten('F')
    vtk_array = numpy_support.numpy_to_vtk(flat_data)
    vtk_data.GetPointData().SetScalars(vtk_array)
    
    return vtk_data
```

## Multi-channel Visualization

### Separate Channels

```python
# Load multi-channel data
channels = []
for i in range(3):
    channel = wrap_vtk("multichannel.zarr", f"channel_{i}")
    channels.append(channel)

# Visualize each channel
plotter = pv.Plotter(shape=(1, 3))

for i, (channel, cmap) in enumerate(zip(channels, ['red', 'green', 'blue'])):
    plotter.subplot(0, i)
    plotter.add_volume(channel, cmap=cmap)
    plotter.add_text(f"Channel {i}", position='upper_edge')

plotter.link_views()
plotter.show()
```

### RGB Composite

```python
def create_rgb_composite(zarr_path, channel_names, output_path):
    """Create RGB composite from separate channels."""
    import numpy as np
    from zarr_utils import open_xarray
    import pyvista as pv
    
    # Load channels
    channels = []
    for name in channel_names:
        ds = open_xarray(zarr_path, name)
        channels.append(ds.values.values)
    
    # Stack as RGB
    rgb = np.stack(channels, axis=-1)
    
    # Normalize to 0-255
    for i in range(3):
        channel = rgb[..., i]
        rgb[..., i] = ((channel - channel.min()) / 
                      (channel.max() - channel.min()) * 255).astype(np.uint8)
    
    # Create VTK image
    image = pv.ImageData(dimensions=rgb.shape[:3])
    image["RGB"] = rgb.reshape(-1, 3, order='F')
    
    # Save
    image.save(output_path)
    return image
```

## Animation

### Time Series

```python
def create_time_series_animation(zarr_paths, output_gif):
    """Create animation from time series."""
    import pyvista as pv
    
    plotter = pv.Plotter(off_screen=True)
    
    # Load first frame
    mesh = wrap_vtk(zarr_paths[0], "data")
    actor = plotter.add_volume(mesh, cmap="viridis")
    
    # Open GIF writer
    plotter.open_gif(output_gif)
    
    # Animate through time points
    for path in zarr_paths:
        mesh = wrap_vtk(path, "data")
        actor.mapper.SetInputData(mesh)
        plotter.write_frame()
    
    plotter.close()
```

### Rotating View

```python
def create_rotation_animation(zarr_path, array_name, output_gif):
    """Create rotating view animation."""
    image = wrap_vtk(zarr_path, array_name)
    
    plotter = pv.Plotter(off_screen=True)
    plotter.add_volume(image, cmap="bone", opacity="sigmoid")
    
    # Set initial view
    plotter.camera_position = 'iso'
    plotter.camera.zoom(1.5)
    
    # Create rotation
    plotter.open_gif(output_gif)
    for angle in range(0, 360, 2):
        plotter.camera.azimuth = angle
        plotter.write_frame()
    plotter.close()
```

## Export Options

### ParaView Compatible

```python
# Export for ParaView
from zarr_utils.visualization import to_vti

# Standard export
to_vti("data.zarr", "volume", "paraview_data.vti")

# With metadata
import zarr
arr = zarr.open_array("data.zarr/volume")
spacing = arr.attrs.get('spacing', [1, 1, 1])
to_vti("data.zarr", "volume", "paraview_data.vti", spacing=spacing)
```

### Other Formats

```python
# Convert to other formats using PyVista
image = wrap_vtk("data.zarr", "volume")

# Export to various formats
image.save("data.vti")      # VTK ImageData
image.save("data.vts")      # VTK StructuredGrid  
image.save("data.vtk")      # Legacy VTK
image.save("data.nrrd")     # NRRD format
image.save("data.mha")      # MetaImage
```

## Performance Optimization

### Memory Management

```python
def visualize_large_data_efficiently(zarr_path, array_name):
    """Efficiently visualize large datasets."""
    import zarr
    import dask.array as da
    
    # Open as dask array
    arr = zarr.open_array(f"{zarr_path}/{array_name}", mode='r')
    dask_arr = da.from_zarr(arr)
    
    # Compute statistics for color mapping
    vmin = float(dask_arr.min())
    vmax = float(dask_arr.max())
    
    # Load in chunks for visualization
    chunk_size = 256
    for z in range(0, arr.shape[0], chunk_size):
        chunk = arr[z:z+chunk_size]
        # Visualize chunk...
```

### GPU Acceleration

```python
# Use GPU for volume rendering
plotter = pv.Plotter()
plotter.add_volume(
    image_data,
    cmap="viridis",
    opacity="sigmoid",
    mapper='gpu'  # Use GPU volume mapper
)
```

## Integration with Notebooks

### Jupyter Visualization

```python
# For Jupyter notebooks
import pyvista as pv
pv.set_jupyter_backend('panel')  # or 'ipygany' or 'pythreejs'

# Create interactive widget
image = wrap_vtk("data.zarr", "volume")
plotter = pv.Plotter()
plotter.add_volume(image)
plotter.show()  # Shows inline in notebook
```

### Static Images

```python
# Generate static images for reports
plotter = pv.Plotter(off_screen=True)
plotter.add_volume(image, cmap="viridis")
plotter.camera_position = 'xy'
plotter.screenshot("figure1.png", transparent_background=True)
```

## Best Practices

1. **Downsample large data** - Don't try to visualize full resolution
2. **Use appropriate color maps** - Match to your data type
3. **Save camera positions** - For reproducible views
4. **Export at appropriate resolution** - Balance quality and file size
5. **Consider your audience** - Interactive vs static visualization

## Troubleshooting

### Memory Errors

```python
# If you get memory errors, reduce data size
def safe_visualize(zarr_path, array_name, max_size=512):
    """Safely visualize with size limits."""
    arr = zarr.open_array(f"{zarr_path}/{array_name}")
    
    # Calculate downsampling needed
    factors = []
    for dim_size in arr.shape:
        factor = max(1, dim_size // max_size)
        factors.append(factor)
    
    # Load downsampled
    slices = tuple(slice(None, None, f) for f in factors)
    data = arr[slices]
    
    # Adjust spacing
    original_spacing = arr.attrs.get('spacing', [1, 1, 1])
    new_spacing = [s * f for s, f in zip(original_spacing, factors)]
    
    # Create temporary array for visualization
    # ... continue with visualization
```

### Display Issues

```python
# If visualization doesn't appear
import pyvista as pv

# Check backend
print(f"Current backend: {pv.global_theme.jupyter_backend}")

# Try different backend
pv.set_jupyter_backend('static')  # Fallback option

# For headless systems
pv.start_xvfb()  # Start virtual display
```