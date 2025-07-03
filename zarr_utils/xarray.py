import numpy as np
import zarr
import xarray as xr
import fsspec


def get_voxel_spacing(zarr_obj, default=(1.0, 1.0, 1.0)):
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
    try:
        spacing = zarr_obj.attrs["pixelResolution"]["dimensions"]
        return tuple(spacing)
    except Exception:
        return default


def open_xarray(store_url, group, var_name="values", anon=True, with_coords=True):
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
    full_url = f"{store_url.rstrip('/')}/{group.strip('/')}"
    z = zarr.open_array(full_url, mode="r", storage_options={"anon": anon})
    
    shape = z.shape
    if len(shape) != 3:
        raise ValueError(f"Expected 3D array, got shape {shape}")

    dims = ["z", "y", "x"]
    spacing_nm = get_voxel_spacing(z)

    coords = {}
    if with_coords:
        for dim, size, spacing in zip(dims, shape, spacing_nm):
            coords[dim] = np.arange(size) * spacing * 1e-9  # convert nm → meters

    da = xr.DataArray(z, dims=dims, coords=coords if with_coords else None, attrs=dict(z.attrs))
    return xr.Dataset({var_name: da})