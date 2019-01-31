#!/usr/bin/env python3

from sys import argv
import json

from h5py import File


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
    if len(argv) != 2:
        print('Requires single HDF5 file')
        exit(1)
    reader = CountsHdf5Reader(argv[1])
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
            print(json.dumps(pair), end='')
        print(']', end='')
    print('}', end='')
