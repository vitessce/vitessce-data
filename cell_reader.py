#!/usr/bin/env python3

import json
import argparse
from pickle import load

from loom_reader import LoomReader

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create JSON with cell metadata and segmentation.')
    parser.add_argument('--pickle', required=True,
        help='Pickle file with cell segmentation data')
    parser.add_argument('--loom', required=True,
        help='Loom file with cell metadata')
    args = parser.parse_args()

    loom = LoomReader(args.loom)
    with open(args.pickle, 'rb') as f:
        segmentation = load(f)

    metadata = loom.data()

    for cell_id, poly in segmentation.items():
        if cell_id in metadata:
            metadata[cell_id]['poly'] = poly.tolist()

    print(json.dumps(metadata, indent=1))
