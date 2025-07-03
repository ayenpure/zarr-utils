import sys
from zarr_utils.inspect import list_zarr_arrays
from zarr_utils.xarray import open_xarray
from zarr_utils.convert import wrap_vtk

import pyvista as pv


def prompt_for_choice(arrays):
    print("\nAvailable arrays:")
    for i, arr in enumerate(arrays):
        print(f"[{i}] {arr['path']:40s}  {arr['shape']}  {arr['dtype']}  {arr['size_bytes'] / 1e6:.2f} MB")

    while True:
        try:
            choice = int(input("\nEnter the number of the array to load: "))
            if 0 <= choice < len(arrays):
                return arrays[choice]
        except ValueError:
            pass
        print("Invalid input. Try again.")


def main():
    url = input("Enter the Zarr dataset URL (e.g. s3://janelia-cosem-datasets/jrc_hela-1/jrc_hela-1.zarr): ").strip()

    arrays = list_zarr_arrays(url, anon=True)
    if not arrays:
        print("No arrays found.")
        sys.exit(1)

    selected = prompt_for_choice(arrays)

    print(f"\nLoading: {selected['path']}")
    ds = open_xarray(url, selected["path"], var_name="values", anon=True, with_coords=True)
    da = ds["values"]

    print("Converting to VTK...")
    vtk_image = wrap_vtk(da)

    print("Rendering...")
    pl = pv.Plotter()
    pl.add_volume(vtk_image, cmap="viridis", opacity="sigmoid")
    pl.show()


if __name__ == "__main__":
    main()
