from typing import Any, Optional, Union

import numpy as np
import xarray as xr
import zarr

from .compat import open_array_with_storage_options, open_group_with_storage_options


def get_voxel_spacing(
    zarr_obj: Union[zarr.Array, zarr.Group], default: tuple[float, float, float] = (1.0, 1.0, 1.0)
) -> tuple[float, float, float]:
    """
    Extract voxel spacing in nanometers from Zarr array/group attributes.

    Parameters
    ----------
    zarr_obj : zarr.Array or zarr.Group
        Opened Zarr array or group
    default : tuple[float, float, float]
        Fallback voxel size if not specified

    Returns
    -------
    tuple[float, float, float]
        Spacing in nanometers: (z, y, x)
    """
    # Check for common metadata formats
    attrs = zarr_obj.attrs

    # Format 1: pixelResolution.dimensions
    if "pixelResolution" in attrs and isinstance(attrs["pixelResolution"], dict):
        if "dimensions" in attrs["pixelResolution"]:
            try:
                spacing = attrs["pixelResolution"]["dimensions"]
                if len(spacing) == 3:
                    return tuple(float(s) for s in spacing)
            except (ValueError, TypeError):
                pass

    # Format 2: Direct spacing/resolution attributes
    for key in ["spacing", "resolution", "voxel_size", "voxelSize"]:
        if key in attrs:
            try:
                spacing = attrs[key]
                if len(spacing) == 3:
                    return tuple(float(s) for s in spacing)
            except (ValueError, TypeError):
                pass

    # Format 3: Individual axis attributes
    try:
        spacing = []
        for axis in ["z", "y", "x"]:
            for key in [f"{axis}_spacing", f"{axis}_resolution", f"{axis}Resolution"]:
                if key in attrs:
                    spacing.append(float(attrs[key]))
                    break
        if len(spacing) == 3:
            return tuple(spacing)
    except (ValueError, TypeError):
        pass

    return default


def open_xarray(
    store_url: str,
    group: str,
    var_name: str = "values",
    anon: bool = True,
    with_coords: bool = True,
    storage_options: Optional[dict[str, Any]] = None,
) -> xr.Dataset:
    """
    Open a 3D Zarr array as an xarray.Dataset with optional physical coordinates.

    Parameters
    ----------
    store_url : str
        URL to Zarr root (local or remote), e.g. "s3://bucket/my.zarr"
    group : str
        Group path within the Zarr store, e.g. "aligned/s2"
    var_name : str
        Name to assign to the xarray variable
    anon : bool
        If using remote object store (S3), use anonymous access
    with_coords : bool
        If True, attach real-world coordinates (in meters) using pixel spacing

    Returns
    -------
    xr.Dataset
    """
    # Clean and combine URLs
    store_url = store_url.rstrip("/")
    group = group.strip("/")
    full_url = f"{store_url}/{group}" if group else store_url

    # Merge storage options
    opts = {"anon": anon}
    if storage_options:
        opts.update(storage_options)

    # Try to open as array or group
    z = None
    try:
        z = open_array_with_storage_options(full_url, mode="r", storage_options=opts)
    except Exception as e:
        # Try opening as a group and look for a data array
        try:
            g = open_group_with_storage_options(full_url, mode="r", storage_options=opts)
            # Look for common data array names
            array_names = list(g.array_keys()) if hasattr(g, "array_keys") else list(g.keys())

            if not array_names:
                raise ValueError(f"No arrays found in group at '{full_url}'")

            # Try common names first
            for name in ["data", "values", "array", "0"]:
                if name in array_names:
                    z = g[name]
                    break
            else:
                # Use the first available array
                z = g[array_names[0]]
        except Exception as group_error:
            raise ValueError(
                f"Failed to open '{full_url}' as array or group. Array error: {str(e)}. Group error: {str(group_error)}"
            ) from group_error

    if z is None:
        raise ValueError(f"Could not open zarr data at '{full_url}'")

    shape = z.shape
    ndim = len(shape)

    # Handle different dimensionalities
    if ndim == 2:
        dims = ["y", "x"]
        # Will add z dimension later in xarray
        needs_z_dim = True
    elif ndim == 3:
        dims = ["z", "y", "x"]
        needs_z_dim = False
    elif ndim == 4:
        # Assume channel/time is first dimension
        dims = ["c", "z", "y", "x"]
        needs_z_dim = False
    else:
        raise ValueError(f"Unsupported array dimensionality: {ndim}D (shape: {shape})")

    spacing_nm = get_voxel_spacing(z)

    # Extend spacing for higher dimensions
    if ndim == 4:
        spacing_nm = (1.0,) + spacing_nm  # No spacing for channel dimension
    elif ndim == 2:
        spacing_nm = spacing_nm[1:]  # Only y, x spacing

    coords = {}
    if with_coords:
        if ndim == 2:
            # For 2D arrays, manually handle y and x
            coords["y"] = np.arange(shape[0]) * spacing_nm[0] * 1e-9
            coords["x"] = np.arange(shape[1]) * spacing_nm[1] * 1e-9
        else:
            for i, (dim, size) in enumerate(zip(dims, shape)):
                if dim == "c":
                    coords[dim] = np.arange(size)  # Channel numbers
                else:
                    # Get appropriate spacing
                    spacing_idx = i
                    spacing = spacing_nm[spacing_idx] if spacing_idx < len(spacing_nm) else 1.0
                    coords[dim] = np.arange(size) * spacing * 1e-9  # convert nm → meters

    # Create DataArray with chunking information
    da = xr.DataArray(z, dims=dims, coords=coords if with_coords else None, attrs=dict(z.attrs))

    # Add z dimension if needed (for 2D arrays)
    if ndim == 2 and needs_z_dim:
        # Add z coordinate
        z_coord = np.array([0.0]) if with_coords else None
        da = da.expand_dims({"z": z_coord}, axis=0)

    # Add metadata about chunking
    if hasattr(z, "chunks"):
        da.attrs["zarr_chunks"] = z.chunks
    elif hasattr(z, "chunk_shape"):
        da.attrs["zarr_chunks"] = z.chunk_shape

    dataset = xr.Dataset({var_name: da})

    # Add dataset-level attributes
    dataset.attrs["source_url"] = full_url
    dataset.attrs["voxel_spacing_nm"] = spacing_nm

    return dataset
