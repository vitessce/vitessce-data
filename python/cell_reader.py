#!/usr/bin/env python3

import json
import argparse
import pickle
from collections import defaultdict

import numpy as np

from loom_reader import LoomReader
from transform import apply_transform, get_transform
from cluster import cluster as get_clusters
from delaunay import DictDelaunay2d


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
    So... we find the center of our polygon instead.

    >>> mean_coord([[1,2], [3,4], [5,6]])
    [3, 4]

    '''
    return [int(x) for x in np.mean(coords, axis=0).tolist()]


# Taken from http://linnarssonlab.org/osmFISH/clusters/
LOOKUP = {
  "Astrocyte Gfap": "Astrocyte",
  "Astrocyte Mfge8": "Astrocyte",
  "C. Plexus": "Ventricle",
  "Endothelial 1": "Vasculature",
  "Endothelial": "Vasculature",
  "Ependymal": "Ventricle",
  "Hippocampus": "Excitatory neurons",
  "Inhibitory CP": "Inhibitory neurons",
  "Inhibitory Cnr1": "Inhibitory neurons",
  "Inhibitory Crhbp": "Inhibitory neurons",
  "Inhibitory IC": "Inhibitory neurons",
  "Inhibitory Kcnip2": "Inhibitory neurons",
  "Inhibitory Pthlh": "Inhibitory neurons",
  "Inhibitory Vip": "Inhibitory neurons",
  "Microglia": "Brain immune",
  "Oligodendrocyte COP": "Oligodendrocytes",
  "Oligodendrocyte MF": "Oligodendrocytes",
  "Oligodendrocyte Mature": "Oligodendrocytes",
  "Oligodendrocyte NF": "Oligodendrocytes",
  "Oligodendrocyte Precursor cells": "Oligodendrocytes",
  "Pericytes": "Vasculature",
  "Perivascular Macrophages": "Brain immune",
  "Pyramidal Cpne5": "Excitatory neurons",
  "Pyramidal Kcnip2": "Excitatory neurons",
  "Pyramidal L2-3 L5": "Excitatory neurons",
  "Pyramidal L2-3": "Excitatory neurons",
  "Pyramidal L3-4": "Excitatory neurons",
  "Pyramidal L5": "Excitatory neurons",
  "Pyramidal L6": "Excitatory neurons",
  "Vascular Smooth Muscle": "Vasculature",
  "pyramidal L4": "Excitatory neurons"
}


def get_neighborhoods(metadata):
    '''
    >>> cells = {
    ...   'O': { 'xy': [0,0], 'extra': 'field'},
    ...   'N': { 'xy': [0,1], 'extra': 'field'},
    ...   'E': { 'xy': [1,0], 'extra': 'field'},
    ...   'S': { 'xy': [0,-1], 'extra': 'field'},
    ...   'W': { 'xy': [-1,0], 'extra': 'field'}
    ... }
    >>> neighborhoods = get_neighborhoods(cells)
    >>> neighborhoods.keys()
    dict_keys(['O::E::N', 'O::N::W', 'O::S::E', 'O::W::S'])
    >>> neighborhoods['O::E::N']
    {'poly': [[0, 0], [1, 0], [0, 1]]}

    '''
    coords = {}
    for (k, v) in metadata.items():
        coords[k] = v['xy']
    triangles = DictDelaunay2d(coords).getTriangles()
    neighborhoods = {}
    for triangle in triangles:
        key = '::'.join(triangle)
        value = {
            'poly': [coords[point] for point in triangle]
        }
        neighborhoods[key] = value
    return neighborhoods


def get_genes(metadata):
    '''
    >>> metadata = {
    ...   'cell-1': {'genes': {'a': 1, 'b': 20}},
    ...   'cell-2': {'genes': {'a': 2, 'b': 10}}
    ... }
    >>> genes = get_genes(metadata)
    >>> genes['a']
    {'max': 2, 'cells': {'cell-1': 1, 'cell-2': 2}}
    >>> genes['b']
    {'max': 20, 'cells': {'cell-1': 20, 'cell-2': 10}}

    '''
    genes = defaultdict(lambda: {'max': 0, 'cells': {}})
    for cell_id, cell_data in metadata.items():
        for gene_id, expression_level in cell_data['genes'].items():
            gene_data = genes[gene_id]
            gene_data['cells'][cell_id] = expression_level
            if gene_data['max'] < expression_level:
                gene_data['max'] = expression_level
    return genes


def get_factors(metadata):
    '''
    >>> metadata = {
    ...   "Santa's Little Helper": {'factors':{'eng': 'dog', 'sci': 'canine'}},
    ...   "Snowball II": {'factors':{'eng': 'cat', 'sci': 'feline'}}
    ... }
    >>> factors = get_factors(metadata)
    >>> list(factors['eng'].keys())
    ['map', 'cells']
    >>> factors['eng']['map']
    ['dog', 'cat']
    >>> factors['eng']['cells']
    {"Santa's Little Helper": 0, 'Snowball II': 1}

    '''
    factors = defaultdict(lambda: {'map': [], 'cells': {}})
    for cell_id, cell_data in metadata.items():
        for factor_id, factor_value in cell_data['factors'].items():
            factor_data = factors[factor_id]
            if factor_value not in factor_data['map']:
                factor_data['map'].append(factor_value)
            factor_index = factor_data['map'].index(factor_value)
            factor_data['cells'][cell_id] = factor_index
    return factors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create JSON with cell metadata and, '
                    'optionally, segmentation.')
    parser.add_argument(
        '--loom', required=True,
        help='Loom file with cell metadata')
    parser.add_argument(
        '--pkl', type=argparse.FileType('rb'),
        help='Pickle file with cell segmentation data')
    parser.add_argument(
        '--transform_file', type=argparse.FileType('x'),
        help='Center the data at (0, 0), and save the transformation.')
    parser.add_argument(
        '--clusters_file', type=argparse.FileType('x'),
        help='Write the hierarchically clustered data to this file.')
    parser.add_argument(
        '--cells_file', type=argparse.FileType('x'),
        help='Write the cleaned cell data to this file.')
    parser.add_argument(
        '--genes_file', type=argparse.FileType('x'),
        help='Write a list of genes to this file.'),
    parser.add_argument(
        '--neighborhoods_file', type=argparse.FileType('x'),
        help='Write the cell neighborhoods to this file.')
    parser.add_argument(
        '--factors_file', type=argparse.FileType('x'),
        help='Write the cell factors to this file.')
    parser.add_argument(
        '--integers', action='store_true',
        help='Convert all numbers to integers.')
    args = parser.parse_args()

    metadata = LoomReader(args.loom).data()

    for cell in metadata.values():
        # "Clusters" in the raw data are called "subclusters"
        # in http://linnarssonlab.org/osmFISH/clusters/
        subcluster = cell.pop('cluster')
        cell['factors'] = {
            'subcluster': subcluster,
            'cluster': LOOKUP[subcluster]
        }

    if args.pkl:
        segmentation = pickle.load(args.pkl)
        for cell_id, poly in segmentation.items():
            if cell_id in metadata:
                simple_poly = octagon(poly)
                xy = mean_coord(simple_poly)
                metadata[cell_id]['poly'] = simple_poly
                metadata[cell_id]['xy'] = xy

    if args.transform_file:
        transform = get_transform(metadata)
        json.dump(transform, args.transform_file, indent=1)
        for cell in metadata.values():
            if 'xy' in cell:
                cell['xy'] = apply_transform(transform, cell['xy'])
            if 'poly' in cell:
                cell['poly'] = [
                    apply_transform(transform, xy) for xy in cell['poly']
                ]

    if args.integers:
        for cell in metadata.values():
            cell['xy'] = [
                # Raw data has way too many decimal points!
                int(z) for z in cell['xy']
            ]

    if args.cells_file:
        json.dump(metadata, args.cells_file, indent=1)

    if args.clusters_file:
        clusters = get_clusters(metadata)
        clusters_json = json.dumps(clusters)
        # Line-break after every element is too much, but this works:
        spaced_clusters_json = clusters_json.replace(
            '],',
            '],\n'
        )
        print(spaced_clusters_json, file=args.clusters_file)

    if args.genes_file:
        genes = get_genes(metadata)
        genes_json = json.dumps(genes)
        spaced_genes_json = genes_json.replace(
            '},',
            '},\n'
        )
        print(spaced_genes_json, file=args.genes_file)

    if args.factors_file:
        factors = get_factors(metadata)
        factors_json = json.dumps(factors)
        spaced_factors_json = factors_json.replace(
            '},',
            '},\n'
        )
        print(spaced_factors_json, file=args.factors_file)

    if args.neighborhoods_file:
        neighborhoods = get_neighborhoods(metadata)
        json.dump(neighborhoods, args.neighborhoods_file)
