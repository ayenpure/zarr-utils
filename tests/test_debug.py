import shutil
import tempfile
import time
from pathlib import Path

import numpy as np
import pytest
import zarr

from zarr_utils.compat import create_array_compat
from zarr_utils.debug import (
    ZarrDebugger,
    diagnose_zarr_store,
    enable_debug_mode,
    explain_zarr_error,
)


class TestZarrDebugger:
    """Test the ZarrDebugger class."""

    def test_successful_operation(self, capsys):
        """Test tracking successful operations."""
        debugger = ZarrDebugger(verbose=True)

        with debugger.operation("Test operation"):
            time.sleep(0.1)  # Simulate work

        assert len(debugger.operation_times) == 1
        assert debugger.operation_times[0]["success"] is True
        assert debugger.operation_times[0]["duration"] >= 0.1

        captured = capsys.readouterr()
        assert "Starting: Test operation" in captured.out
        assert "Completed: Test operation" in captured.out

    def test_failed_operation(self, capsys):
        """Test tracking failed operations."""
        debugger = ZarrDebugger(verbose=True)

        with pytest.raises(ValueError):
            with debugger.operation("Failing operation"):
                raise ValueError("Test error")

        assert len(debugger.operation_times) == 1
        assert debugger.operation_times[0]["success"] is False
        assert "error" in debugger.operation_times[0]

        captured = capsys.readouterr()
        assert "Failed: Failing operation" in captured.out

    def test_quiet_mode(self, capsys):
        """Test debugger in quiet mode."""
        debugger = ZarrDebugger(verbose=False)

        with debugger.operation("Quiet operation"):
            pass

        captured = capsys.readouterr()
        assert captured.out == ""  # No output in quiet mode

    def test_summarize(self, capsys):
        """Test operation summary."""
        debugger = ZarrDebugger(verbose=False)

        # Add some operations
        with debugger.operation("Op1"):
            time.sleep(0.05)

        try:
            with debugger.operation("Op2"):
                raise ValueError("Error")
        except ValueError:
            pass

        with debugger.operation("Op3"):
            time.sleep(0.05)

        debugger.summarize()

        captured = capsys.readouterr()
        assert "Operation Summary:" in captured.out
        assert "Total operations: 3" in captured.out
        assert "Successful: 2" in captured.out
        assert "Failed: 1" in captured.out
        assert "✓ Op1:" in captured.out
        assert "✗ Op2:" in captured.out
        assert "Error: Error" in captured.out


class TestDiagnoseZarrStore:
    """Test Zarr store diagnostics."""

    @pytest.fixture
    def temp_zarr_store(self):
        """Create a test Zarr store."""
        temp_dir = tempfile.mkdtemp()
        store_path = Path(temp_dir) / "test.zarr"

        store = zarr.open_group(str(store_path), mode="w")
        store.attrs["description"] = "Test store"

        # Add some arrays
        data1 = np.random.rand(100, 100)
        arr1 = create_array_compat(
            store, "data1", data=data1, chunks=(50, 50)
        )
        arr1.attrs["units"] = "meters"

        group1 = store.create_group("subgroup")
        data2 = np.random.rand(50, 50, 50)
        create_array_compat(
            group1, "data2", data=data2, chunks=(25, 25, 25)
        )

        yield str(store_path)

        shutil.rmtree(temp_dir)

    def test_diagnose_local_store(self, temp_zarr_store):
        """Test diagnosing a local Zarr store."""
        report = diagnose_zarr_store(temp_zarr_store, detailed=True)

        assert report["accessible"] is True
        assert report["store_type"] == "Local filesystem"
        assert report["has_consolidated_metadata"] is False
        assert report["total_arrays"] == 2
        assert report["total_size_bytes"] > 0

        # Check arrays were analyzed
        assert len(report["arrays"]) == 2
        assert "data1" in report["arrays"]
        assert report["arrays"]["data1"]["readable"] is True

        # Check performance metrics
        assert "small_read_time" in report["performance"]
        assert "read_bandwidth_mbps" in report["performance"]

    def test_diagnose_with_consolidated(self):
        """Test diagnosing store with consolidated metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "consolidated.zarr"

            store = zarr.open_group(str(store_path), mode="w")
            data = np.arange(1000)
            create_array_compat(store, "data", data=data)
            zarr.consolidate_metadata(str(store_path))

            report = diagnose_zarr_store(str(store_path), detailed=False)

            assert report["has_consolidated_metadata"] is True
            assert len(report["issues"]) == 0

    def test_diagnose_single_array(self):
        """Test diagnosing a single array store."""
        with tempfile.TemporaryDirectory() as temp_dir:
            array_path = Path(temp_dir) / "array.zarr"

            arr = zarr.open_array(str(array_path), mode="w", shape=(10, 10), chunks=(5, 5))
            arr[:] = np.random.rand(10, 10)

            report = diagnose_zarr_store(str(array_path))

            assert report["accessible"] is True
            assert report.get("is_single_array") is True
            assert "array" in report["arrays"]

    def test_diagnose_nonexistent_store(self):
        """Test diagnosing non-existent store."""
        report = diagnose_zarr_store("/path/that/does/not/exist")

        # Either the store should be inaccessible or there should be issues
        assert report["accessible"] is False or len(report["issues"]) > 0

        # Check for various error messages that might appear
        if report["issues"]:
            issues_text = " ".join(report["issues"])
            assert any(phrase in issues_text for phrase in [
                "Cannot access store",
                "Cannot create mapper",
                "does not exist",
                "No such file"
            ])

    def test_diagnose_empty_store(self):
        """Test diagnosing empty store."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "empty.zarr"
            zarr.open_group(str(store_path), mode="w")

            report = diagnose_zarr_store(str(store_path))

            assert report["accessible"] is True
            assert report.get("total_arrays", 0) == 0


class TestExplainZarrError:
    """Test error explanation functionality."""

    def test_explain_zmetadata_error(self):
        """Test explaining missing .zmetadata error."""
        error = KeyError(".zmetadata")
        explanation = explain_zarr_error(error)

        assert "missing consolidated metadata" in explanation
        assert "consolidate_metadata" in explanation
        assert "Suggestions:" in explanation

    def test_explain_permission_error(self):
        """Test explaining permission errors."""
        error = PermissionError("Access denied to s3://bucket/data.zarr")
        explanation = explain_zarr_error(error)

        assert "don't have permission" in explanation
        assert "Check your credentials" in explanation
        assert "anon" in explanation

    def test_explain_file_not_found(self):
        """Test explaining file not found errors."""
        error = FileNotFoundError("No such file or directory: 'data.zarr'")
        explanation = explain_zarr_error(error)

        assert "doesn't exist" in explanation
        assert "Check the path/URL for typos" in explanation

    def test_explain_codec_error(self):
        """Test explaining codec errors."""
        error = ValueError("codec 'lz4' is not available")
        explanation = explain_zarr_error(error)

        assert "compression codec" in explanation
        assert "Install required compression libraries" in explanation

    def test_explain_shape_error(self):
        """Test explaining shape/dimension errors."""
        error = ValueError("shape mismatch: expected (10, 10) got (20, 20)")
        explanation = explain_zarr_error(error)

        assert "mismatch in array dimensions" in explanation
        assert "inspect_zarr_store" in explanation

    def test_explain_with_context(self):
        """Test error explanation with context."""
        error = KeyError(".zmetadata")
        context = {"operation": "opening store", "url": "s3://bucket/data.zarr"}

        explanation = explain_zarr_error(error, context)

        assert "Context:" in explanation
        assert "operation: opening store" in explanation
        assert "url: s3://bucket/data.zarr" in explanation

    def test_explain_generic_error(self):
        """Test generic error handling."""
        error = RuntimeError("Something went wrong")
        explanation = explain_zarr_error(error)

        assert "RuntimeError: Something went wrong" in explanation


class TestEnableDebugMode:
    """Test debug mode enablement."""

    def test_enable_debug_mode(self, capsys):
        """Test enabling debug mode."""
        enable_debug_mode()

        captured = capsys.readouterr()
        assert "Debug mode enabled" in captured.out

        # Note: We can't easily test the monkey-patching without
        # importing zarr_utils in a specific way, but we verify
        # the function runs without error
