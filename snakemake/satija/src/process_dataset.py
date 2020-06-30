import argparse

import json
import pyarrow as pa
import pandas as pd

from constants import COLUMNS
from generate_cell_sets import (
    generate_leiden_cluster_cell_sets,
    generate_cell_type_cell_sets
)
from utils import (
    merge_cell_sets_trees
)


def generate_json_files(
    input_cells_arrow_file, input_annotations_csv_file, input_cl_obo_file,
    output_cells_json_file, output_factors_json_file,
    output_cell_sets_json_file
):
    cells_df = pa.ipc.open_file(input_cells_arrow_file).read_pandas()
    annotation_df = pd.read_csv(input_annotations_csv_file)
    annotation_df = annotation_df.set_index(COLUMNS.CELL_ID.value)

    df = cells_df.join(annotation_df)
    df.index = df.index.rename(COLUMNS.CELL_ID.value)

    df['leiden'] = df['leiden'].apply(lambda i: f"Cluster {str(i).zfill(2)}")
    df[COLUMNS.ANNOTATION.value] = df[COLUMNS.ANNOTATION.value].astype(str)

    cells_df_items = df.T.to_dict().items()

    # Generate .cells.json
    cells = {
        k: {
            "mappings": {"UMAP": [v['umap_x'], v['umap_y']]},
            "factors": {
                "Leiden Clustering": v['leiden'],
                "Cell Type Annotation": v[COLUMNS.ANNOTATION.value],
                "Cell Type Annotation Prediction Score":
                    '{:.2g}'.format(v[COLUMNS.PREDICTION_SCORE.value])
            }
        }
        for (k, v) in cells_df_items
    }
    with open(output_cells_json_file, 'w') as f:
        json.dump(cells, f, indent=1)

    # Generate data for .factors.json
    def get_factors(col_name):
        unique_values = sorted(df[col_name].unique().tolist())
        return {
            "map": unique_values,
            "cells": {
                k: unique_values.index(v[col_name])
                for (k, v) in cells_df_items
            }
        }
    factors = {
        "Leiden Clustering": get_factors('leiden'),
        "Cell Type Annotation": get_factors(COLUMNS.ANNOTATION.value)
    }
    with open(output_factors_json_file, 'w') as f:
        json.dump(factors, f, indent=1)

    # Remove annotations with NaN prediction scores
    df = df.dropna(subset=[COLUMNS.PREDICTION_SCORE.value], axis=0)

    # Generate data for .cell_sets.json
    df = df.reset_index()

    leiden_cell_sets = generate_leiden_cluster_cell_sets(df)
    cell_type_cell_sets = generate_cell_type_cell_sets(
        df,
        input_cl_obo_file
    )

    # Merge the Leiden Cluster and Cell Type Annotation cell sets.
    cell_sets = merge_cell_sets_trees(
        leiden_cell_sets,
        cell_type_cell_sets
    )

    with open(output_cell_sets_json_file, 'w') as f:
        json.dump(cell_sets, f, indent=1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-ic',
        '--input_cells_arrow_file',
        type=str,
        required=True,
        help='Input Arrow file'
    )
    parser.add_argument(
        '-ia',
        '--input_annotations_csv_file',
        type=str,
        required=True,
        help='Input Arrow file'
    )
    parser.add_argument(
        '-ico',
        '--input_cl_obo_file',
        type=str,
        required=True,
        help='Input EBI Cell Ontology OBO file'
    )
    parser.add_argument(
        '-oc',
        '--output_cells_json_file',
        required=True,
        help='Output cells.json file'
    )
    parser.add_argument(
        '-of',
        '--output_factors_json_file',
        required=True,
        help='Output factors.json file'
    )
    parser.add_argument(
        '-ocs',
        '--output_cell_sets_json_file',
        required=True,
        help='Output cell_sets.json file'
    )
    args = parser.parse_args()
    generate_json_files(
        args.input_cells_arrow_file,
        args.input_annotations_csv_file,
        args.input_cl_obo_file,
        args.output_cells_json_file,
        args.output_factors_json_file,
        args.output_cell_sets_json_file
    )
