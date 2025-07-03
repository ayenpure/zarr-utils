import math
from pathlib import PurePosixPath

import fsspec
import zarr
import numpy as np


def _sizeof_fmt(num_bytes, suffix="B"):
    """Pretty-print bytes (e.g. 1.43 GB)."""
    if num_bytes == 0:
        return "0 B"
    magnitude = int(math.log(num_bytes, 1024))
    power = 1024**magnitude
    val = num_bytes / power
    unit = " KMGTPE"[magnitude]
    return f"{val:5.2f} {unit}{suffix}"


def _walk_group(group, path=""):
    """Yield (path, shape, dtype, nbytes) for every array in the Zarr group."""
    for name, array in group.arrays():
        full = f"{path}/{name}" if path else name
        nbytes = array.dtype.itemsize * int(np.prod(array.shape))
        yield full, array.shape, array.dtype, nbytes
    for name, sub in group.groups():
        sub_path = f"{path}/{name}" if path else name
        yield from _walk_group(sub, sub_path)


def list_zarr_arrays(store_url, anon=True):
    """
    List all arrays in a Zarr store, including nested groups.

    Parameters
    ----------
    store_url : str
        Path or S3 URL to a Zarr store or group
    anon : bool
        If using a remote store (e.g. S3), set to True for anonymous access

    Returns
    -------
    List of dictionaries with keys: path, shape, dtype, size_bytes
    """
    mapper = fsspec.get_mapper(store_url, anon=anon)
    try:
        root = zarr.open_consolidated(mapper, mode="r")
    except Exception:
        # Fallback for stores without .zmetadata
        root = zarr.open_group(mapper, mode="r")

    arrays = []
    for path, shape, dtype, nbytes in _walk_group(root):
        arrays.append({
            "path": path,
            "shape": shape,
            "dtype": str(dtype),
            "size_bytes": nbytes,
        })

    # Sort by size descending
    arrays.sort(key=lambda a: a["size_bytes"], reverse=True)
    return arrays


def inspect_zarr_store(store_url, anon=True, summarize=True):
    """
    Print summary and return metadata for all arrays in a Zarr store.

    Parameters
    ----------
    store_url : str
        Path or S3 URL to a Zarr store or group
    anon : bool
        If using a remote store (e.g. S3), set to True for anonymous access
    summarize : bool
        If True, prints formatted summary

    Returns
    -------
    Dict[str, dict]
        Dictionary keyed by array path, with metadata for each array
    """
    arrays = list_zarr_arrays(store_url, anon=anon)
    result = {}
    total = 0
    if summarize:
        print(f"\nInspecting Zarr store: {PurePosixPath(store_url).name}")
    for arr in arrays:
        total += arr["size_bytes"]
        result[arr["path"]] = arr
        if summarize:
            print(f"  {arr['path']:<30} {arr['shape']!s:<20} {arr['dtype']}  {_sizeof_fmt(arr['size_bytes'])}")
    if summarize:
        print(f"  Total logical size: {_sizeof_fmt(total)}")
    return result