#!/usr/bin/env python3

import json
import argparse
import pickle

import numpy as np

from loom_reader import LoomReader


def octagon(poly):
    '''
    Returns a bounding octagon.
    >>> square = np.array([[0,0], [0,1], [1,1], [1,0]])
    >>> octagon(square)
    [[0, 0], [0, 1], [0, 1], [1, 1], [1, 1], [1, 0], [1, 0], [0, 0]]

    >>> triangle = np.array([[1,0], [0,2], [2,3]])
    >>> octagon(triangle)
    [[0, 1], [0, 2], [1, 3], [2, 3], [2, 3], [2, 1], [1, 0], [1, 0]]

    >>> type(octagon(triangle)[0][0])
    <class 'int'>
    '''
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
    min_x = int(np.min(poly_as_int[:, [0]]))
    max_x = int(np.max(poly_as_int[:, [0]]))
    min_y = int(np.min(poly_as_int[:, [1]]))
    max_y = int(np.max(poly_as_int[:, [1]]))

    summed = np.sum(poly_as_int, axis=1)
    diffed = np.diff(poly_as_int, axis=1)

    min_sum = int(np.min(summed))
    max_sum = int(np.max(summed))
    min_diff = int(np.min(diffed))
    max_diff = int(np.max(diffed))

    return [
        [min_x, min_sum - min_x],
        [min_x, max_diff + min_x],  # ^ Left
        [max_y - max_diff, max_y],
        [max_sum - max_y, max_y],  # ^ Botton
        [max_x, max_sum - max_x],
        [max_x, min_diff + max_x],  # ^ Right
        [min_y - min_diff, min_y],
        [min_sum - min_y, min_y]  # ^ Top
    ]


def mean_coord(coords):
    '''
    The xy values in the Linnarsson data are not good:
    They take a different corner as the origin.
    So... we find the center of our polygon instead
    >>> mean_coord([[1,2], [3,4], [5,6]])
    [3.0, 4.0]

    '''
    return np.mean(coords, axis=0).tolist()


def get_transform(metadata):
    xy_array = np.array([cell['xy'] for cell in metadata.values()])
    max_xy = np.max(xy_array, axis=0)
    min_xy = np.min(xy_array, axis=0)
    domain = 2000
    # Limited by raster-based picking in deck.gl:
    # https://github.com/uber/deck.gl/issues/2658#issuecomment-463293063
    return {
        'x_shift': - (max_xy[0] + min_xy[0]) / 2,
        'y_shift': - (max_xy[1] + min_xy[1]) / 2,
        'x_scale': domain / (max_xy[0] - min_xy[0]),
        'y_scale': domain / (max_xy[1] - min_xy[1])
    }


def apply_transform(transform, xy):
    # TODO: Rounding should be based on precision of input.
    return [
        round((xy[0] + transform['x_shift']) * transform['x_scale'], 2),
        round((xy[1] + transform['y_shift']) * transform['y_scale'], 2)
    ]


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
        '--save_transform',
        help='Center the data at (0, 0), and save the transformation.'
    )
    args = parser.parse_args()

    metadata = LoomReader(args.loom).data()

    if args.pkl:
        with open(args.pkl, 'rb') as f:
            segmentation = pickle.load(f)
        for cell_id, poly in segmentation.items():
            if cell_id in metadata:
                simple_poly = octagon(poly)
                xy = mean_coord(simple_poly)
                metadata[cell_id]['poly'] = simple_poly
                metadata[cell_id]['xy'] = xy
    if args.save_transform:
        with open(args.save_transform, 'w') as f:
            transform = get_transform(metadata)
            json.dump(transform, f, indent=1)
            for cell in metadata.values():
                if 'xy' in cell:
                    cell['xy'] = apply_transform(transform, cell['xy'])
                if 'poly' in cell:
                    cell['poly'] = [
                        apply_transform(transform, xy) for xy in cell['poly']
                    ]

    print(json.dumps(metadata, indent=1))
