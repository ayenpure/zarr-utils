import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest
import zarr

from zarr_utils.compat import create_array_compat
from zarr_utils.xarray import get_voxel_spacing, open_xarray


class TestVoxelSpacing:
    """Test voxel spacing extraction."""

    def test_pixelresolution_format(self):
        """Test standard pixelResolution format."""

        # Mock zarr object with attrs
        class MockZarr:
            attrs = {"pixelResolution": {"dimensions": [40.0, 20.0, 20.0]}}

        spacing = get_voxel_spacing(MockZarr())
        assert spacing == (40.0, 20.0, 20.0)

    def test_direct_spacing_attribute(self):
        """Test direct spacing attribute."""

        class MockZarr:
            attrs = {"spacing": [1.0, 2.0, 3.0]}

        spacing = get_voxel_spacing(MockZarr())
        assert spacing == (1.0, 2.0, 3.0)

    def test_voxel_size_attribute(self):
        """Test voxelSize attribute."""

        class MockZarr:
            attrs = {"voxelSize": [10, 20, 30]}

        spacing = get_voxel_spacing(MockZarr())
        assert spacing == (10.0, 20.0, 30.0)

    def test_individual_axis_attributes(self):
        """Test individual axis spacing attributes."""

        class MockZarr:
            attrs = {"z_spacing": 5.0, "y_resolution": 2.5, "xResolution": 1.25}

        spacing = get_voxel_spacing(MockZarr())
        assert spacing == (5.0, 2.5, 1.25)

    def test_default_spacing(self):
        """Test fallback to default spacing."""

        class MockZarr:
            attrs = {}

        spacing = get_voxel_spacing(MockZarr())
        assert spacing == (1.0, 1.0, 1.0)

        # Test custom default
        spacing = get_voxel_spacing(MockZarr(), default=(2.0, 3.0, 4.0))
        assert spacing == (2.0, 3.0, 4.0)

    def test_invalid_spacing_values(self):
        """Test handling of invalid spacing values."""

        class MockZarr:
            attrs = {"pixelResolution": {"dimensions": ["not", "a", "number"]}}

        spacing = get_voxel_spacing(MockZarr())
        assert spacing == (1.0, 1.0, 1.0)  # Should fall back to default


class TestOpenXarray:
    """Test opening Zarr arrays as xarray Datasets."""

    @pytest.fixture
    def temp_zarr_3d(self):
        """Create a temporary 3D Zarr array."""
        temp_dir = tempfile.mkdtemp()
        store_path = Path(temp_dir) / "test3d.zarr"

        # Create 3D array with attributes
        arr = zarr.open_array(
            str(store_path), mode="w", shape=(10, 20, 30), chunks=(5, 10, 15), dtype="f4"
        )
        arr[:] = np.random.rand(10, 20, 30)
        arr.attrs["pixelResolution"] = {
            "dimensions": [100.0, 50.0, 50.0]  # nm
        }
        arr.attrs["test_attr"] = "test_value"

        yield str(store_path)

        shutil.rmtree(temp_dir)

    @pytest.fixture
    def temp_zarr_group(self):
        """Create a temporary Zarr group with arrays."""
        temp_dir = tempfile.mkdtemp()
        store_path = Path(temp_dir) / "test_group.zarr"

        store = zarr.open_group(str(store_path), mode="w")

        # Create group with data array
        group = store.create_group("mygroup")
        data = np.random.rand(5, 10, 15)
        arr = create_array_compat(group, "data", data=data, chunks=(5, 5, 5))
        arr.attrs["spacing"] = [2.0, 1.0, 1.0]

        yield str(store_path)

        shutil.rmtree(temp_dir)

    def test_open_3d_array_with_coords(self, temp_zarr_3d):
        """Test opening 3D array with coordinates."""
        ds = open_xarray(temp_zarr_3d, "", with_coords=True)

        # Check dataset structure
        assert "values" in ds
        assert ds["values"].shape == (10, 20, 30)
        assert list(ds["values"].dims) == ["z", "y", "x"]

        # Check coordinates (converted from nm to meters)
        assert "z" in ds.coords
        assert "y" in ds.coords
        assert "x" in ds.coords

        # Check spacing conversion (100nm -> 100e-9 m)
        np.testing.assert_almost_equal(ds.coords["z"].values[1] - ds.coords["z"].values[0], 100e-9)

    def test_open_3d_array_without_coords(self, temp_zarr_3d):
        """Test opening 3D array without coordinates."""
        ds = open_xarray(temp_zarr_3d, "", with_coords=False)

        assert "values" in ds
        assert ds["values"].shape == (10, 20, 30)
        assert len(ds.coords) == 0  # No coordinates

    def test_open_array_in_group(self, temp_zarr_group):
        """Test opening array within a group."""
        ds = open_xarray(temp_zarr_group, "mygroup/data", var_name="mydata")

        assert "mydata" in ds
        assert ds["mydata"].shape == (5, 10, 15)

        # Check spacing from attrs
        np.testing.assert_almost_equal(
            ds.coords["z"].values[1] - ds.coords["z"].values[0],
            2.0e-9,  # 2nm -> 2e-9 m
        )

    def test_open_2d_array(self):
        """Test opening 2D array (should add z dimension)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            array_path = Path(temp_dir) / "test2d.zarr"

            # Create 2D array
            arr = zarr.open_array(str(array_path), mode="w", shape=(100, 200), chunks=(50, 100))
            arr[:] = np.random.rand(100, 200)

            ds = open_xarray(str(array_path), "")

            # Should have z dimension added
            assert ds["values"].shape == (1, 100, 200)
            assert list(ds["values"].dims) == ["z", "y", "x"]

    def test_open_4d_array(self):
        """Test opening 4D array."""
        with tempfile.TemporaryDirectory() as temp_dir:
            array_path = Path(temp_dir) / "test4d.zarr"

            # Create 4D array
            arr = zarr.open_array(
                str(array_path), mode="w", shape=(3, 10, 20, 30), chunks=(1, 5, 10, 15)
            )
            arr[:] = np.random.rand(3, 10, 20, 30)

            ds = open_xarray(str(array_path), "")

            assert ds["values"].shape == (3, 10, 20, 30)
            assert list(ds["values"].dims) == ["c", "z", "y", "x"]

            # Channel dimension should have integer coords
            assert ds.coords["c"].dtype == np.int64

    def test_custom_storage_options(self, temp_zarr_3d):
        """Test with custom storage options."""
        ds = open_xarray(temp_zarr_3d, "", storage_options={"mode": "r"})

        assert "values" in ds
        assert ds["values"].shape == (10, 20, 30)

    def test_zarr_chunks_preserved(self, temp_zarr_3d):
        """Test that Zarr chunking info is preserved."""
        ds = open_xarray(temp_zarr_3d, "")

        # Check that zarr_chunks attribute is added
        assert "zarr_chunks" in ds["values"].attrs
        assert ds["values"].attrs["zarr_chunks"] == (5, 10, 15)

    def test_dataset_attributes(self, temp_zarr_3d):
        """Test that dataset-level attributes are added."""
        ds = open_xarray(temp_zarr_3d, "")

        assert "source_url" in ds.attrs
        assert ds.attrs["source_url"] == temp_zarr_3d
        assert "voxel_spacing_nm" in ds.attrs
        assert ds.attrs["voxel_spacing_nm"] == (100.0, 50.0, 50.0)

    def test_array_attributes_preserved(self, temp_zarr_3d):
        """Test that array attributes are preserved."""
        ds = open_xarray(temp_zarr_3d, "")

        assert "test_attr" in ds["values"].attrs
        assert ds["values"].attrs["test_attr"] == "test_value"

    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        with pytest.raises(ValueError, match="Failed to open"):
            open_xarray("/path/that/does/not/exist", "array")

    def test_group_with_multiple_arrays(self):
        """Test opening group with multiple arrays (should pick first)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "multi.zarr"

            store = zarr.open_group(str(store_path), mode="w")
            data1 = np.ones((5, 5, 5))
            create_array_compat(store, "data", data=data1)

            data2 = np.zeros((3, 3, 3))
            create_array_compat(store, "other", data=data2)

            # Should pick 'data' array
            ds = open_xarray(str(store_path), "")
            assert ds["values"].shape == (5, 5, 5)
            np.testing.assert_array_equal(ds["values"].values, 1.0)
