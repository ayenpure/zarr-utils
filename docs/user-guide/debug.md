# Debugging Tools

zarr-utils provides comprehensive debugging tools to help diagnose and fix common Zarr issues. These tools provide clear error messages, performance metrics, and actionable suggestions.

## Core Components

### ZarrDebugger

A context manager for tracking and timing Zarr operations.

```python
from zarr_utils.debug import ZarrDebugger

# Create debugger instance
debugger = ZarrDebugger(verbose=True)

# Track operations
with debugger.operation("Loading data"):
    data = zarr.open_array("data.zarr")
    
with debugger.operation("Computing statistics"):
    mean = data[:].mean()

# View summary
debugger.summarize()
```

### diagnose_zarr_store

Comprehensive diagnostics for Zarr stores.

```python
from zarr_utils import diagnose_zarr_store

# Basic diagnosis
report = diagnose_zarr_store("data.zarr")

# Detailed diagnosis with performance metrics
report = diagnose_zarr_store("s3://bucket/data.zarr", 
                           detailed=True,
                           storage_options={'anon': True})
```

### explain_zarr_error

User-friendly error explanations with solutions.

```python
from zarr_utils import explain_zarr_error

try:
    store = zarr.open_consolidated("data.zarr")
except Exception as e:
    print(explain_zarr_error(e))
```

### enable_debug_mode

Enable verbose debugging for all zarr-utils operations.

```python
from zarr_utils.debug import enable_debug_mode

# Enable debug mode
enable_debug_mode()

# Now all operations will be tracked
# Note: This uses monkey patching and should only be used during development
```

## Understanding Diagnostic Reports

### Report Structure

```python
{
    'accessible': True,
    'store_type': 'Local filesystem',
    'has_consolidated_metadata': True,
    'total_arrays': 5,
    'total_size_bytes': 1073741824,
    'arrays': {
        'data': {
            'shape': (100, 200, 300),
            'chunks': (50, 100, 150),
            'dtype': 'float32',
            'compressor': 'blosc',
            'readable': True
        }
    },
    'performance': {
        'small_read_time': 0.002,
        'read_bandwidth_mbps': 450.5,
        'latency_estimate': 'low'
    },
    'issues': [],
    'suggestions': []
}
```

### Key Metrics

- **accessible**: Whether the store can be opened
- **store_type**: Local, S3, HTTP, etc.
- **performance**: Read speed and latency estimates
- **issues**: Problems found during diagnosis
- **suggestions**: Recommended fixes

## Common Debugging Scenarios

### Debugging Slow Performance

```python
# Diagnose performance issues
report = diagnose_zarr_store("s3://bucket/slow-data.zarr", detailed=True)

print(f"Read bandwidth: {report['performance']['read_bandwidth_mbps']:.1f} MB/s")
print(f"Latency: {report['performance']['latency_estimate']}")

if report['performance']['read_bandwidth_mbps'] < 10:
    print("⚠️ Slow read performance detected")
    print("Suggestions:")
    print("- Check network connection")
    print("- Use consolidated metadata")
    print("- Consider using a compute instance in the same region")
```

### Debugging Access Errors

```python
from zarr_utils import diagnose_zarr_store, explain_zarr_error

# Try to diagnose
report = diagnose_zarr_store("s3://private-bucket/data.zarr")

if not report['accessible']:
    print("Store is not accessible!")
    print(f"Issues: {report['issues']}")
    
    # Try with credentials
    report = diagnose_zarr_store(
        "s3://private-bucket/data.zarr",
        storage_options={
            'key': 'YOUR_KEY',
            'secret': 'YOUR_SECRET'
        }
    )
```

### Debugging Metadata Issues

```python
# Comprehensive metadata debugging
def debug_metadata(store_path):
    """Debug metadata issues step by step."""
    
    print(f"Debugging metadata for: {store_path}")
    print("-" * 50)
    
    # 1. Check if store exists
    report = diagnose_zarr_store(store_path)
    if not report['accessible']:
        print("❌ Store is not accessible")
        return
    
    print("✓ Store is accessible")
    
    # 2. Check consolidated metadata
    if not report['has_consolidated_metadata']:
        print("❌ No consolidated metadata found")
        print("   Fix: zu.consolidate_metadata(store_path)")
    else:
        print("✓ Consolidated metadata exists")
    
    # 3. Validate metadata
    from zarr_utils import validate_metadata
    validation = validate_metadata(store_path)
    
    if not validation['valid']:
        print(f"❌ Metadata validation failed ({len(validation['issues'])} issues)")
        for issue in validation['issues'][:5]:
            print(f"   - {issue}")
    else:
        print("✓ Metadata is valid")
    
    # 4. Check array accessibility
    print(f"\nChecking {report['total_arrays']} arrays:")
    for name, info in list(report['arrays'].items())[:3]:
        status = "✓" if info['readable'] else "❌"
        print(f"  {status} {name}: {info['shape']} ({info['dtype']})")

# Use it
debug_metadata("problematic_store.zarr")
```

## Error Explanation Examples

### Common Errors and Solutions

```python
# Example 1: Missing metadata
try:
    store = zarr.open_consolidated("data.zarr")
except KeyError as e:
    print(explain_zarr_error(e))
    # Output:
    # ❌ Error: KeyError: '.zmetadata'
    # 
    # 💡 What this means:
    #    The Zarr store is missing consolidated metadata.
    # 
    # 🔧 Suggestions:
    #    • Run: zarr_utils.consolidate_metadata('data.zarr')
    #    • Or open without consolidation: zarr.open_group(store, mode='r')

# Example 2: Permission error
try:
    data = zarr.open_array("s3://private-bucket/data.zarr")
except PermissionError as e:
    print(explain_zarr_error(e))
    # Output includes AWS credential setup instructions

# Example 3: Codec error
try:
    arr = zarr.open_array("data_with_lz4.zarr")
    data = arr[:]
except ValueError as e:
    print(explain_zarr_error(e, context={'operation': 'reading compressed data'}))
    # Output includes codec installation instructions
```

## Performance Profiling

### Tracking Operation Times

```python
from zarr_utils.debug import ZarrDebugger
import time

debugger = ZarrDebugger(verbose=True)

# Profile different operations
with debugger.operation("Open store"):
    store = zarr.open_group("large_dataset.zarr", mode='r')

with debugger.operation("List arrays"):
    arrays = list(store.arrays())

with debugger.operation("Load slice"):
    data = store['array'][0:100, :, :]

with debugger.operation("Compute statistics"):
    mean = data.mean()
    std = data.std()

# Get detailed timing report
debugger.summarize()
```

### Comparing Access Methods

```python
def compare_access_methods(store_path):
    """Compare performance of different access methods."""
    debugger = ZarrDebugger()
    
    # Method 1: Direct access
    with debugger.operation("Direct access"):
        store = zarr.open(store_path, mode='r')
        _ = list(store.arrays())
    
    # Method 2: Consolidated access
    with debugger.operation("Consolidated access"):
        store = zarr.open_consolidated(store_path, mode='r')
        _ = list(store.arrays())
    
    # Method 3: With fsspec
    with debugger.operation("FSSpec access"):
        import fsspec
        mapper = fsspec.get_mapper(store_path)
        store = zarr.open(mapper, mode='r')
        _ = list(store.arrays())
    
    debugger.summarize()
```

## Advanced Debugging

### Custom Debug Context

```python
class CustomDebugger(ZarrDebugger):
    """Extended debugger with custom metrics."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_loaded = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def track_data_load(self, nbytes):
        """Track amount of data loaded."""
        self.data_loaded += nbytes
        if self.verbose:
            print(f"  Loaded {nbytes:,} bytes (total: {self.data_loaded:,})")
    
    def track_cache(self, hit=True):
        """Track cache performance."""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def summarize(self):
        """Extended summary with custom metrics."""
        super().summarize()
        print(f"\nData Transfer:")
        print(f"  Total loaded: {self.data_loaded / 1e6:.1f} MB")
        if self.cache_hits + self.cache_misses > 0:
            hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) * 100
            print(f"  Cache hit rate: {hit_rate:.1f}%")
```

### Debug Logging

```python
import logging
from zarr_utils.debug import enable_debug_mode

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='zarr_debug.log'
)

# Enable debug mode with logging
enable_debug_mode()

# All operations will now be logged
store = zarr.open("data.zarr")
```

## Best Practices

1. **Use debugger in development** - Remove in production for performance
2. **Start with diagnose_zarr_store** - It catches most common issues
3. **Keep debug logs** - Useful for troubleshooting intermittent issues
4. **Profile before optimizing** - Measure to find actual bottlenecks
5. **Use error explanations** - They save debugging time

## Integration with Monitoring

### Simple Metrics Collection

```python
from datetime import datetime
import json

class MetricsCollector:
    """Collect Zarr operation metrics."""
    
    def __init__(self):
        self.metrics = []
    
    def record_operation(self, store_path, operation, duration, success=True):
        """Record an operation metric."""
        self.metrics.append({
            'timestamp': datetime.utcnow().isoformat(),
            'store': store_path,
            'operation': operation,
            'duration_ms': duration * 1000,
            'success': success
        })
    
    def save_metrics(self, filename='zarr_metrics.json'):
        """Save metrics to file."""
        with open(filename, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def get_summary(self):
        """Get metrics summary."""
        if not self.metrics:
            return "No metrics collected"
        
        total_ops = len(self.metrics)
        successful = sum(1 for m in self.metrics if m['success'])
        avg_duration = sum(m['duration_ms'] for m in self.metrics) / total_ops
        
        return f"""
Metrics Summary:
  Total operations: {total_ops}
  Successful: {successful} ({successful/total_ops*100:.1f}%)
  Average duration: {avg_duration:.1f}ms
        """

# Use with debugger
collector = MetricsCollector()
debugger = ZarrDebugger()

with debugger.operation("Load data") as op:
    try:
        data = zarr.open_array("data.zarr")
        collector.record_operation("data.zarr", "load", op.duration)
    except Exception as e:
        collector.record_operation("data.zarr", "load", op.duration, success=False)
        raise
```