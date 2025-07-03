from .debug import ZarrDebugger, diagnose_zarr_store, enable_debug_mode, explain_zarr_error
from .inspect import inspect_zarr_store, list_zarr_arrays
from .metadata import consolidate_metadata, repair_metadata, validate_metadata
from .xarray import get_voxel_spacing, open_xarray

# Import VTK functions only if VTK is available
try:
    from .visualization import HAS_VTK, to_vti, to_vtk, wrap_vtk
except ImportError:
    HAS_VTK = False
    wrap_vtk = None
    to_vtk = None
    to_vti = None

__version__ = "1.1.6"

__all__ = [
    "__version__",
    # Core functionality
    "open_xarray",
    "get_voxel_spacing",
    "inspect_zarr_store",
    "list_zarr_arrays",
    # Metadata tools
    "consolidate_metadata",
    "validate_metadata",
    "repair_metadata",
    # Debug tools
    "diagnose_zarr_store",
    "explain_zarr_error",
    "enable_debug_mode",
    "ZarrDebugger",
]

# Only export VTK functions if available
if HAS_VTK:
    __all__.extend(["wrap_vtk", "to_vtk", "to_vti", "HAS_VTK"])
