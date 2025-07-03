import os

import numpy as np
import xarray as xr

try:
    import vtk
    from vtk.util import numpy_support

    HAS_VTK = True
except ImportError:
    HAS_VTK = False


def wrap_vtk(data: xr.DataArray) -> "vtk.vtkImageData":
    """
    Convert xarray DataArray to vtkImageData.

    Parameters
    ----------
    data : xr.DataArray
        3D data array with optional coordinate information.

    Returns
    -------
    vtk.vtkImageData
        VTK image data object.

    Raises
    ------
    ImportError
        If VTK is not installed.
    ValueError
        If data is not 3D.
    """
    if not HAS_VTK:
        raise ImportError("VTK is required for this function. Install with: pip install vtk")
    # Validate dimensions
    if data.ndim != 3:
        raise ValueError(f"Expected 3D array, got {data.ndim}D array with shape {data.shape}")

    # Convert to Fortran-contiguous array for VTK
    arr = np.asarray(data, order="F")

    # Get VTK data type
    try:
        dtype = numpy_support.get_vtk_array_type(arr.dtype)
    except TypeError:
        # Fallback for unsupported types
        arr = arr.astype(np.float32)
        dtype = numpy_support.get_vtk_array_type(np.float32)

    vtk_array = numpy_support.numpy_to_vtk(arr.ravel(order="F"), deep=True, array_type=dtype)

    nz, ny, nx = arr.shape

    # Extract spacing from coordinates or attributes
    spacing = []
    for dim in ["z", "y", "x"]:
        if dim in data.coords and len(data.coords[dim]) > 1:
            # Calculate spacing from coordinates
            coord_vals = data.coords[dim].values
            space = float(np.diff(coord_vals[:2])[0])
            spacing.append(abs(space))  # Ensure positive spacing
        else:
            # Try to get from attributes
            space = 1.0
            if "voxel_spacing_nm" in data.attrs:
                try:
                    idx = ["z", "y", "x"].index(dim)
                    space = float(data.attrs["voxel_spacing_nm"][idx]) * 1e-9
                except (IndexError, ValueError, KeyError):
                    pass
            spacing.append(space)

    spacing = tuple(spacing)

    img = vtk.vtkImageData()
    img.SetDimensions(nx, ny, nz)
    img.SetSpacing(spacing)

    # Set origin if available
    origin = [0.0, 0.0, 0.0]
    for i, dim in enumerate(["z", "y", "x"]):
        if dim in data.coords and len(data.coords[dim]) > 0:
            origin[i] = float(data.coords[dim].values[0])
    img.SetOrigin(origin[::-1])  # VTK uses x,y,z order

    img.GetPointData().SetScalars(vtk_array)
    vtk_array.SetName(data.name or "values")

    # Add metadata as field data
    if data.attrs:
        field_data = img.GetFieldData()
        for key, value in data.attrs.items():
            if isinstance(value, (int, float)):
                arr = vtk.vtkFloatArray()
                arr.SetName(str(key))
                arr.SetNumberOfTuples(1)
                arr.SetValue(0, float(value))
                field_data.AddArray(arr)
            elif isinstance(value, str):
                arr = vtk.vtkStringArray()
                arr.SetName(str(key))
                arr.SetNumberOfValues(1)
                arr.SetValue(0, value)
                field_data.AddArray(arr)

    return img


def to_vtk(data: xr.DataArray, output_path: str, binary: bool = True) -> None:
    """
    Convert and write xarray DataArray as legacy .vtk file.

    Parameters
    ----------
    data : xr.DataArray
        3D data to write.
    output_path : str
        File path ending in .vtk.
    binary : bool, optional
        Write in binary format (default: True). Binary is more efficient.

    Raises
    ------
    ValueError
        If output path doesn't end with .vtk
    ImportError
        If VTK is not installed
    """
    if not output_path.endswith(".vtk"):
        raise ValueError("Output path must end in '.vtk'")

    img = wrap_vtk(data)

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    writer = vtk.vtkDataSetWriter()
    writer.SetFileName(output_path)
    writer.SetInputData(img)

    if binary:
        writer.SetFileTypeToBinary()
    else:
        writer.SetFileTypeToASCII()

    writer.Write()


def to_vti(data: xr.DataArray, output_path: str, compression: bool = True) -> None:
    """
    Convert and write xarray DataArray as XML VTK ImageData (.vti) file.

    VTI format is more modern than legacy VTK and supports compression.

    Parameters
    ----------
    data : xr.DataArray
        3D data to write.
    output_path : str
        File path ending in .vti.
    compression : bool, optional
        Enable compression (default: True).

    Raises
    ------
    ValueError
        If output path doesn't end with .vti
    ImportError
        If VTK is not installed
    """
    if not output_path.endswith(".vti"):
        raise ValueError("Output path must end in '.vti'")

    img = wrap_vtk(data)

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    writer = vtk.vtkXMLImageDataWriter()
    writer.SetFileName(output_path)
    writer.SetInputData(img)

    if compression:
        writer.SetCompressorTypeToZLib()
    else:
        writer.SetCompressorTypeToNone()

    writer.Write()
