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
    ...     },
    ...     "cell_2": {
    ...         "locations": [1589.47, -669.51],
    ...         "factors": {
    ...             "pleiden_clus": [3],
    ...             "kmeans": [8]
    ...         },
    ...         "mappings": {
    ...             "tsne": [-10.7971, 4.0234],
    ...             "umap": [-8.0222, 16.2033]
    ...         }
    ...     }
    ... }
    >>> cells = cells_json(data)
    >>> cells.keys()
    dict_keys(['cell_1', 'cell_2'])
    >>> cells['cell_1'].keys()
    dict_keys(['mappings', 'genes', 'xy', 'factors', 'poly'])
    >>> cells['cell_1']['mappings'].keys()
    dict_keys(['t-SNE', 'UMAP'])
    >>> cells['cell_2']['factors'].keys()
    dict_keys(['pleiden_clus', 'kmeans'])

    '''
    cell_dict = {}
    for cell in data.keys():

        mappings_dict = {
            't-SNE': data[cell]['mappings']['tsne'],
            'UMAP': data[cell]['mappings']['umap']
            }

        genes_dict = {}

        factors_dict = {
            'pleiden_clus': "Cluster " +
            str(data[cell]['factors']['pleiden_clus'][0]),
            'kmeans': "Cluster " + str(data[cell]['factors']['kmeans'][0])
            }

        poly_dict = {}

        cell_dict[cell] = {
            'mappings': mappings_dict,
            'genes': genes_dict,
            'xy': data[cell]['locations'],
            'factors': factors_dict,
            'poly': poly_dict
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
    ...     },
    ...     "cell_2": {
    ...         "locations": [1589.47, -669.51],
    ...         "factors": {
    ...             "pleiden_clus": [3],
    ...             "kmeans": [8]
    ...         },
    ...         "mappings": {
    ...             "tsne": [-10.7971, 4.0234],
    ...             "umap": [-8.0222, 16.2033]
    ...         }
    ...     }
    ... }
    >>> factors = factors_json(data)
    >>> factors.keys()
    dict_keys(['pleiden_clus', 'kmeans'])
    >>> factors['kmeans'].keys()
    dict_keys(['map', 'cells'])
    >>> factors['kmeans'].values()
    dict_values([['Cluster 8'], {'cell_1': 0, 'cell_2': 0}])
    >>> factors['pleiden_clus']['cells'].keys()
    dict_keys(['cell_1', 'cell_2'])

    '''
    pleiden_clusters = []
    kmeans_clusters = []
    for cell in data.keys():
        pleiden_clusters.append(data[cell]['factors']['pleiden_clus'][0])
        kmeans_clusters.append(data[cell]['factors']['kmeans'][0])

    pleiden_clusters = list(dict.fromkeys(pleiden_clusters))
    kmeans_clusters = list(dict.fromkeys(kmeans_clusters))

    pleiden_cells = {}
    kmeans_cells = {}

    for cell in data.keys():
        pleiden_cells[cell] = pleiden_clusters.index(
            data[cell]['factors']['pleiden_clus'][0]
        )

        kmeans_cells[cell] = kmeans_clusters.index(
            data[cell]['factors']['kmeans'][0]
        )

    factors_dict = {
        'pleiden_clus': {
            'map': list(map(lambda c: "Cluster " + str(c), pleiden_clusters)),
            'cells': pleiden_cells
        },
        'kmeans': {
            'map': list(map(lambda c: "Cluster " + str(c), kmeans_clusters)),
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
