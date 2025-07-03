import json

from zarr_utils.inspect import inspect_zarr_store, list_zarr_arrays

url = "s3://janelia-cosem-datasets/jrc_hela-1/jrc_hela-1.zarr"

if __name__ == "__main__":
    arrays = list_zarr_arrays(url)
    assert len(arrays) != 0

    summary = inspect_zarr_store(url)
    print(json.dumps(summary, indent=4))
