#!/usr/bin/env python3
import csv
import argparse
import json

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
            cells[row['id']] = {
                'xy': [row['x'], row['y']]
            }

    json.dump(cells, args.cells_file, indent=1)
