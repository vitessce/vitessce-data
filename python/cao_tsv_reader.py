#!/usr/bin/env python3

import json
import csv
import argparse


def cells_dict(filename):
    cells = {}
    with open(filename) as file:
        rows = csv.reader(file, delimiter='\t')
        for row in rows:
            id, x, y = row
            cells[id] = {
                'mappings': {
                    't-SNE': [x, y]
                }
            }
    return cells


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create JSON from Cao t-SNE TSV from UCSB.')
    parser.add_argument(
        '--tsv_file', required=True,
        help='TSV file from UCSB giving t-SNE coordinates.')
    parser.add_argument(
        '--cells_file', type=argparse.FileType('x'), required=True,
        help='Write the cell data to this file.')
    args = parser.parse_args()

    cells = cells_dict(args.csv_file)
    json.dump(cells, args.cells_file, indent=1)
