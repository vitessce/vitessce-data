#!/usr/bin/env python3

from h5py import File
from apeer_ometiff_library import io, omexmlClass
import datetime
import uuid
import numpy as np
import png
import argparse
import json


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

    def sample_image(self, channel, sample):
        '''
        >>> path = 'fake-files/input/linnarsson.imagery.hdf5'
        >>> reader = ImgHdf5Reader(path)
        >>> sampled = reader.sample_image('polyT', 2)
        >>> sampled.shape
        (25, 25)

        '''
        return self.data[channel][::sample, ::sample]

    def scale_sample(self, channel, sample, max_allowed, clip):
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
        sampled = np.clip(self.sample_image(channel, sample), 0, clip)
        # 255 displays as black... color table issue?
        return sampled / clip * (max_allowed - 1)

    def to_png(self, channel, sample, png_path, clip):
        MAX_ALLOWED = 256
        NP_TYPE = np.int8

        scaled_sample = self.scale_sample(
            channel=channel,
            sample=sample,
            max_allowed=MAX_ALLOWED,
            clip=clip
        ).astype(NP_TYPE)
        scaled_sample_transposed = np.transpose(scaled_sample)

        # Bug with PNG generation from transposed numpy arrays:
        # https://github.com/drj11/pypng/issues/91
        # Work-around is to dump and reload.
        hack = np.array(scaled_sample_transposed.tolist()).astype(NP_TYPE)
        png.from_array(hack, mode='L').save(png_path)

    def to_pngs(self, channel_clips, sample, json_file):
        channels = {}
        s3_target = open('s3_target.txt').read().strip()
        for (channel, clip) in channel_clips:
            channels[channel] = {
                'sample': sample,
                # TODO: Pass in portions of this path as parameters
                'tileSource':
                    'https://s3.amazonaws.com/'
                + '{}/linnarsson.tiles/linnarsson.images.{}/'.format(
                    s3_target, channel)
                + 'info.json'
            }
            png_path = '{}.{}.png'.format(
                json_file.name.replace('.json', ''),
                channel
            )
            self.to_png(
                channel=channel,
                clip=float(clip),
                sample=sample,
                png_path=png_path,
            )
        json.dump(channels, json_file, indent=2)
        # This JSON file is not used right now:
        # really just a list of the files processed.

    def get_omexml(self, image, channels, name, pixel_type):
        print(image.shape)
        omexml = omexmlClass.OMEXML()
        omexml.image().ID = str(uuid.uuid4())
        omexml.image().Name = name
        omexml.image().AcquisitionDate = datetime.datetime.now().isoformat()
        omexml.image().Pixels.SizeX = image.shape[3]
        omexml.image().Pixels.SizeY = image.shape[2]
        omexml.image().Pixels.SizeC = image.shape[1]
        omexml.image().Pixels.PixelType = pixel_type
        channel_count = len(channels)
        omexml.image().Pixels.channel_count = channel_count
        for i in range(0, channel_count):
            omexml.image().Pixels.Channel(i).Name = channels[i]

        return omexml

    def to_ometiff(self, channel_clips, sample, json_file):
        channels = []
        images = []
        ometif_path = '{}.ome.tif'.format(
            json_file.name.replace('.json', '')
        )
        for (channel, clip) in channel_clips:
            channels.append(channel)
            array = self.scale_sample(
                channel=channel,
                sample=1,
                max_allowed=256,
                clip=float(clip)
            ).astype(np.uint8)

            images.append(array)

        image = np.transpose(np.dstack(tuple(images)))
        image = np.expand_dims(image, axis=0)

        channels = [tup[0] for tup in channel_clips]
        omexml = str(self.get_omexml(image, channels, 'linnarsson', 'uint8'))

        print(omexml)

        io.write_ometiff(ometif_path, image, str(omexml))


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
        '--sample', default=1, type=int,
        help='Sample 1 pixel out of N')
    args = parser.parse_args()

    channel_clips = [pair.split(':') for pair in args.channel_clip_pairs]

    reader = ImgHdf5Reader(args.hdf5)

    reader.to_pngs(
        channel_clips=channel_clips,
        sample=args.sample,
        json_file=args.json_file
    )

    reader.to_ometiff(
        channel_clips=channel_clips,
        sample=args.sample,
        json_file=args.json_file
    )
