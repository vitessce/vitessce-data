#!/usr/bin/env python3

import json
import argparse
import pandas as pd
from enum import Enum


class COLUMNS(Enum):
    # Cell Type Annotation column names
    CELL_ID = "cell_id"
    ANNOTATION = "annotation"
    PREDICTION_SCORE = "prediction_score"
    DATASET_ID = "dataset_id"


def factors_json(df, dataset_id):
    '''
    >>> df = pd.DataFrame(data=[
    ...    {
    ...         "cell_id": "cell_1",
    ...         "annotation": "B cell",
    ...         "prediction_score": 0.5,
    ...         "dataset_id": "A"
    ...    },
    ...    {
    ...         "cell_id": "cell_2",
    ...         "annotation": "T cell",
    ...         "prediction_score": 0.7,
    ...         "dataset_id": "A"
    ...    },
    ...    {
    ...         "cell_id": "cell_3",
    ...         "annotation": "dendritic cell",
    ...         "prediction_score": 0.2,
    ...         "dataset_id": "B"
    ...    }
    ... ])
    >>> dataset_id = 'A'
    >>> factors = factors_json(df, dataset_id)
    >>> factors.keys()
    dict_keys(['Cell Type Annotations'])
    >>> factors['Cell Type Annotations'].keys()
    dict_keys(['map', 'cells'])
    >>> factors['Cell Type Annotations']['map']
    ['B cell', 'T cell']

    '''
    df = df.loc[df[COLUMNS.DATASET_ID.value] == dataset_id].copy()

    # Get a list containing all unique annotation values in the input file.
    annotation_values = df[COLUMNS.ANNOTATION.value].unique().tolist()

    # Append a temporary column to the dataframe containing
    # the index of each annotation,
    # relative to the `annotation_values` list.
    df["annotation_index"] = df[COLUMNS.ANNOTATION.value].apply(
        lambda val: annotation_values.index(val)
    )

    # Construct the factors dict.
    factors = {
        "Cell Type Annotations": {
            "map": annotation_values,
            "cells": dict(zip(
                df[COLUMNS.CELL_ID.value].tolist(),
                df["annotation_index"].tolist()
            ))
        }
    }
    return factors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create JSON with cell annotation '
        'metadata from CSV.')
    parser.add_argument(
        '--csv_file', required=True,
        help='CSV file containing annotations.')
    parser.add_argument(
        '--dataset_id', type=str,
        help='Filter by this dataset ID.')
    parser.add_argument(
        '--factors_file', type=argparse.FileType('w'),
        help='Write the cell factors to this file.')
    args = parser.parse_args()

    with open(args.csv_file) as csv_file:
        df = pd.read_csv(csv_file)

    if args.factors_file:
        json.dump(
            factors_json(df, args.dataset_id),
            args.factors_file,
            indent=1
        )
