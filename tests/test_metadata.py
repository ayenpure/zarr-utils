import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest
import zarr

from zarr_utils.compat import IS_ZARR_V3, access_store_item, create_array_compat
from zarr_utils.metadata import consolidate_metadata, repair_metadata, validate_metadata


class TestConsolidateMetadata:
    """Test metadata consolidation functionality."""

    @pytest.fixture
    def temp_zarr_store(self):
        """Create a temporary Zarr store without consolidated metadata."""
        temp_dir = tempfile.mkdtemp()
        store_path = Path(temp_dir) / "test.zarr"

        # Create store without consolidation
        store = zarr.open_group(str(store_path), mode="w")
        store.attrs["root_attr"] = "root_value"

        # Add arrays
        data1 = np.random.rand(10, 10)
        create_array_compat(store, "array1", data=data1)

        group1 = store.create_group("group1")
        data2 = np.random.rand(20, 20)
        create_array_compat(group1, "array2", data=data2)

        yield str(store_path)

        shutil.rmtree(temp_dir)

    def test_consolidate_new_metadata(self, temp_zarr_store, capsys):
        """Test creating new consolidated metadata."""
        # Verify no .zmetadata exists
        import fsspec
        mapper = fsspec.get_mapper(temp_zarr_store)
        assert access_store_item(mapper, ".zmetadata") is None

        # Consolidate
        metadata = consolidate_metadata(temp_zarr_store)

        # Check output
        captured = capsys.readouterr()
        assert "No consolidated metadata found" in captured.out
        assert "Scanning store and building metadata" in captured.out
        assert "Consolidated metadata written" in captured.out

        # Verify .zmetadata now exists
        import fsspec
        mapper = fsspec.get_mapper(temp_zarr_store)
        assert access_store_item(mapper, ".zmetadata") is not None

        # Verify metadata content
        assert "metadata" in metadata or isinstance(metadata, dict)

    def test_consolidate_existing_metadata(self, capsys):
        """Test handling of already consolidated metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "consolidated.zarr"

            # Create and consolidate
            store = zarr.open_group(str(store_path), mode="w")
            data = np.arange(100)
            create_array_compat(store, "data", data=data)
            zarr.consolidate_metadata(str(store_path))

            # Try to consolidate again
            consolidate_metadata(str(store_path))

            captured = capsys.readouterr()
            assert "Consolidated metadata exists" in captured.out

    def test_dry_run(self, temp_zarr_store, capsys):
        """Test dry run mode."""
        consolidate_metadata(temp_zarr_store, dry_run=True)

        captured = capsys.readouterr()
        assert "Dry run - metadata not written" in captured.out

        # Verify .zmetadata was not created
        import fsspec
        mapper = fsspec.get_mapper(temp_zarr_store)
        assert access_store_item(mapper, ".zmetadata") is None

    def test_storage_options(self, temp_zarr_store):
        """Test with custom storage options."""
        metadata = consolidate_metadata(temp_zarr_store, storage_options={"mode": "r+"})

        assert metadata is not None


class TestValidateMetadata:
    """Test metadata validation functionality."""

    @pytest.fixture
    def valid_zarr_store(self):
        """Create a valid Zarr store with consolidated metadata."""
        temp_dir = tempfile.mkdtemp()
        store_path = Path(temp_dir) / "valid.zarr"

        store = zarr.open_group(str(store_path), mode="w")
        store.attrs["description"] = "Test store"

        data_temp = np.random.rand(10, 10)
        arr1 = create_array_compat(
            store, "temperature", data=data_temp, chunks=(5, 5)
        )
        arr1.attrs["units"] = "celsius"

        group1 = store.create_group("measurements")
        group1.attrs["location"] = "lab"

        data_pressure = np.random.rand(20, 20)
        arr2 = create_array_compat(
            group1, "pressure", data=data_pressure, chunks=(10, 10)
        )
        arr2.attrs["units"] = "pascal"

        # Consolidate metadata
        zarr.consolidate_metadata(str(store_path))

        yield str(store_path)

        shutil.rmtree(temp_dir)

    @pytest.fixture
    def invalid_zarr_store(self):
        """Create a Zarr store with issues."""
        temp_dir = tempfile.mkdtemp()
        store_path = Path(temp_dir) / "invalid.zarr"

        store = zarr.open_group(str(store_path), mode="w")
        # No root attributes

        # Array without units
        data = np.random.rand(10, 10)
        create_array_compat(store, "data", data=data)

        # Group without attributes
        store.create_group("empty_group")

        yield str(store_path)

        shutil.rmtree(temp_dir)

    def test_validate_valid_store(self, valid_zarr_store, capsys):
        """Test validation of a valid store."""
        report = validate_metadata(valid_zarr_store)

        assert report["valid"] is True
        assert report["has_consolidated"] is True
        assert len(report["issues"]) == 0
        assert len(report["arrays"]) == 2
        assert len(report["groups"]) == 2  # root + measurements

        captured = capsys.readouterr()
        assert "Valid: ✓" in captured.out
        assert "Consolidated metadata: ✓" in captured.out

    def test_validate_invalid_store(self, invalid_zarr_store, capsys):
        """Test validation of store with issues."""
        report = validate_metadata(invalid_zarr_store)

        assert report["valid"] is False
        assert report["has_consolidated"] is False
        assert len(report["issues"]) > 0

        # Check specific issues
        issue_strings = " ".join(report["issues"])
        assert "Missing consolidated metadata" in issue_strings
        assert "No units specified" in issue_strings
        assert "has no attributes" in issue_strings

        captured = capsys.readouterr()
        assert "Valid: ✗" in captured.out
        assert "Issues found" in captured.out

    def test_validate_corrupted_metadata(self):
        """Test handling of corrupted .zmetadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "corrupted.zarr"

            store = zarr.open_group(str(store_path), mode="w")
            data = np.arange(100)
            create_array_compat(store, "data", data=data)

            # Manually create invalid .zmetadata
            if IS_ZARR_V3:
                # For v3, write directly to filesystem
                import os
                with open(os.path.join(str(store_path), ".zmetadata"), "wb") as f:
                    f.write(b'{"invalid json')
            else:
                store.store[".zmetadata"] = b'{"invalid json'

            report = validate_metadata(str(store_path))

            assert report["valid"] is False
            assert any("Invalid JSON" in issue for issue in report["issues"])


class TestRepairMetadata:
    """Test metadata repair functionality."""

    def test_repair_missing_consolidated(self, capsys):
        """Test repairing missing consolidated metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "repair.zarr"

            store = zarr.open_group(str(store_path), mode="w")
            data = np.random.rand(10, 10)
            create_array_compat(store, "data", data=data)

            # Repair
            repair_metadata(str(store_path))

            # Verify consolidated metadata was created
            import fsspec
            mapper = fsspec.get_mapper(str(store_path))
            assert access_store_item(mapper, ".zmetadata") is not None

            captured = capsys.readouterr()
            assert "Creating consolidated metadata" in captured.out
            assert "Repair complete" in captured.out

    def test_repair_valid_store(self, capsys):
        """Test repair on already valid store."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "valid.zarr"

            store = zarr.open_group(str(store_path), mode="w")
            store.attrs["description"] = "Test store"  # Add root attributes
            data = np.random.rand(10, 10)
            arr = create_array_compat(store, "data", data=data)
            arr.attrs["units"] = "meters"
            zarr.consolidate_metadata(str(store_path))

            repair_metadata(str(store_path))

            captured = capsys.readouterr()
            assert "No repairs needed" in captured.out

    def test_repair_add_missing_attrs(self):
        """Test adding missing attributes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "missing_attrs.zarr"

            store = zarr.open_group(str(store_path), mode="w")
            # Create array without units
            data = np.random.rand(10, 10)
            create_array_compat(store, "data", data=data)

            repair_metadata(str(store_path), add_missing_attrs=True)

            # Verify units were added
            store = zarr.open_group(str(store_path), mode="r")
            assert "units" in store["data"].attrs
            assert store["data"].attrs["units"] == "unknown"

    def test_repair_readonly_store(self, capsys):
        """Test repair on read-only store."""
        # This should show the message about read-only stores even before trying to access
        try:
            repair_metadata("s3://fake-bucket/data.zarr", add_missing_attrs=True)
        except Exception:
            # Expected to fail since we don't have credentials
            pass

        captured = capsys.readouterr()
        # The function should detect it's a remote store and show appropriate message
        # or fail trying to access it
        assert any(msg in captured.out for msg in [
            "Cannot add attributes to read-only remote stores",
            "Error accessing store",
            "Creating consolidated metadata"
        ])
