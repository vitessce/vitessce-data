#!/usr/bin/env python3

import json
import numpy as np
import pandas as pd
from collections import defaultdict
from cell_reader import octagon, get_genes
import argparse


def cells_dict(df):
    cells_dict = {}
    genes_pair_list = defaultdict(list)
    xy_dict = defaultdict(list)

    df_genes = df.groupby(['cell', 'gene1']).size().reset_index(name='count')

    for index, row in df_genes.iterrows():
        genes_pair_list[row['cell']].append((row['gene1'], row['count']))

    for index, row in df.iterrows():
        xy_dict[row['cell']].append([row['x'], row['y']])

    for cell in xy_dict:
        cells_dict[cell] = {
            "mappings": {},
            "genes": dict(genes_pair_list[cell]),
            "xy": list(map(np.mean, zip(*xy_dict[cell]))),
            "factors": {},
            "poly": octagon(np.array(xy_dict[cell]))
        }

    return cells_dict


def molecules_dict(df):
    molecules_dict = defaultdict(list)

    for index, row in df.iterrows():
        molecules_dict[row['gene1']].append([row['x'], row['y']])

    return molecules_dict


def image_dict():
    cloud_target = open('cloud_target.txt').read().strip()
    url = 'https://s3.amazonaws.com/{}/wang.images/info.json'.format(
        cloud_target
    )
    image_dict = {
        'MERrfish': {
            'sample': 1,
            'tileSource': url
        }
    }

    return image_dict


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create JSON with cell metadata from MERmaid CSV.')
    parser.add_argument(
        '--csv_file', required=True,
        help='CSV file from MERfish data.')
    parser.add_argument(
        '--cells_file', type=argparse.FileType('x'),
        help='Write the cell data to this file.')
    parser.add_argument(
        '--molecules_file', type=argparse.FileType('x'),
        help='Create JSON with molecule locations.')
    parser.add_argument(
        '--genes_file', type=argparse.FileType('x'),
        help='Write a list of genes to this file.')
    parser.add_argument(
        '--images_file', type=argparse.FileType('x'),
        help='JSON file which will include image location.')
    args = parser.parse_args()

    with open(args.csv_file) as csv_file:
        df = pd.read_csv(csv_file)

    metadata = cells_dict(df)

    if args.cells_file:
        json.dump(metadata, args.cells_file, indent=1)
    if args.molecules_file:
        json.dump(molecules_dict(df), args.molecules_file, indent=1)
    if args.genes_file:
        json.dump(get_genes(metadata), args.genes_file, indent=1)
    if args.images_file:
        json.dump(image_dict(), args.images_file, indent=1)
