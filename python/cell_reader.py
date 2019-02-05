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
                # not sure we want that fragility.
                #
                # Also: The goal is really just to get a simplified shape...
                # A convex hull is too precise in some ways,
                # while in others it falls short, ie, concavities.
                #
                # I kind-of like the obvious artificiality of an octagon.

                # Was unsigned, and substraction causes underflow.
                poly_as_int = poly.astype('int')
                min_x = np.min(poly_as_int[:, [0]])
                max_x = np.max(poly_as_int[:, [0]])
                min_y = np.min(poly_as_int[:, [1]])
                max_y = np.max(poly_as_int[:, [1]])

                summed = np.sum(poly_as_int, axis=1)
                diffed = np.diff(poly_as_int, axis=1)

                min_sum = np.min(summed)
                max_sum = np.max(summed)
                min_diff = np.min(diffed)
                max_diff = np.max(diffed)

                metadata[cell_id]['poly'] = [
                    [min_x, min_y],
                    [min_x, max_y],
                    [max_x, max_y],
                    [max_x, min_y]
                ]

    print(json.dumps(metadata, indent=1))
