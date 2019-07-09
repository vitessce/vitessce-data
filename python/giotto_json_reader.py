#!/usr/bin/env python3

import json
import argparse


def cells_json(data):
    '''
    >>> data = {
    ...     "cell_1": {
    ...         "locations": [1632.02, -1305.7],
    ...         "factors": {
    ...             "pleiden_clus": [3],
    ...             "kmeans": [8]
    ...         },
    ...         "mappings": {
    ...             "tsne": [-11.0776, 6.0311],
    ...             "umap": [-6.858, 15.7691]
    ...         }
    ...     }
    ... }
    >>> cells = cells_json(data)
    >>> cells.keys()
    dict_keys(['cell_1'])
    >>> cells['cell_1'].keys()
    dict_keys(['mappings', 'genes', 'xy', 'factors', 'poly'])

    '''
    cell_dict = {}
    for cell in data.keys():

        mappings_dict = {
            't-SNE': data[cell]['mappings']['tsne'],
            'UMAP': data[cell]['mappings']['umap']
            }

        genes_dict = {}

        factors_dict = {
            'pleiden_clus': 'Cluster {}'.format(
                data[cell]['factors']['pleiden_clus'][0]
            ),
            'kmeans': 'Cluster {}'.format(data[cell]['factors']['kmeans'][0])
            }

        cell_dict[cell] = {
            'mappings': mappings_dict,
            'genes': genes_dict,
            'xy': data[cell]['locations'],
            'factors': factors_dict,
            'poly': []
        }

    return cell_dict


def factors_json(data):
    '''
    >>> data = {
    ...     "cell_1": {
    ...         "locations": [1632.02, -1305.7],
    ...         "factors": {
    ...             "pleiden_clus": [3],
    ...             "kmeans": [8]
    ...         },
    ...         "mappings": {
    ...             "tsne": [-11.0776, 6.0311],
    ...             "umap": [-6.858, 15.7691]
    ...         }
    ...     }
    ... }
    >>> factors = factors_json(data)
    >>> factors.keys()
    dict_keys(['pleiden_clus', 'kmeans'])
    >>> factors['kmeans'].keys()
    dict_keys(['map', 'cells'])

    '''
    pleiden_clusters = set()
    kmeans_clusters = set()
    for cell in data:
        factors = data[cell]['factors']
        pleiden_clusters.add(factors['pleiden_clus'][0])
        kmeans_clusters.add(factors['kmeans'][0])

    pleiden_clusters = list(pleiden_clusters)
    kmeans_clusters = list(kmeans_clusters)

    pleiden_cells = {}
    kmeans_cells = {}

    for cell_id in data:
        factors = data[cell_id]['factors']
        pleiden_cells[cell_id] = pleiden_clusters.index(
            factors['pleiden_clus'][0]
            )

        kmeans_cells[cell_id] = kmeans_clusters.index(factors['kmeans'][0])

    factors_dict = {
        'pleiden_clus': {
            'map': ['Cluster {}'.format(c) for c in pleiden_clusters],
            'cells': pleiden_cells
        },
        'kmeans': {
            'map': ['Cluster {}'.format(c) for c in kmeans_clusters],
            'cells': kmeans_cells
        }
    }

    return factors_dict


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create JSON with cell metadata from '
        'Giotto-produced JSON.')
    parser.add_argument(
        '--json_file', required=True,
        help='JSON file produced by Giotto object.')
    parser.add_argument(
        '--cells_file', type=argparse.FileType('x'),
        help='Write the cell data to this file.')
    parser.add_argument(
        '--factors_file', type=argparse.FileType('x'),
        help='Write the cell factors to this file.')
    args = parser.parse_args()

    with open(args.json_file) as json_file:
        data = json.load(json_file)

    if args.cells_file:
        json.dump(cells_json(data), args.cells_file, indent=1)

    if args.factors_file:
        json.dump(factors_json(data), args.factors_file, indent=1)
