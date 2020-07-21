import argparse

from anndata import read_h5ad
import pandas as pd
import scipy.cluster
import zarr
from numcodecs import Zlib


def h5ad_to_zarr(input_file, output_file):
    gexp = read_h5ad(input_file)
    gexp_arr = gexp.X
    gexp_df = gexp.to_df()

    # Re-scale the gene expression values between 0 and 255 (one byte ints).
    gexp_arr_min = gexp_arr.min()
    gexp_arr_max = gexp_arr.max()
    gexp_arr_range = gexp_arr_max - gexp_arr_min
    gexp_arr_ratio = 255 / gexp_arr_range
    gexp_norm_arr = (gexp_arr - gexp_arr_min) * gexp_arr_ratio

    # Perform hierarchical clustering along the genes axis.
    Z = scipy.cluster.hierarchy.linkage(gexp_norm_arr.T, method="ward")
    labels = gexp.var.index.values

    # Get the hierarchy-based ordering of genes.
    leaf_index_list = scipy.cluster.hierarchy.leaves_list(Z)
    leaf_list = labels[leaf_index_list].tolist()

    # Create a new *ordered* gene expression dataframe.
    gexp_norm_df = pd.DataFrame(
        index=gexp_df.index.values.tolist(),
        columns=gexp_df.columns.values.tolist(),
        data=gexp_norm_arr
    )
    sorted_gexp_norm_df = gexp_norm_df[leaf_list]
    sorted_gene_names = sorted_gexp_norm_df.columns.values.tolist()
    sorted_cell_names = sorted_gexp_norm_df.index.values.tolist()

    # Save the data to the output file.
    z = zarr.open(
        output_file,
        mode='w',
        shape=sorted_gexp_norm_df.shape,
        dtype='uint8',
        compressor=Zlib(level=1)
    )
    # Store the matrix.
    z[:] = sorted_gexp_norm_df.values
    # Store the rows/observations (cell IDs).
    z.attrs["rows"] = sorted_cell_names
    # Store the columns/variables (gene IDs).
    z.attrs["cols"] = sorted_gene_names


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i',
        '--input_file',
        type=str,
        required=True,
        help='Input h5ad file'
    )
    parser.add_argument(
        '-o',
        '--output_file',
        type=str,
        required=True,
        help='Output Zarr file'
    )
    args = parser.parse_args()
    h5ad_to_zarr(args.input_file, args.output_file)
