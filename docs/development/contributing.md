# Contributing to zarr-utils

We welcome contributions to zarr-utils! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- Optional: uv for fast Python environment management

### Setting Up Your Environment

1. Fork and clone the repository:
```bash
git clone https://github.com/yourusername/zarr-utils.git
cd zarr-utils
```

2. Create a virtual environment:
```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using uv
uv venv
source .venv/bin/activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"

# Or with uv
uv pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Code Style

We use `ruff` for linting and formatting:

```bash
# Check code style
ruff check .

# Fix auto-fixable issues
ruff check . --fix

# Format code
ruff format .
```

### Style Guidelines

- Follow PEP 8
- Use type hints for all public functions
- Maximum line length: 100 characters
- Use descriptive variable names
- Add docstrings to all public functions and classes

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=zarr_utils --cov-report=html

# Run specific test file
pytest tests/test_inspect.py

# Run with verbose output
pytest -xvs
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Use descriptive test function names
- Include both positive and negative test cases
- Test with both Zarr v2 and v3

Example test:
```python
import pytest
import numpy as np
from zarr_utils import list_zarr_arrays

def test_list_zarr_arrays_empty_store(tmp_path):
    """Test listing arrays in an empty store."""
    import zarr
    
    store_path = tmp_path / "empty.zarr"
    zarr.open_group(str(store_path), mode='w')
    
    arrays = list_zarr_arrays(str(store_path))
    assert len(arrays) == 0
```

## Documentation

### Docstring Format

We use Google-style docstrings:

```python
def function_name(param1: str, param2: int = 0) -> bool:
    """
    Brief description of function.
    
    Longer description if needed, explaining behavior,
    assumptions, and important details.
    
    Parameters
    ----------
    param1 : str
        Description of param1
    param2 : int, optional
        Description of param2, by default 0
        
    Returns
    -------
    bool
        Description of return value
        
    Raises
    ------
    ValueError
        When param1 is empty
        
    Examples
    --------
    >>> function_name("test", 42)
    True
    """
```

### Building Documentation

```bash
# Install docs dependencies
pip install -e ".[docs]"

# Build docs
mkdocs build

# Serve locally
mkdocs serve
# Visit http://127.0.0.1:8000
```

## Making Changes

### Workflow

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes
3. Add tests for new functionality
4. Run tests and linting:
```bash
pytest
ruff check .
```

5. Commit your changes:
```bash
git add .
git commit -m "feat: add new feature"
```

### Commit Messages

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

## Pull Requests

### Before Submitting

1. Ensure all tests pass
2. Update documentation if needed
3. Add entry to CHANGELOG.md
4. Check code style
5. Ensure compatibility with Zarr v2 and v3

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added
- [ ] Tested with Zarr v2
- [ ] Tested with Zarr v3

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## Adding New Features

### Feature Checklist

1. **Implementation**
   - Add to appropriate module
   - Include type hints
   - Handle errors gracefully
   - Consider Zarr v2/v3 compatibility

2. **Documentation**
   - Add docstring
   - Update user guide
   - Add to API reference
   - Include examples

3. **Testing**
   - Unit tests
   - Integration tests
   - Edge cases
   - Both Zarr versions

4. **Export**
   - Add to `__init__.py` if public API
   - Update `__all__` list

### Example Feature Addition

```python
# In zarr_utils/new_feature.py
from typing import Optional
import zarr
from .compat import IS_ZARR_V3

def new_function(store_path: str, option: Optional[str] = None) -> dict:
    """
    Brief description.
    
    Parameters
    ----------
    store_path : str
        Path to Zarr store
    option : str, optional
        Some option
        
    Returns
    -------
    dict
        Result dictionary
    """
    # Implementation
    pass

# In zarr_utils/__init__.py
from .new_feature import new_function
__all__.append('new_function')

# In tests/test_new_feature.py
def test_new_function():
    result = new_function("test.zarr")
    assert isinstance(result, dict)
```

## Debugging

### Debug Mode

Enable verbose output:
```python
from zarr_utils.debug import enable_debug_mode
enable_debug_mode()
```

### Common Issues

1. **Import Errors**: Check all dependencies are installed
2. **Test Failures**: Ensure test data is properly created
3. **Compatibility**: Test with both Zarr versions

## Release Process

1. Update version in `zarr_utils/__init__.py`
2. Update CHANGELOG.md
3. Create release PR
4. After merge, tag release:
```bash
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

## Getting Help

- Open an issue for bugs or features
- Join discussions for questions
- Check existing issues before creating new ones

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on what is best for the community

Thank you for contributing to zarr-utils!