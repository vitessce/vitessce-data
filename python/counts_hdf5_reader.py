#!/usr/bin/env python3

import argparse
import json

from h5py import File

from transform import apply_transform


class CountsHdf5Reader:
    def __init__(self, filename):
        self.data = File(filename, 'r')

    def keys(self):
        '''
        # >>> path = 'fake-files/input/linnarsson.molecules.hdf5'
        # >>> reader = CountsHdf5Reader(path)
        # >>> len(reader.keys())
        # 39
        # >>> sorted(list(reader.keys()))[:2]
        # ['Acta2_Hybridization5', 'Aldoc_Hybridization1']

        '''
        return self.data.keys()

    def __getitem__(self, key):
        '''
        # >>> path = 'fake-files/input/linnarsson.molecules.hdf5'
        # >>> reader = CountsHdf5Reader(path)
        # >>> pairs = list(reader['Acta2_Hybridization5'])
        # >>> len(pairs)
        # 13052
        # >>> pairs[0]
        # [18215.0, 20052.0]

        '''
        return (list(pair) for pair in self.data[key])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create JSON with molecule locations')
    parser.add_argument(
        '--hdf5', required=True,
        help='HDF5 file with molecule locations')
    parser.add_argument(
        '--transform',
        help='Transform the coordinates')
    args = parser.parse_args()

    transform = {

    }
    if args.transform:
        with open(args.transform) as f:
            transform = json.loads(f.read())
    else:
        transform = {
            'x_shift': 0,
            'y_shift': 0,
            'x_scale': 1,
            'y_scale': 1
        }

    reader = CountsHdf5Reader(args.hdf5)
    # Doing the serialization by hand so we get immediate output,
    # and don't need an extra intermediate object
    print('{')
    first_key = True
    for key in reader.keys():
        if first_key:
            first_key = False
        else:
            print(',')
        print(json.dumps(key) + ':[')
        first_pair = True
        for pair in reader[key]:
            if first_pair:
                first_pair = False
            else:
                print(',')
            transformed = apply_transform(transform, pair)
            print(json.dumps(transformed), end='')
        print(']', end='')
    print('}', end='')
