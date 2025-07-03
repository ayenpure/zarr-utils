# Testing Guide

This guide covers testing practices for zarr-utils development.

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_inspect.py      # Tests for inspection module
├── test_xarray.py       # Tests for xarray integration
├── test_metadata.py     # Tests for metadata management
├── test_debug.py        # Tests for debugging tools
├── test_compat.py       # Tests for compatibility layer
└── test_visualization.py # Tests for visualization
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_inspect.py

# Run specific test
pytest tests/test_inspect.py::TestZarrInspection::test_list_zarr_arrays

# Stop on first failure
pytest -x

# Show print statements
pytest -s
```

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=zarr_utils --cov-report=html

# View HTML report
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=zarr_utils --cov-report=term-missing
```

### Testing with Different Zarr Versions

```bash
# Test with Zarr v2
pip install "zarr<3"
pytest

# Test with Zarr v3
pip install "zarr>=3.0.0"
pytest
```

## Writing Tests

### Test File Structure

```python
"""Test module description."""
import pytest
import numpy as np
import zarr
from zarr_utils import function_to_test

class TestClassName:
    """Test class description."""
    
    @pytest.fixture
    def sample_store(self, tmp_path):
        """Create a sample Zarr store."""
        store_path = tmp_path / "test.zarr"
        # Setup code
        yield store_path
        # Teardown code (if needed)
    
    def test_basic_functionality(self, sample_store):
        """Test basic functionality."""
        result = function_to_test(sample_store)
        assert result is not None
```

### Common Fixtures

#### Temporary Zarr Store

```python
@pytest.fixture
def temp_zarr_store(tmp_path):
    """Create a temporary Zarr store with test data."""
    store_path = tmp_path / "test.zarr"
    
    store = zarr.open_group(str(store_path), mode='w')
    store.attrs['test'] = True
    
    # Add test data
    data = np.random.rand(100, 200, 300).astype('float32')
    from zarr_utils.compat import create_array_compat
    arr = create_array_compat(store, 'data', data=data, chunks=(50, 100, 150))
    arr.attrs['units'] = 'test_units'
    
    yield str(store_path)
```

#### Remote Store Mock

```python
@pytest.fixture
def mock_s3_store(monkeypatch):
    """Mock S3 store for testing."""
    import fsspec
    from unittest.mock import MagicMock
    
    mock_fs = MagicMock()
    mock_mapper = MagicMock()
    
    def mock_get_mapper(url, **kwargs):
        if url.startswith('s3://'):
            return mock_mapper
        return fsspec.get_mapper(url, **kwargs)
    
    monkeypatch.setattr(fsspec, 'get_mapper', mock_get_mapper)
    return mock_mapper
```

### Testing Patterns

#### Testing Exceptions

```python
def test_invalid_input():
    """Test that invalid input raises appropriate error."""
    with pytest.raises(ValueError, match="Invalid store path"):
        list_zarr_arrays("")
    
    with pytest.raises(FileNotFoundError):
        list_zarr_arrays("/nonexistent/path.zarr")
```

#### Testing Output

```python
def test_console_output(capsys):
    """Test console output."""
    inspect_zarr_store("test.zarr", summarize=True)
    
    captured = capsys.readouterr()
    assert "Inspecting Zarr store" in captured.out
    assert "Total arrays:" in captured.out
```

#### Parametrized Tests

```python
@pytest.mark.parametrize("dtype,expected_size", [
    (np.float32, 4),
    (np.float64, 8),
    (np.int32, 4),
    (np.uint8, 1),
])
def test_array_sizes(temp_zarr_store, dtype, expected_size):
    """Test array size calculation for different dtypes."""
    data = np.ones((10, 10), dtype=dtype)
    # Test implementation
```

#### Testing with Both Zarr Versions

```python
from zarr_utils.compat import IS_ZARR_V3

def test_version_specific_behavior():
    """Test behavior that differs between versions."""
    if IS_ZARR_V3:
        # Test v3 specific behavior
        assert hasattr(array, 'compressors')
    else:
        # Test v2 specific behavior
        assert hasattr(array, 'compressor')
```

## Integration Tests

### Testing with Real Data

```python
@pytest.mark.integration
def test_with_real_s3_data():
    """Test with real S3 data (requires internet)."""
    # Skip if no internet
    import urllib.request
    try:
        urllib.request.urlopen('http://google.com', timeout=1)
    except:
        pytest.skip("No internet connection")
    
    # Test with public S3 data
    arrays = list_zarr_arrays(
        "s3://janelia-cosem-datasets/jrc_hela-2/jrc_hela-2.zarr",
        storage_options={'anon': True}
    )
    assert len(arrays) > 0
```

### Performance Tests

```python
@pytest.mark.slow
def test_large_array_performance(benchmark):
    """Benchmark array listing performance."""
    def setup():
        # Create large store
        store = zarr.open_group("large.zarr", mode='w')
        for i in range(100):
            store.create_dataset(f'array_{i}', shape=(100, 100), chunks=(50, 50))
        return ("large.zarr",), {}
    
    benchmark.pedantic(list_zarr_arrays, setup=setup, rounds=10)
```

## Test Data

### Creating Test Data

```python
def create_test_hierarchy():
    """Create complex test hierarchy."""
    store = zarr.open_group("hierarchy.zarr", mode='w')
    
    # Root arrays
    store.create_dataset('root_array', data=np.arange(100))
    
    # Groups
    raw = store.create_group('raw')
    raw.create_dataset('channel0', data=np.random.rand(64, 128, 128))
    raw.create_dataset('channel1', data=np.random.rand(64, 128, 128))
    
    processed = store.create_group('processed')
    processed.attrs['pipeline'] = 'v1.0'
    
    return store
```

### Using Test Data Files

```python
@pytest.fixture
def sample_data_path():
    """Path to sample data."""
    import importlib.resources
    
    if hasattr(importlib.resources, 'files'):
        # Python 3.9+
        return importlib.resources.files('tests.data') / 'sample.zarr'
    else:
        # Python 3.7-3.8
        with importlib.resources.path('tests.data', 'sample.zarr') as p:
            return p
```

## Mocking

### Mocking File Systems

```python
def test_with_mock_filesystem(tmp_path, monkeypatch):
    """Test with mocked filesystem operations."""
    from unittest.mock import Mock, patch
    
    # Mock fsspec
    with patch('fsspec.get_mapper') as mock_get_mapper:
        mock_mapper = Mock()
        mock_mapper.__contains__ = Mock(return_value=True)
        mock_mapper.__getitem__ = Mock(return_value=b'{}')
        mock_get_mapper.return_value = mock_mapper
        
        # Test code
        result = consolidate_metadata("s3://bucket/data.zarr")
        assert mock_get_mapper.called
```

### Mocking Time

```python
def test_operation_timing(monkeypatch):
    """Test operation timing."""
    import time
    
    # Mock time for consistent tests
    current_time = [0.0]
    
    def mock_time():
        current_time[0] += 1.0
        return current_time[0]
    
    monkeypatch.setattr(time, 'time', mock_time)
    
    with ZarrDebugger() as debugger:
        with debugger.operation("test"):
            pass  # Should take 1 second
    
    assert debugger.operation_times[0]['duration'] == 1.0
```

## Best Practices

### Test Organization

1. **Group related tests** in classes
2. **Use descriptive names** for tests and fixtures
3. **One assertion per test** when possible
4. **Test both success and failure** cases
5. **Use fixtures** for setup/teardown

### Test Data

1. **Use temporary directories** for test data
2. **Clean up after tests** (use fixtures with yield)
3. **Keep test data small** for speed
4. **Mock external services** when possible

### Performance

1. **Mark slow tests** with `@pytest.mark.slow`
2. **Use `pytest-xdist`** for parallel execution
3. **Profile tests** that seem slow
4. **Cache expensive fixtures** with `scope='session'`

## Continuous Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.9', '3.10', '3.11']
        zarr-version: ['2.*', '3.*']
    
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
        pip install "zarr~=${{ matrix.zarr-version }}"
    
    - name: Run tests
      run: pytest --cov=zarr_utils --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Debugging Failed Tests

### Using pytest debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at start of test
pytest --trace
```

### Verbose Output

```bash
# Show all output
pytest -vvs

# Show local variables on failure
pytest -l
```

### Reproducing CI Failures

```bash
# Run with same environment as CI
docker run -it python:3.9 bash
pip install -e ".[dev]"
pytest
```