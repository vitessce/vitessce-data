import argparse

from anndata import read_h5ad
import pyarrow as pa
import pandas as pd
import numpy as np


def h5ad_to_arrow(h5ad_file, arrow_file):
    ann_data = read_h5ad(h5ad_file)
    umap = ann_data.obsm['X_umap'].transpose()
    leiden = ann_data.obs['leiden'].to_numpy().astype('uint8')
    index = ann_data.obs.index

    df = pd.DataFrame(
        data={'umap_x': umap[0], 'umap_y': umap[1], 'leiden': leiden},
        index=index
    )
    df['umap_x'] = df['umap_x'].astype(np.float32)
    df['umap_y'] = df['umap_y'].astype(np.float32)
    table = pa.Table.from_pandas(df)

    with pa.RecordBatchFileWriter(arrow_file, table.schema) as writer:
        writer.write(table)


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
        help='Output Arrow file'
    )
    args = parser.parse_args()
    h5ad_to_arrow(args.input_file, args.output_file)
