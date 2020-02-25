#!/usr/bin/env python3
import csv
import argparse
import json


def round_conv(s):
    # TODO: Truncating after decimal point might be slightly too aggressive?
    return round(float(s))


def row_to_dict(row):
    '''
    >>> row = {
    ...        'id': '123', 'x': '1.2', 'y': '3.4',
    ...        'ci:ABC:mean': '5.6', 'ni:XYZ:mean': '7.8',
    ...        'ci:EMPTY:mean': '9.0'
    ... }
    >>> row_to_dict(row)
    {'xy': [1, 3], 'genes': {'ci:ABC': 6, 'ni:XYZ': 8}}
    '''

    data_col_names = [
        k for k in row.keys()
        if k[:2] in {'ni', 'ci'} and 'EMPTY' not in k
    ]
    return {
        'xy': [round_conv(xy) for xy in [row['x'], row['y']]],
        'genes': {
            k.replace(':mean', ''): round_conv(row[k])
            # Each one has ":mean", so remove.
            for k in data_col_names
        }
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create JSON with cell metadata from Cytokit CSV.')
    parser.add_argument(
        '--cytokit', required=True,
        help='CSV from Cytokit')
    parser.add_argument(
        '--cells_file', type=argparse.FileType('x'),
        help='Write the cleaned cell data to this file.')
    # TODO: Neighborhood information is also in this file.
    # parser.add_argument(
    #     '--neighborhoods_file', type=argparse.FileType('x'),
    #     help='Write the cell neighborhoods to this file.')
    args = parser.parse_args()

    cells = {}
    with open(args.cytokit) as csv_file:
        for row in csv.DictReader(csv_file):
            cells[row['id']] = row_to_dict(row)

    json.dump(cells, args.cells_file, indent=1)
