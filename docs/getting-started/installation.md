# Installation

## Requirements

- Python 3.9 or higher
- NumPy
- Zarr (v2 or v3)
- fsspec (for remote storage support)

## Installing from PyPI

The easiest way to install zarr-utils is from PyPI:

```bash
pip install zarr-utils
```

## Installing from Source

To install the latest development version from GitHub:

```bash
git clone https://github.com/yourusername/zarr-utils.git
cd zarr-utils
pip install -e .
```

## Installing with Optional Dependencies

### For Development

Install with all development dependencies:

```bash
pip install -e ".[dev]"
```

This includes:
- pytest (testing)
- ruff (linting and formatting)
- mypy (type checking)
- pre-commit (git hooks)
- mkdocs (documentation)

### For Visualization

Install with visualization support:

```bash
pip install zarr-utils[viz]
```

This includes:
- vtk (for VTK export)
- pyvista (for interactive visualization)

### For All Features

Install with all optional dependencies:

```bash
pip install zarr-utils[all]
```

## Using uv

If you're using [uv](https://github.com/astral-sh/uv) for Python environment management:

```bash
# Create environment and install
uv pip install zarr-utils

# For development
uv pip install -e ".[dev]"

# Run tests
uv run pytest
```

## Verifying Installation

After installation, verify that zarr-utils is working correctly:

```python
import zarr_utils

# Check version
print(zarr_utils.__version__)

# Test basic functionality
arrays = zarr_utils.list_zarr_arrays("path/to/test.zarr")
```

## Zarr Version Compatibility

zarr-utils automatically detects your Zarr version and adjusts its behavior accordingly. It supports:

- Zarr v2.x (2.13.0 and higher)
- Zarr v3.x (experimental support)

To check which Zarr version you have:

```python
import zarr
print(zarr.__version__)
```

## Troubleshooting

### Import Errors

If you encounter import errors:

1. Ensure you're in the correct Python environment
2. Check that all dependencies are installed: `pip list | grep zarr`
3. Try reinstalling: `pip install --force-reinstall zarr-utils`

### Permission Errors with S3

For S3 access, ensure you have:
- boto3 and s3fs installed: `pip install boto3 s3fs`
- AWS credentials configured (or use `storage_options={'anon': True}` for public data)

### VTK Import Errors

If visualization features fail:
- Install VTK: `pip install vtk`
- On headless systems, you may need to set: `export VTK_OFFSCREEN_RENDERING=true`