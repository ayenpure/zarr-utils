import time
import traceback
from contextlib import contextmanager
from typing import Any, Optional

import fsspec
import zarr


class ZarrDebugger:
    """Enhanced error messages and debugging for Zarr operations."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.operation_times: list[dict[str, Any]] = []

    @contextmanager
    def operation(self, name: str):
        """Context manager to track and debug operations."""
        start = time.time()
        if self.verbose:
            print(f"→ Starting: {name}")

        try:
            yield
            duration = time.time() - start
            self.operation_times.append({"name": name, "duration": duration, "success": True})
            if self.verbose:
                print(f"✓ Completed: {name} ({duration:.2f}s)")
        except Exception as e:
            duration = time.time() - start
            self.operation_times.append(
                {"name": name, "duration": duration, "success": False, "error": str(e)}
            )
            if self.verbose:
                print(f"✗ Failed: {name} ({duration:.2f}s)")
            raise

    def summarize(self):
        """Print operation summary."""
        if not self.operation_times:
            return

        print("\nOperation Summary:")
        print("=" * 60)

        total_time = sum(op["duration"] for op in self.operation_times)
        successful = sum(1 for op in self.operation_times if op["success"])
        failed = len(self.operation_times) - successful

        print(f"Total operations: {len(self.operation_times)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total time: {total_time:.2f}s")

        print("\nDetailed breakdown:")
        for op in self.operation_times:
            status = "✓" if op["success"] else "✗"
            print(f"  {status} {op['name']}: {op['duration']:.2f}s")
            if not op["success"]:
                print(f"    Error: {op.get('error', 'Unknown error')}")


def diagnose_zarr_store(
    store_url: str, storage_options: Optional[dict[str, Any]] = None, detailed: bool = True
) -> dict[str, Any]:
    """
    Comprehensive diagnostic tool for Zarr stores.

    Parameters
    ----------
    store_url : str
        Path or URL to the Zarr store
    storage_options : dict, optional
        Additional storage options
    detailed : bool, optional
        Include detailed diagnostics (default: True)

    Returns
    -------
    dict
        Diagnostic report
    """
    debugger = ZarrDebugger(verbose=detailed)
    report = {
        "store_url": store_url,
        "accessible": False,
        "store_type": None,
        "issues": [],
        "suggestions": [],
        "arrays": {},
        "performance": {},
    }

    # Check store accessibility
    with debugger.operation("Check store accessibility"):
        try:
            storage_options = storage_options or {}
            fs, path = fsspec.core.url_to_fs(store_url, **storage_options)

            if store_url.startswith("s3://"):
                report["store_type"] = "S3"
            elif store_url.startswith("gs://"):
                report["store_type"] = "Google Cloud Storage"
            elif store_url.startswith("az://"):
                report["store_type"] = "Azure Blob Storage"
            else:
                report["store_type"] = "Local filesystem"

            # Try to list files
            try:
                files = fs.ls(path)
                report["accessible"] = True
                report["file_count"] = len(files)
            except Exception as e:
                report["issues"].append(f"Cannot list files: {e}")
                report["suggestions"].append("Check permissions and credentials")

        except Exception as e:
            report["issues"].append(f"Cannot access store: {e}")
            report["suggestions"].append("Verify the store URL is correct")
            return report

    # Try different opening methods
    root = None
    mapper = None

    # Get the mapper first
    try:
        mapper = fsspec.get_mapper(store_url, **storage_options)
    except Exception as e:
        report["issues"].append(f"Cannot create mapper: {e}")
        return report

    with debugger.operation("Try opening with consolidated metadata"):
        try:
            root = zarr.open_consolidated(mapper, mode="r")
            report["has_consolidated_metadata"] = True
        except KeyError:
            report["issues"].append("Missing consolidated metadata (.zmetadata)")
            report["suggestions"].append("Run consolidate_metadata() to create .zmetadata")
            report["has_consolidated_metadata"] = False
        except Exception as e:
            report["issues"].append(f"Error opening with consolidated metadata: {e}")
            report["has_consolidated_metadata"] = False

    if root is None:
        with debugger.operation("Try opening as group"):
            try:
                root = zarr.open_group(mapper, mode="r")
            except Exception as e:
                report["issues"].append(f"Cannot open as group: {e}")

    if root is None:
        with debugger.operation("Try opening as array"):
            try:
                arr = zarr.open_array(mapper, mode="r")
                report["is_single_array"] = True
                report["arrays"]["array"] = {
                    "shape": arr.shape,
                    "dtype": str(arr.dtype),
                    "chunks": arr.chunks,
                }
            except Exception as e:
                report["issues"].append(f"Cannot open as array: {e}")
                report["suggestions"].append("Store may be corrupted or in an unsupported format")
                return report

    # Analyze arrays if we have a group
    if root is not None and not report.get("is_single_array"):
        with debugger.operation("Analyze arrays"):
            try:
                from .inspect import _walk_group

                array_count = 0
                total_size = 0

                for path, shape, dtype, nbytes in _walk_group(root):
                    array_count += 1
                    total_size += nbytes

                    if detailed and array_count <= 10:  # Show first 10 arrays
                        report["arrays"][path] = {
                            "shape": shape,
                            "dtype": str(dtype),
                            "size_bytes": nbytes,
                        }

                        # Check array accessibility
                        try:
                            arr = root[path]
                            # Try to read a small chunk
                            if hasattr(arr, "chunks"):
                                report["arrays"][path]["chunks"] = arr.chunks
                                # Test read
                                _ = arr[tuple(slice(0, min(10, s)) for s in arr.shape)]
                                report["arrays"][path]["readable"] = True
                        except Exception as e:
                            report["arrays"][path]["readable"] = False
                            report["arrays"][path]["read_error"] = str(e)

                report["total_arrays"] = array_count
                report["total_size_bytes"] = total_size

            except Exception as e:
                report["issues"].append(f"Error analyzing arrays: {e}")

    # Performance checks
    if detailed and root is not None:
        with debugger.operation("Performance diagnostics"):
            # Test read performance on first array
            try:
                if report.get("arrays"):
                    first_array_path = list(report["arrays"].keys())[0]
                    arr = root[first_array_path] if not report.get("is_single_array") else root

                    # Time small read
                    start = time.time()
                    data = arr[tuple(slice(0, min(100, s)) for s in arr.shape)]
                    read_time = time.time() - start

                    report["performance"]["small_read_time"] = read_time
                    report["performance"]["small_read_size"] = data.nbytes
                    report["performance"]["read_bandwidth_mbps"] = (
                        data.nbytes / 1024 / 1024
                    ) / read_time

                    if read_time > 1.0:
                        report["suggestions"].append(
                            "Slow read performance detected - check network/storage"
                        )

            except Exception as e:
                report["performance"]["error"] = str(e)

    # Generate suggestions based on findings
    if report["store_type"] != "Local filesystem" and not report.get("has_consolidated_metadata"):
        report["suggestions"].insert(
            0, "For remote stores, consolidated metadata significantly improves performance"
        )

    if detailed:
        debugger.summarize()

    return report


def explain_zarr_error(error: Exception, context: Optional[dict[str, Any]] = None) -> str:
    """
    Provide user-friendly explanations for common Zarr errors.

    Parameters
    ----------
    error : Exception
        The exception that occurred
    context : dict, optional
        Additional context (e.g., {'operation': 'opening store', 'url': 's3://...'})

    Returns
    -------
    str
        User-friendly error explanation with suggestions
    """
    error_str = str(error)
    error_type = type(error).__name__

    explanations = []
    suggestions = []

    # KeyError: '.zmetadata'
    if isinstance(error, KeyError) and ".zmetadata" in error_str:
        explanations.append("The Zarr store is missing consolidated metadata.")
        suggestions.extend(
            [
                "Run: zarr_utils.consolidate_metadata('path/to/store')",
                "Or open without consolidation: zarr.open_group(store, mode='r')",
            ]
        )

    # Permission errors
    elif isinstance(error, PermissionError) or "permission" in error_str.lower() or "forbidden" in error_str.lower() or "access denied" in error_str.lower():
        explanations.append("You don't have permission to access this store.")
        suggestions.extend(
            [
                "Check your credentials (AWS_ACCESS_KEY_ID, etc.)",
                "For public S3 data, use: storage_options={'anon': True}",
                "Verify the bucket/path exists and is accessible",
            ]
        )

    # File not found
    elif isinstance(error, FileNotFoundError) or "not found" in error_str.lower():
        explanations.append("The specified Zarr store or array doesn't exist.")
        suggestions.extend(
            [
                "Check the path/URL for typos",
                "Ensure the store exists at the specified location",
                "For S3, verify the bucket name and key",
            ]
        )

    # Codec/compression errors
    elif "codec" in error_str.lower() or "compressor" in error_str.lower():
        explanations.append("The Zarr array uses a compression codec that isn't available.")
        suggestions.extend(
            [
                "Install required compression libraries (e.g., pip install blosc)",
                "Check which codec is needed with zarr.open_array(store).compressor",
            ]
        )

    # Shape/dimension errors
    elif "shape" in error_str.lower() or "dimension" in error_str.lower():
        explanations.append("There's a mismatch in array dimensions or shape.")
        suggestions.extend(
            [
                "Verify the expected dimensions match the actual array shape",
                "Use inspect_zarr_store() to see array shapes",
                "Check if you're accessing the right array/group",
            ]
        )

    # Connection errors
    elif "connection" in error_str.lower() or "timeout" in error_str.lower():
        explanations.append("Network connection issue when accessing remote store.")
        suggestions.extend(
            [
                "Check your internet connection",
                "Try increasing timeout: storage_options={'timeout': 60}",
                "For S3, check your AWS region settings",
            ]
        )

    # Generic Zarr errors
    elif error_type == "ValueError" and "zarr" in error_str.lower():
        explanations.append("The store may not be a valid Zarr format.")
        suggestions.extend(
            [
                "Verify this is actually a Zarr store",
                "Try diagnose_zarr_store() for detailed analysis",
                "Check if it's a Zarr v2 vs v3 compatibility issue",
            ]
        )

    # Build output
    output = [f"\n❌ Error: {error_type}: {error_str}"]

    if explanations:
        output.append("\n💡 What this means:")
        output.extend(f"   {exp}" for exp in explanations)

    if suggestions:
        output.append("\n🔧 Suggestions:")
        output.extend(f"   • {sug}" for sug in suggestions)

    if context:
        output.append("\n📍 Context:")
        for key, value in context.items():
            output.append(f"   {key}: {value}")

    # Add stack trace location
    tb = traceback.extract_tb(error.__traceback__)
    if tb:
        last_frame = tb[-1]
        output.append(f"\n📄 Error occurred in: {last_frame.filename}:{last_frame.lineno}")

    return "\n".join(output)


# Monkey-patch better error messages
def _wrap_with_better_errors(func):
    """Decorator to add better error messages to functions."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Add context
            context = {
                "function": func.__name__,
                "args": str(args)[:100] if args else None,
            }

            # Print friendly error
            print(explain_zarr_error(e, context))

            # Re-raise original exception
            raise

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def enable_debug_mode():
    """Enable enhanced error messages globally for zarr-utils."""
    # Wrap key functions with better error handling
    import zarr_utils

    # List of functions to wrap
    functions_to_wrap = [
        "list_zarr_arrays",
        "inspect_zarr_store",
        "open_xarray",
        "consolidate_metadata",
        "validate_metadata",
    ]

    for func_name in functions_to_wrap:
        if hasattr(zarr_utils, func_name):
            original_func = getattr(zarr_utils, func_name)
            wrapped_func = _wrap_with_better_errors(original_func)
            setattr(zarr_utils, func_name, wrapped_func)

    print("✓ Debug mode enabled - you'll see enhanced error messages")
