#!/usr/bin/env python3

import argparse

from loom_reader import LoomReader
from segmentation_pickle_reader import SegPickleReader

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Create JSON with cell metadata and segmentation.')
    parser.add_argument('--pickle', required=True,
        help='Pickle file with cell segmentation data')
    parser.add_argument('--loom', required=True,
        help='Loom file with cell metadata')
    args = parser.parse_args()

    loom = LoomReader(args.loom)
    pickle = SegPickleReader(args.pickle)
