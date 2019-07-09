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
    for cell_id in data.keys():
        factors = data[cell_id]['factors']

        mappings_dict = {
            't-SNE': data[cell_id]['mappings']['tsne'],
            'UMAP': data[cell_id]['mappings']['umap']
        }
        factors_dict = {
            'pleiden_clus': 'Cluster {}'.format(factors['pleiden_clus'][0]),
            'kmeans': 'Cluster {}'.format(factors['kmeans'][0])
        }
        cell_dict[cell_id] = {
            'mappings': mappings_dict,
            'genes': {},
            'xy': data[cell_id]['locations'],
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
    def get_factor(cell, factor_name):
        return cell['factors'][factor_name][0]
    pleiden_clusters_set = {
        get_factor(cell, 'pleiden_clus') for cell in data.values()
    }
    kmeans_clusters_set = {
        get_factor(cell, 'kmeans') for cell in data.values()
    }

    pleiden_clusters_list = list(pleiden_clusters_set)
    kmeans_clusters_list = list(kmeans_clusters_set)

    pleiden_cells = {}
    kmeans_cells = {}

    for cell_id in data:
        factors = data[cell_id]['factors']
        pleiden_cells[cell_id] = pleiden_clusters_list.index(
            factors['pleiden_clus'][0]
        )
        kmeans_cells[cell_id] = kmeans_clusters_list.index(
            factors['kmeans'][0]
        )

    factors_dict = {
        'pleiden_clus': {
            'map': ['Cluster {}'.format(c) for c in pleiden_clusters_list],
            'cells': pleiden_cells
        },
        'kmeans': {
            'map': ['Cluster {}'.format(c) for c in kmeans_clusters_list],
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
        '--cells_file', required=True, type=argparse.FileType('x'),
        help='Write the cell data to this file.')
    parser.add_argument(
        '--factors_file', required=True, type=argparse.FileType('x'),
        help='Write the cell factors to this file.')
    args = parser.parse_args()

    with open(args.json_file) as json_file:
        data = json.load(json_file)

    json.dump(cells_json(data), args.cells_file, indent=1)

    json.dump(factors_json(data), args.factors_file, indent=1)
