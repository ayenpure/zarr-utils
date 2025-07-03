import os
import numpy as np
import xarray as xr
import vtk
from vtk.util import numpy_support

def wrap_vtk(data: xr.DataArray):
    """
    Convert and return as vtkImageData

    Parameters
    ----------
    data : xr.DataArray
        3D data to write.
    output_path : str
        File path ending in .vtk.
    """
    arr = np.asarray(data, order="F")
    dtype = numpy_support.get_vtk_array_type(arr.dtype)

    vtk_array = numpy_support.numpy_to_vtk(
        arr.ravel(order="F"), deep=True, array_type=dtype
    )

    nz, ny, nx = arr.shape
    spacing = tuple(np.diff(data.coords[dim].values[:2])[0] if dim in data.coords else 1.0
                    for dim in ["z", "y", "x"])
    spacing = tuple(float(s) for s in spacing)

    img = vtk.vtkImageData()
    img.SetDimensions(nx, ny, nz)
    img.SetSpacing(spacing)
    img.GetPointData().SetScalars(vtk_array)
    vtk_array.SetName(data.name or "values")

    return img

def to_vtk(data: xr.DataArray, output_path: str):
    """
    Convert and write as legacy .vtk file (for compatibility).

    Parameters
    ----------
    data : xr.DataArray
        3D data to write.
    output_path : str
        File path ending in .vtk.
    """
    if not output_path.endswith(".vtk"):
        raise ValueError("Output path must end in '.vtk'")
    
    img = wrap_vtk(data)

    writer = vtk.vtkDataSetWriter()
    writer.SetFileName(output_path)
    writer.SetInputData(img)
    writer.Write()