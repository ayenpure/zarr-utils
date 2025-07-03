import json
from typing import Any, Optional

import fsspec
import zarr

from .compat import access_store_item, get_array_compressor, store_contains
from .compat import consolidate_metadata as consolidate_metadata_compat


def consolidate_metadata(
    store_url: str, storage_options: Optional[dict[str, Any]] = None, dry_run: bool = False
) -> dict[str, Any]:
    """
    Create or repair consolidated metadata (.zmetadata) for a Zarr store.

    This solves the common "KeyError: '.zmetadata'" issue and improves
    performance when opening stores.

    Parameters
    ----------
    store_url : str
        Path or URL to the Zarr store
    storage_options : dict, optional
        Additional storage options (e.g., {'anon': True} for S3)
    dry_run : bool, optional
        If True, return metadata without writing .zmetadata file

    Returns
    -------
    dict
        The consolidated metadata dictionary

    Examples
    --------
    >>> # Fix missing .zmetadata in local store
    >>> consolidate_metadata("data.zarr")

    >>> # Consolidate metadata for S3 store
    >>> consolidate_metadata("s3://bucket/data.zarr", storage_options={'anon': True})
    """
    # Get filesystem and path
    storage_options = storage_options or {}

    # Open the store using fsspec mapper
    mapper = fsspec.get_mapper(store_url, **storage_options)

    # Try to open as consolidated first
    try:
        zarr.open_consolidated(mapper, mode="r")
        # Try to access consolidated metadata
        metadata_bytes = access_store_item(mapper, ".zmetadata")
        if metadata_bytes:
            if isinstance(metadata_bytes, bytes):
                existing_metadata = json.loads(metadata_bytes.decode())
            else:
                existing_metadata = json.loads(metadata_bytes)
            print(f"✓ Consolidated metadata exists at {store_url}/.zmetadata")
            return existing_metadata
        else:
            raise KeyError(".zmetadata not found")
    except (KeyError, ValueError, AttributeError):
        print(f"⚠ No consolidated metadata found at {store_url}/.zmetadata")
        zarr.open_group(mapper, mode="r")

    # Generate consolidated metadata
    print("→ Scanning store and building metadata...")

    if not dry_run:
        # Use the mapper to consolidate
        consolidate_metadata_compat(mapper, metadata_key=".zmetadata")
        print(f"✓ Consolidated metadata written to {store_url}/.zmetadata")
    else:
        print("ℹ Dry run - metadata not written")
        # For dry run, just return empty dict
        return {}

    # Return the metadata dict
    try:
        metadata_bytes = access_store_item(mapper, ".zmetadata")
        if metadata_bytes:
            if isinstance(metadata_bytes, bytes):
                return json.loads(metadata_bytes.decode())
            else:
                return json.loads(metadata_bytes)
    except Exception:
        # Fallback - return basic info
        return {"zarr_consolidated_format": 1}


def _get_compression_info(arr) -> Optional[str]:
    """Get compression info from array in a version-compatible way."""
    try:
        return get_array_compressor(arr)
    except Exception:
        return None


def validate_metadata(
    store_url: str, storage_options: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Validate and report issues with Zarr store metadata.

    Parameters
    ----------
    store_url : str
        Path or URL to the Zarr store
    storage_options : dict, optional
        Additional storage options

    Returns
    -------
    dict
        Validation report with keys:
        - 'valid': bool - whether metadata is valid
        - 'has_consolidated': bool - whether .zmetadata exists
        - 'issues': list - any issues found
        - 'arrays': dict - info about each array
        - 'groups': dict - info about each group
    """
    issues = []
    report = {
        "valid": True,
        "has_consolidated": False,
        "issues": issues,
        "arrays": {},
        "groups": {},
    }

    storage_options = storage_options or {}

    # Check for consolidated metadata
    try:
        mapper = fsspec.get_mapper(store_url, **storage_options)

        # Check if .zmetadata exists
        has_zmetadata = store_contains(mapper, ".zmetadata")

        if has_zmetadata:
            report["has_consolidated"] = True
            try:
                metadata_bytes = access_store_item(mapper, ".zmetadata")
                if metadata_bytes:
                    if isinstance(metadata_bytes, bytes):
                        json.loads(metadata_bytes.decode())
                    else:
                        json.loads(metadata_bytes)
                    print("✓ Consolidated metadata exists and is valid JSON")
                else:
                    raise ValueError("Could not read .zmetadata")
            except json.JSONDecodeError as e:
                issues.append(f"Invalid JSON in .zmetadata: {e}")
                report["valid"] = False
        else:
            issues.append("Missing consolidated metadata (.zmetadata)")
    except Exception as e:
        issues.append(f"Error accessing store: {e}")
        report["valid"] = False
        return report

    # Open store and validate structure
    try:
        if report["has_consolidated"]:
            root = zarr.open_consolidated(mapper, mode="r")
        else:
            root = zarr.open_group(mapper, mode="r")
    except Exception as e:
        issues.append(f"Error opening store: {e}")
        report["valid"] = False
        return report

    # Check root attributes
    if not hasattr(root, "attrs") or not root.attrs:
        issues.append("Root group has no attributes")

    # Walk through arrays and groups
    def check_array(name: str, arr: zarr.Array, path: str = ""):
        array_issues = []
        full_path = f"{path}/{name}" if path else name

        # Check for required attributes
        if not hasattr(arr, "shape"):
            array_issues.append("Missing shape")
        if not hasattr(arr, "dtype"):
            array_issues.append("Missing dtype")
        if not hasattr(arr, "chunks"):
            array_issues.append("Missing chunks")

        # Check for common metadata
        if "units" not in arr.attrs and "unit" not in arr.attrs:
            array_issues.append("No units specified in attributes")

        # Store array info
        report["arrays"][full_path] = {
            "shape": arr.shape if hasattr(arr, "shape") else None,
            "dtype": str(arr.dtype) if hasattr(arr, "dtype") else None,
            "chunks": arr.chunks if hasattr(arr, "chunks") else None,
            "compression": _get_compression_info(arr),
            "issues": array_issues,
        }

        if array_issues:
            issues.extend([f"Array '{full_path}': {issue}" for issue in array_issues])

    def check_group(group: zarr.Group, path: str = ""):
        # Check group attributes
        group_issues = []

        if not group.attrs:
            group_issues.append(f"Group '{path or '/'}' has no attributes")

        report["groups"][path or "/"] = {"attrs": dict(group.attrs), "issues": group_issues}

        # Check arrays in group
        for name, arr in group.arrays():
            check_array(name, arr, path)

        # Recursively check subgroups
        for name, subgroup in group.groups():
            sub_path = f"{path}/{name}" if path else name
            check_group(subgroup, sub_path)

    # Start validation from root
    check_group(root)

    # Set overall validity
    if issues:
        report["valid"] = False

    # Print summary
    print(f"\nValidation Report for {store_url}")
    print(f"{'=' * 50}")
    print(f"Valid: {'✓' if report['valid'] else '✗'}")
    print(f"Consolidated metadata: {'✓' if report['has_consolidated'] else '✗'}")
    print(f"Arrays found: {len(report['arrays'])}")
    print(f"Groups found: {len(report['groups'])}")

    if issues:
        print(f"\nIssues found ({len(issues)}):")
        for issue in issues[:10]:  # Show first 10 issues
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more issues")

    return report


def repair_metadata(
    store_url: str, storage_options: Optional[dict[str, Any]] = None, add_missing_attrs: bool = True
) -> None:
    """
    Attempt to repair common metadata issues in a Zarr store.

    Parameters
    ----------
    store_url : str
        Path or URL to the Zarr store
    storage_options : dict, optional
        Additional storage options
    add_missing_attrs : bool, optional
        Add commonly expected attributes if missing
    """
    print(f"Repairing metadata for {store_url}...")

    # First validate to find issues
    report = validate_metadata(store_url, storage_options)

    if report["valid"] and report["has_consolidated"]:
        print("✓ No repairs needed - metadata is valid")
        return

    # Consolidate metadata if missing
    if not report["has_consolidated"]:
        print("\n→ Creating consolidated metadata...")
        consolidate_metadata(store_url, storage_options)

    # Add missing attributes if requested
    if add_missing_attrs and report["arrays"]:
        print("\n→ Adding missing attributes...")
        storage_options = storage_options or {}

        if store_url.startswith(("s3://", "gs://", "az://")):
            print("⚠ Cannot add attributes to read-only remote stores")
            print("  Consider copying to a local store first")
            return

        # Open store for writing
        store = zarr.open_group(store_url, mode="r+")

        for array_path, info in report["arrays"].items():
            if "No units specified" in str(info.get("issues", [])):
                try:
                    arr = store[array_path]
                    arr.attrs["units"] = "unknown"
                    print(f"  ✓ Added units attribute to {array_path}")
                except Exception as e:
                    print(f"  ✗ Failed to update {array_path}: {e}")

    print("\n✓ Repair complete")
