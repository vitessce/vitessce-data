#!/usr/bin/env python3
import csv
import argparse
import json

def round_conv(s):
    # After the first decimal place, digits repeat, which I think
    # indicates the limited precision of the data.
    return round(float(s), 2)

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
            data_col_names = [k for k in row.keys() if k[:2] in {'ni', 'ci'}]
            cells[row['id']] = {
                'xy': [round_conv(xy) for xy in [row['x'], row['y']]],
                'genes': { k: row[k] for k in data_col_names }
            }

    json.dump(cells, args.cells_file, indent=1)
