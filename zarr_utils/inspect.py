import math
from collections.abc import Generator
from pathlib import PurePosixPath
from typing import Any, Optional

import fsspec
import numpy as np
import zarr


def _sizeof_fmt(num_bytes: int, suffix: str = "B") -> str:
    """Pretty-print bytes (e.g. 1.43 GB).

    Parameters
    ----------
    num_bytes : int
        Number of bytes to format
    suffix : str, optional
        Suffix to append (default: "B")

    Returns
    -------
    str
        Human-readable size string
    """
    if num_bytes == 0:
        return "0 B"
    if num_bytes < 0:
        raise ValueError(f"Negative size not supported: {num_bytes}")

    magnitude = int(math.log(num_bytes, 1024))
    power = 1024**magnitude
    val = num_bytes / power
    unit = " KMGTPE"[magnitude]
    return f"{val:5.2f} {unit}{suffix}"


def _walk_group(
    group: zarr.Group, path: str = ""
) -> Generator[tuple[str, tuple[int, ...], np.dtype, int], None, None]:
    """Yield (path, shape, dtype, nbytes) for every array in the Zarr group.

    Parameters
    ----------
    group : zarr.Group
        Zarr group to walk
    path : str, optional
        Current path prefix

    Yields
    ------
    Tuple[str, Tuple[int, ...], np.dtype, int]
        Array path, shape, dtype, and size in bytes
    """
    try:
        for name, array in group.arrays():
            full = f"{path}/{name}" if path else name
            nbytes = array.dtype.itemsize * int(np.prod(array.shape))
            yield full, array.shape, array.dtype, nbytes
        for name, sub in group.groups():
            sub_path = f"{path}/{name}" if path else name
            yield from _walk_group(sub, sub_path)
    except Exception as e:
        # Log the error but continue walking other arrays
        import warnings

        warnings.warn(f"Error walking group at path '{path}': {str(e)}", stacklevel=2)


def list_zarr_arrays(
    store_url: str, anon: bool = True, storage_options: Optional[dict[str, Any]] = None
) -> list[dict[str, Any]]:
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
    # Merge storage options
    opts = {"anon": anon}
    if storage_options:
        opts.update(storage_options)

    mapper = fsspec.get_mapper(store_url, **opts)

    # Try multiple strategies to open the store
    root = None
    errors = []

    # Strategy 1: Try consolidated metadata
    try:
        root = zarr.open_consolidated(mapper, mode="r")
    except Exception as e:
        errors.append(("consolidated", str(e)))

    # Strategy 2: Try as group
    if root is None:
        try:
            root = zarr.open_group(mapper, mode="r")
        except Exception as e:
            errors.append(("group", str(e)))

    # Strategy 3: Try as array
    if root is None:
        try:
            arr = zarr.open_array(mapper, mode="r")
            # Wrap single array in a fake group structure
            arrays = [
                {
                    "path": "array",
                    "shape": arr.shape,
                    "dtype": str(arr.dtype),
                    "size_bytes": arr.dtype.itemsize * int(np.prod(arr.shape)),
                }
            ]
            return arrays
        except Exception as e:
            errors.append(("array", str(e)))

    if root is None:
        error_msg = "Failed to open Zarr store. Tried:\n"
        for method, error in errors:
            error_msg += f"  - {method}: {error}\n"
        raise ValueError(error_msg)

    arrays = []
    for path, shape, dtype, nbytes in _walk_group(root):
        arrays.append(
            {
                "path": path,
                "shape": shape,
                "dtype": str(dtype),
                "size_bytes": nbytes,
            }
        )

    # Sort by size descending
    arrays.sort(key=lambda a: a["size_bytes"], reverse=True)
    return arrays


def inspect_zarr_store(
    store_url: str,
    anon: bool = True,
    summarize: bool = True,
    storage_options: Optional[dict[str, Any]] = None,
) -> dict[str, dict[str, Any]]:
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
    arrays = list_zarr_arrays(store_url, anon=anon, storage_options=storage_options)
    result = {}
    total = 0
    if summarize:
        store_name = PurePosixPath(store_url).name or store_url
        print(f"\nInspecting Zarr store: {store_name}")
        print(f"  Arrays found: {len(arrays)}")
    for arr in arrays:
        total += arr["size_bytes"]
        result[arr["path"]] = arr
        if summarize:
            print(
                f"  {arr['path']:<30} {arr['shape']!s:<20} {arr['dtype']}  {_sizeof_fmt(arr['size_bytes'])}"
            )
    if summarize:
        print(f"  Total logical size: {_sizeof_fmt(total)}")
    return result
