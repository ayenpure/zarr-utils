# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

zarr-utils is a Python utilities package for working with Zarr datasets, providing tools for inspection, conversion, and integration with scientific Python libraries.

**Note**: This package supports both Zarr v2 and v3 through a compatibility layer (`zarr_utils/compat.py`).

## Key Commands

### Development Setup
```bash
# Install the package in development mode with all dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Running Examples
```bash
# Inspect a Zarr store
python examples/inspect.py

# Interactive visualization example
python examples/jenelia.py
```

### Code Quality
```bash
# Run linting with ruff
python -m ruff check zarr_utils/

# Format code with ruff
python -m ruff format zarr_utils/
```

### Testing
```bash
# Run tests with pytest
python -m pytest

# Run tests with uv (if using uv for environment management)
uv run pytest

# Run tests with verbose output
uv run pytest -xvs
```

## Architecture Overview

The package is organized into three main modules:

1. **inspect.py**: Provides utilities for exploring Zarr stores and arrays
   - `list_zarr_arrays()`: Lists all arrays in a Zarr store (local or remote)
   - `get_info()`: Retrieves detailed information about a specific Zarr array

2. **xarray.py**: Integration with xarray for labeled arrays
   - `open_zarr_array()`: Opens Zarr arrays as xarray.DataArray with proper dimensional coordinates
   - Handles voxel spacing and pixel resolution metadata

3. **convert.py**: Export utilities for visualization
   - `to_vti()`: Converts 3D Zarr arrays to VTK ImageData format
   - Preserves metadata and spacing information for scientific visualization

## Important Notes

- The package supports both local and remote (S3) Zarr stores via fsspec
- Designed for large-scale 3D imaging data with physical coordinates
- Uses semantic versioning with version tracked in `zarr_utils/__init__.py`
- Test suite implemented with pytest (run with `python -m pytest`)
- Examples demonstrate common use cases with real scientific datasets
- Zarr v2/v3 compatibility handled via `zarr_utils/compat.py`

## Recent Enhancements

- Added comprehensive type hints throughout the codebase
- Implemented metadata consolidation and validation tools
- Added debugging utilities with better error messages
- Created test suite with pytest
- Set up CI/CD pipeline with GitHub Actions
- Configured code quality tools (ruff, mypy, pre-commit)
- Added Zarr v2/v3 compatibility layer to ensure the codebase works with both versions
- All tests pass with both Zarr v2 and v3

## Zarr v2/v3 Compatibility

The codebase includes a compatibility layer (`zarr_utils/compat.py`) that handles differences between Zarr v2 and v3:

- `consolidate_metadata()`: Handles metadata_key parameter differences
- `open_array_with_storage_options()`: Manages storage_options compatibility
- `create_array_compat()`: Provides unified array creation API
- `get_array_compressor()`: Abstracts compressor access differences
- `access_store_item()` and `store_contains()`: Handle store API changes

All modules use these compatibility functions to ensure they work seamlessly with both Zarr versions.

## Code Documentation Guidelines

- Always ensure that public functions, classes, etc. have docstrings that capture essential information about them, focusing on purpose and usage rather than implementation details