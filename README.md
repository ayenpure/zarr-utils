# zarr-utils

A utilities package designed to make working with Zarr data a little easier.

[![Python Version](https://img.shields.io/pypi/pyversions/zarr-utils.svg)](https://pypi.org/project/zarr-utils/)
[![License](https://img.shields.io/pypi/l/zarr-utils.svg)](https://github.com/yourusername/zarr-utils/blob/main/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/zarr-utils/badge/?version=latest)](https://zarr-utils.readthedocs.io/en/latest/?badge=latest)

## Features

- 📊 **Inspect** Zarr stores and arrays (local or remote)
- 🏷️ **Manage metadata** - consolidate, validate, and repair
- 🔍 **Debug** with helpful error messages and diagnostics
- 📈 **Integrate** with xarray for labeled arrays
- 🎨 **Visualize** via VTK export
- 🔄 **Compatible** with both Zarr v2 and v3

## Installation

```bash
pip install zarr-utils
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

```python
import zarr_utils as zu

# List arrays in a Zarr store
arrays = zu.list_zarr_arrays("data.zarr")
for array in arrays:
    print(f"{array['path']}: {array['shape']} ({array['dtype']})")

# Fix missing consolidated metadata
zu.consolidate_metadata("data.zarr")

# Open as xarray with physical coordinates
ds = zu.open_xarray("data.zarr", "array_name")

# Debug issues
diagnosis = zu.diagnose_zarr_store("data.zarr")
```

## Documentation

Full documentation is available at [zarr-utils.readthedocs.io](https://zarr-utils.readthedocs.io).

### Building Documentation Locally

```bash
pip install -e ".[docs]"
mkdocs serve
# Visit http://127.0.0.1:8000
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/zarr-utils.git
cd zarr-utils

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=zarr_utils

# Run linting
ruff check .
```

## Contributing

Contributions are welcome! Please see our [Contributing Guide](https://zarr-utils.readthedocs.io/en/latest/development/contributing/) for details.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.