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
                indices = np.linspace(
                    0, poly.shape[0], num=args.sample,
                    endpoint=False, dtype=int)
                vertices = np.take(poly, axis=0, indices=indices)
                # This isn't perfect: fails if ray from center crosses boundary multiple times.
                center = np.mean(vertices, axis=0)
                centered = vertices - center
                angles = np.arctan2(centered[:,0], centered[:,1])
                order = np.argsort(angles)
                metadata[cell_id]['poly'] = vertices[order].tolist()

    print(json.dumps(metadata, indent=1))
