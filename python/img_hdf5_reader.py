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
        >>> path = 'fake-files/input/linnarsson.imagery.hdf5'
        >>> reader = ImgHdf5Reader(path)
        >>> len(reader.keys())
        2
        >>> sorted(list(reader.keys()))
        ['nuclei', 'polyT']

        '''
        return self.data.keys()

    def __getitem__(self, key):
        return self.data[key]

    def sample(self, channel, step):
        '''
        >>> path = 'fake-files/input/linnarsson.imagery.hdf5'
        >>> reader = ImgHdf5Reader(path)
        >>> sample = reader.sample('polyT', 2)
        >>> sample.shape
        (25, 25)

        '''
        return self.data[channel][::step, ::step]

    def scale_sample(self, channel, step, max_allowed, clip):
        '''
        Assumes there are no negative values

        >>> path = 'fake-files/input/linnarsson.imagery.hdf5'
        >>> reader = ImgHdf5Reader(path)
        >>> sample = reader.scale_sample('polyT', 10, 255, 20)
        >>> sample.shape
        (5, 5)
        >>> for l in sample.tolist():
        ...   print(l)
        [0.0, 127.0, 254.0, 254.0, 254.0]
        [0.0, 127.0, 254.0, 254.0, 254.0]
        [0.0, 127.0, 254.0, 254.0, 254.0]
        [0.0, 127.0, 254.0, 254.0, 254.0]
        [0.0, 127.0, 254.0, 254.0, 254.0]

        '''
        sample = np.clip(self.sample(channel, step), 0, clip)
        # 255 displays as black... color table issue?
        return sample / clip * (max_allowed - 1)

    def to_png(self, channel, step, png_path, s3_target, clip, png_basename):
        MAX_ALLOWED = 256
        NP_TYPE = np.int8

        scaled_sample = self.scale_sample(
            channel=channel,
            step=step,
            max_allowed=MAX_ALLOWED,
            clip=clip
        ).astype(NP_TYPE)
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

        return {
            'x': 0,
            'y': 0,
            'width': hack.shape[0] * step,
            'height': hack.shape[1] * step,
            'href': 'https://s3.amazonaws.com/{}/{}'.format(
                s3_target, png_basename
            )
        }

    def to_png_json(self, channel_clips, step, json_file, s3_target):
        descriptions = {}
        for (channel, clip) in channel_clips:
            png_path = '{}.{}.png'.format(
                json_file.name.replace('.json', ''),
                channel
            )
            png_basename = basename(png_path)
            descriptions[channel] = self.to_png(
                channel=channel,
                clip=float(clip),
                step=step,
                png_path=png_path,
                s3_target=s3_target,
                png_basename=png_basename
            )
        json.dump(descriptions, json_file, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create PNG files and one JSON file with metadata')
    parser.add_argument(
        '--hdf5', required=True,
        help='HDF5 file with raster data')
    parser.add_argument(
        '--channel_clip_pairs', required=True, nargs='+',
        help='Colon-delimited pairs of channels and clip values')
    parser.add_argument(
        '--json_file', required=True, type=argparse.FileType('x'),
        help='JSON file which will include image dimensions and location')
    parser.add_argument(
        '--sample', required=True, type=int,
        help='Sample 1 pixel out of N')
    parser.add_argument(
        '--s3_target', required=True,
        help='S3 bucket and path')
    args = parser.parse_args()

    channel_clips = [pair.split(':') for pair in args.channel_clip_pairs]

    reader = ImgHdf5Reader(args.hdf5)
    reader.to_png_json(
        channel_clips=channel_clips,
        step=args.sample,
        json_file=args.json_file,
        s3_target=args.s3_target
    )
