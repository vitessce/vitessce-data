#!/usr/bin/env python3

import json
import numpy as np
import pandas as pd
from collections import defaultdict
import argparse


def cells_json(df):
    cells_dict = {}
    xy_dict = defaultdict(list)

    for index, row in df.iterrows():
            xy_dict[row['cell']].append([row['x'], row['y']])

    for cell in xy_dict:
        cells_dict[cell] = {
            "mappings": {},
            "genes": {},
            "xy": list(map(np.mean, zip(*xy_dict[cell]))),
            "factors": {},
            "poly": []
        }

    return cells_dict


def molecules_json(df):
    molecules_dict = defaultdict(list)

    for index, row in df.iterrows():
            molecules_dict[row['gene1']].append([row['x'], row['y']])

    return molecules_dict


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create JSON with cell metadata from erMAID CSV.')
    parser.add_argument(
        '--csv_file', required=True,
        help='CSV file produced by Giotto object.')
    parser.add_argument(
        '--cells_file', type=argparse.FileType('x'),
        help='Write the cell data to this file.')
    parser.add_argument(
        '--molecules_file', type=argparse.FileType('x'),
        help='Write the cell factors to this file.')
    args = parser.parse_args()

    with open(args.csv_file) as csv_file:
        df = pd.read_csv(csv_file)

    if args.cells_file:
        json.dump(cells_json(df), args.cells_file, indent=1)

    if args.molecules_file:
        json.dump(molecules_json(df), args.molecules_file, indent=1)
