"""Compatibility layer for Zarr v2 and v3."""
from typing import Optional

import zarr

# Detect Zarr version
ZARR_VERSION = tuple(int(x) for x in zarr.__version__.split('.')[:2])
IS_ZARR_V3 = ZARR_VERSION[0] >= 3


def get_store_from_mapper(mapper):
    """Get the underlying store from a mapper."""
    if IS_ZARR_V3:
        # In v3, mapper is the store itself
        return mapper
    else:
        # In v2, we might need to access the store differently
        return mapper


def consolidate_metadata(store_or_mapper, metadata_key: str = '.zmetadata'):
    """Consolidate metadata in a version-compatible way."""
    if IS_ZARR_V3:
        # v3 doesn't accept metadata_key parameter
        return zarr.consolidate_metadata(store_or_mapper)
    else:
        # v2 accepts metadata_key
        return zarr.consolidate_metadata(store_or_mapper, metadata_key=metadata_key)


def open_array_with_storage_options(store_path: str, mode: str = 'r', storage_options: Optional[dict] = None, **kwargs):
    """Open array with storage options in a version-compatible way."""
    if IS_ZARR_V3:
        # v3 only accepts storage_options for fsspec stores
        if store_path.startswith(('s3://', 'gs://', 'az://', 'http://', 'https://')):
            return zarr.open_array(store_path, mode=mode, storage_options=storage_options, **kwargs)
        else:
            # For local paths, don't pass storage_options
            return zarr.open_array(store_path, mode=mode, **kwargs)
    else:
        # v2 also only accepts storage_options for fsspec stores
        if store_path.startswith(('s3://', 'gs://', 'az://', 'http://', 'https://')):
            return zarr.open_array(store_path, mode=mode, storage_options=storage_options, **kwargs)
        else:
            # For local paths, don't pass storage_options
            return zarr.open_array(store_path, mode=mode, **kwargs)


def open_group_with_storage_options(store_path: str, mode: str = 'r', storage_options: Optional[dict] = None, **kwargs):
    """Open group with storage options in a version-compatible way."""
    if IS_ZARR_V3:
        # v3 only accepts storage_options for fsspec stores
        if store_path.startswith(('s3://', 'gs://', 'az://', 'http://', 'https://')):
            return zarr.open_group(store_path, mode=mode, storage_options=storage_options, **kwargs)
        else:
            # For local paths, don't pass storage_options
            return zarr.open_group(store_path, mode=mode, **kwargs)
    else:
        # v2 also only accepts storage_options for fsspec stores
        if store_path.startswith(('s3://', 'gs://', 'az://', 'http://', 'https://')):
            return zarr.open_group(store_path, mode=mode, storage_options=storage_options, **kwargs)
        else:
            # For local paths, don't pass storage_options
            return zarr.open_group(store_path, mode=mode, **kwargs)


def get_array_compressor(array):
    """Get compressor from array in a version-compatible way."""
    if IS_ZARR_V3:
        # v3 uses compressors property (list)
        try:
            compressors = array.compressors
            if compressors and len(compressors) > 0:
                # Return first compressor's name
                return compressors[0].__class__.__name__.lower()
            return None
        except Exception:
            return None
    else:
        # v2 uses compressor property
        if hasattr(array, 'compressor') and array.compressor:
            return array.compressor.codec_id
        return None


def access_store_item(store, key: str):
    """Access item from store in a version-compatible way."""
    if IS_ZARR_V3:
        # v3 store access might differ
        if hasattr(store, 'get'):
            return store.get(key)
        elif hasattr(store, '__getitem__'):
            try:
                return store[key]
            except KeyError:
                return None
        else:
            return None
    else:
        # v2 store access
        if key in store:
            return store[key]
        return None


def store_contains(store, key: str) -> bool:
    """Check if store contains key in a version-compatible way."""
    if IS_ZARR_V3:
        # v3 might not support 'in' operator for all store types
        try:
            if hasattr(store, '__contains__'):
                return key in store
            elif hasattr(store, 'get'):
                return store.get(key) is not None
            else:
                # Try to access and catch exception
                try:
                    _ = store[key]
                    return True
                except Exception:
                    return False
        except Exception:
            return False
    else:
        # v2 supports 'in' operator
        return key in store


def create_array_compat(group, name: str, data=None, shape=None, dtype=None, chunks=None, **kwargs):
    """Create array in a version-compatible way."""
    if data is not None:
        if shape is None:
            shape = data.shape
        if dtype is None:
            dtype = data.dtype
        if chunks is None:
            # Default chunking
            chunks = tuple(min(1000, s) for s in shape)

    if IS_ZARR_V3:
        # v3 requires shape and dtype
        if shape is None or dtype is None:
            raise ValueError("For Zarr v3, shape and dtype must be specified")
        arr = group.create_array(name, shape=shape, dtype=dtype, chunks=chunks, **kwargs)
        if data is not None:
            arr[:] = data
        return arr
    else:
        # v2 can accept data parameter directly
        if data is not None:
            return group.create_dataset(name, data=data, chunks=chunks, **kwargs)
        else:
            return group.create_dataset(name, shape=shape, dtype=dtype, chunks=chunks, **kwargs)

