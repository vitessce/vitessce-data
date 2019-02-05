#!/usr/bin/env python3

import json
import argparse
import pickle

import numpy as np

from loom_reader import LoomReader

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create JSON with cell metadata and, '
                    'optionally, segmentation.')
    parser.add_argument(
        '--loom', required=True,
        help='Loom file with cell metadata')
    parser.add_argument(
        '--pkl',
        help='Pickle file with cell segmentation data')
    parser.add_argument(
        '--sample',
        default=16,
        help='Number of points to sample from each polygon')
    args = parser.parse_args()

    metadata = LoomReader(args.loom).data()

    if args.pkl:
        with open(args.pkl, 'rb') as f:
            segmentation = pickle.load(f)
        for cell_id, poly in segmentation.items():
            if cell_id in metadata:
                # SciPy has ConvexHull, but it segfaulted on me: perhaps
                #   https://github.com/scipy/scipy/issues/9751
                # ... and even if I fixed it locally,
                # not sure I'd want that fragility.
                #
                # Also: The goal is really just to get a simplified shape...
                # A convex hull is too precise in some ways,
                # while in others it falls short, ie, concavities.
                w = int(np.min(poly[:, [0]]))
                e = int(np.max(poly[:, [0]]))
                n = int(np.min(poly[:, [1]]))
                s = int(np.max(poly[:, [1]]))
                metadata[cell_id]['poly'] = [
                    [w, n],
                    [w, s],
                    [e, s],
                    [e, n]
                ]

    print(json.dumps(metadata, indent=1))
