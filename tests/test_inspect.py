import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest
import zarr

from zarr_utils.compat import create_array_compat
from zarr_utils.inspect import _sizeof_fmt, _walk_group, inspect_zarr_store, list_zarr_arrays


class TestSizeFormat:
    """Test the _sizeof_fmt function."""

    def test_zero_bytes(self):
        assert _sizeof_fmt(0) == "0 B"

    def test_bytes(self):
        assert _sizeof_fmt(100) == "100.00  B"
        assert _sizeof_fmt(1023) == "1023.00  B"

    def test_kilobytes(self):
        assert _sizeof_fmt(1024) == " 1.00 KB"
        assert _sizeof_fmt(1536) == " 1.50 KB"

    def test_megabytes(self):
        assert _sizeof_fmt(1024 * 1024) == " 1.00 MB"
        assert _sizeof_fmt(1024 * 1024 * 2.5) == " 2.50 MB"

    def test_gigabytes(self):
        assert _sizeof_fmt(1024**3) == " 1.00 GB"

    def test_negative_bytes_error(self):
        with pytest.raises(ValueError, match="Negative size not supported"):
            _sizeof_fmt(-100)


class TestZarrInspection:
    """Test Zarr inspection functionality."""

    @pytest.fixture
    def temp_zarr_store(self):
        """Create a temporary Zarr store for testing."""
        temp_dir = tempfile.mkdtemp()
        store_path = Path(temp_dir) / "test.zarr"

        # Create a Zarr store with nested groups and arrays
        store = zarr.open_group(str(store_path), mode="w")

        # Root level array
        data1 = np.random.rand(100, 200)
        create_array_compat(store, "array1", data=data1, chunks=(50, 50))

        # Nested group with arrays
        group1 = store.create_group("group1")
        data2 = np.random.rand(50, 50, 50)
        create_array_compat(group1, "array2", data=data2, chunks=(25, 25, 25))
        group1.attrs["test_attr"] = "test_value"

        # Deeper nesting
        group2 = group1.create_group("subgroup")
        data3 = np.random.rand(10, 10)
        create_array_compat(group2, "array3", data=data3, chunks=(5, 5))

        yield str(store_path)

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_walk_group(self, temp_zarr_store):
        """Test walking through Zarr groups."""
        store = zarr.open_group(temp_zarr_store, mode="r")

        results = list(_walk_group(store))

        # Should find 3 arrays
        assert len(results) == 3

        # Check array paths
        paths = [r[0] for r in results]
        assert "array1" in paths
        assert "group1/array2" in paths
        assert "group1/subgroup/array3" in paths

        # Check shapes
        for path, shape, _dtype, _nbytes in results:
            if path == "array1":
                assert shape == (100, 200)
            elif path == "group1/array2":
                assert shape == (50, 50, 50)
            elif path == "group1/subgroup/array3":
                assert shape == (10, 10)

    def test_list_zarr_arrays(self, temp_zarr_store):
        """Test listing arrays in a Zarr store."""
        arrays = list_zarr_arrays(temp_zarr_store)

        assert len(arrays) == 3

        # Should be sorted by size (descending)
        assert arrays[0]["path"] == "group1/array2"  # Largest
        assert arrays[1]["path"] == "array1"
        assert arrays[2]["path"] == "group1/subgroup/array3"  # Smallest

        # Check data structure
        for arr in arrays:
            assert "path" in arr
            assert "shape" in arr
            assert "dtype" in arr
            assert "size_bytes" in arr

    def test_inspect_zarr_store(self, temp_zarr_store, capsys):
        """Test inspecting and summarizing a Zarr store."""
        result = inspect_zarr_store(temp_zarr_store, summarize=True)

        # Check returned dictionary
        assert len(result) == 3
        assert "array1" in result
        assert "group1/array2" in result
        assert "group1/subgroup/array3" in result

        # Check printed output
        captured = capsys.readouterr()
        assert "Inspecting Zarr store: test.zarr" in captured.out
        assert "Total logical size:" in captured.out
        assert "array1" in captured.out
        assert "group1/array2" in captured.out

    def test_inspect_zarr_store_no_summary(self, temp_zarr_store, capsys):
        """Test inspecting without summary."""
        result = inspect_zarr_store(temp_zarr_store, summarize=False)

        assert len(result) == 3

        # Should not print anything
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_single_array_store(self):
        """Test with a store containing a single array."""
        with tempfile.TemporaryDirectory() as temp_dir:
            array_path = Path(temp_dir) / "single_array.zarr"

            # Create single array
            arr = zarr.open_array(
                str(array_path), mode="w", shape=(100, 100), chunks=(50, 50), dtype="f8"
            )
            arr[:] = np.random.rand(100, 100)

            # List arrays should handle single array
            arrays = list_zarr_arrays(str(array_path))
            assert len(arrays) == 1
            assert arrays[0]["path"] == "array"
            assert arrays[0]["shape"] == (100, 100)

    def test_consolidated_metadata(self):
        """Test handling of consolidated metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "consolidated.zarr"

            # Create store and consolidate
            store = zarr.open_group(str(store_path), mode="w")
            data = np.arange(100)
            create_array_compat(store, "data", data=data)
            zarr.consolidate_metadata(str(store_path))

            # Should open with consolidated metadata
            arrays = list_zarr_arrays(str(store_path))
            assert len(arrays) == 1
            assert arrays[0]["path"] == "data"

    def test_empty_store(self):
        """Test with empty Zarr store."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "empty.zarr"

            # Create empty group
            zarr.open_group(str(store_path), mode="w")

            arrays = list_zarr_arrays(str(store_path))
            assert len(arrays) == 0

    def test_storage_options(self):
        """Test custom storage options."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "test.zarr"

            store = zarr.open_group(str(store_path), mode="w")
            data = np.arange(100)
            create_array_compat(store, "data", data=data)

            # Should work with storage options
            arrays = list_zarr_arrays(str(store_path), storage_options={"mode": "r"})
            assert len(arrays) == 1
