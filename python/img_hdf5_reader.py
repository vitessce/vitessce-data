#!/usr/bin/env python3

from h5py import File
import numpy as np
import png
import argparse
import json
from os.path import basename


class ImgHdf5Reader:
    def __init__(self, filename):
        self.data = File(filename, 'r')

    def keys(self):
        '''
        # >>> path = 'fixtures/Nuclei_polyT.int16.sf.hdf5'
        # >>> reader = ImgHdf5Reader(path)
        # >>> len(reader.keys())
        # 2
        # >>> sorted(list(reader.keys()))
        # ['nuclei', 'polyT']

        '''
        return self.data.keys()

    def __getitem__(self, key):
        return self.data[key]

    def sample(self, key, step):
        '''
        # >>> path = 'fixtures/Nuclei_polyT.int16.sf.hdf5'
        # >>> reader = ImgHdf5Reader(path)
        # >>> sample = reader.sample('polyT', 100)
        # >>> sample.shape
        # (318, 517)

        '''
        return self.data[key][::step, ::step]

    def scale_sample(self, key, step, max_allowed):
        '''
        Assumes there are no negative values

        # >>> path = 'fixtures/Nuclei_polyT.int16.sf.hdf5'
        # >>> reader = ImgHdf5Reader(path)
        # >>> reader.scale_sample('polyT', 100, 255).shape
        # (318, 517)

        '''
        sample = self.sample(key, step)
        max_found = np.max(sample)

        return sample / max_found * max_allowed

    def to_png_json(self, key, step, png_path, json_path, s3_target):
        MAX_ALLOWED = 256
        NP_TYPE = np.int8

        scaled_sample = self.scale_sample(key, step, MAX_ALLOWED)\
            .astype(NP_TYPE)
        scaled_sample_transposed = np.transpose(scaled_sample)

        # Bug with PNG generation from transposed numpy arrays:
        # https://github.com/drj11/pypng/issues/91
        # Work-around is to dump and reload.
        hack = np.array(scaled_sample_transposed.tolist()).astype(NP_TYPE)

        image = png.from_array(hack, mode='L')
        # TODO: Would like "L;4" but get error message.
        # TODO: Online PNG compression tools reduce size by 50%...
        #       Check Python PNG encoding options.
        image.save(png_path)

        with open(args.json_out, 'w') as f:
            base = basename(png_path)
            f.write(json.dumps({
                'href': 'https://s3.amazonaws.com/{}/{}'.format(
                    s3_target, base
                ),
                'height': hack.shape[0],
                'width': hack.shape[1],
            }))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create PNG file and JSON file with metadata')
    parser.add_argument(
        '--hdf5', required=True,
        help='HDF5 file with raster data')
    parser.add_argument(
        '--channel', required=True,
        help='Channel to generate image for')
    parser.add_argument(
        '--json_out', required=True,
        help='JSON file will include image dimensions and location')
    parser.add_argument(
        '--png_out', required=True,
        help='Raster as a PNG')
    parser.add_argument(
        '--sample', required=True, type=int,
        help='Sample 1 pixel out of N')
    parser.add_argument(
        '--s3_target', required=True,
        help='S3 bucket and path')
    args = parser.parse_args()

    reader = ImgHdf5Reader(args.hdf5)
    reader.to_png_json(
        key=args.channel,
        step=args.sample,
        png_path=args.png_out,
        json_path=args.json_out,
        s3_target=args.s3_target
    )
