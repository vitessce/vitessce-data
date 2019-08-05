#!/usr/bin/env python3

from h5py import File
from apeer_ometiff_library import io, omexmlClass
import xml.etree.ElementTree as et
import datetime
import numpy as np
import png
import argparse
import json


class ImgHdf5Reader:
    def __init__(self, filename):
        self.data = File(filename, 'r')

    def keys(self):
        '''
        >>> path = 'fake-files/input/linnarsson/linnarsson.imagery.hdf5'
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
        >>> path = 'fake-files/input/linnarsson/linnarsson.imagery.hdf5'
        >>> reader = ImgHdf5Reader(path)
        >>> sampled = reader.sample_image('polyT', 2)
        >>> sampled.shape
        (25, 25)

        '''
        return self.data[channel][::sample, ::sample]

    def scale_sample(self, channel, sample, max_allowed, clip):
        '''
        Assumes there are no negative values

        >>> path = 'fake-files/input/linnarsson/linnarsson.imagery.hdf5'
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
                    'https://s3.amazonaws.com/{}/linnarsson/'.format(s3_target)
                + 'linnarsson.tiles/linnarsson.images.{}/'.format(channel)
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

    def get_omexml(self, pixel_array, channels, name, pixel_type):
        omexml = omexmlClass.OMEXML()
        image = omexml.image()
        image.Name = name
        image.AcquisitionDate = datetime.datetime.now().isoformat()

        pixels = image.Pixels
        pixels.SizeX = pixel_array.shape[4]
        pixels.SizeY = pixel_array.shape[3]
        pixels.SizeC = pixel_array.shape[2]
        pixels.SizeZ = pixel_array.shape[1]
        pixels.SizeT = pixel_array.shape[0]
        pixels.PixelType = pixel_type

        channel_count = len(channels)
        pixels.channel_count = channel_count
        for i in range(channel_count):
            pixels.Channel(i).ID = "Channel:0:{}".format(i)
            pixels.Channel(i).Name = channels[i]

        root = et.XML(str(omexml))
        ome = "{http://www.openmicroscopy.org/Schemas/OME/2016-06}"
        pixels_elem = root.find("{}Image/{}Pixels".format(ome, ome))

        # Repeat for-loop because XML parsing must have channel adjustments
        for i in range(channel_count):
            et.SubElement(
                pixels_elem,
                '{}TiffData'.format(ome),
                FirstC=str(i),
                FirstT="0",
                FirstZ="0",
                IFD="0",
                PlaneCount="1"
            )

        return omexmlClass.OMEXML(et.tostring(root))

    def to_ometiff(self, channel_clips, sample, json_file):
        channel_data = {}
        channels = []
        images = []
        ometif_path = '{}.ome.tif'.format(
            json_file.name.replace('.json', '')
        )
        s3_target = open('s3_target.txt').read().strip()
        for (channel, clip) in channel_clips:
            channel_data[channel] = {
                'sample': sample,
                'tileSource':
                    'https://s3.amazonaws.com/{}/linnarsson/'.format(s3_target)
                + 'linnarsson.tiles/linnarsson.images.{}/'.format(channel)
                + '{}.dzi'.format(channel)
            }

            channels.append(channel)
            array = self.scale_sample(
                channel=channel,
                sample=sample,
                max_allowed=256,
                clip=float(clip)
            ).astype(np.uint8)

            images.append(array)

        json.dump(channel_data, json_file, indent=2)

        image = np.transpose(np.dstack(tuple(images)))
        image = np.expand_dims(image, axis=0)
        image = np.expand_dims(image, axis=0)

        channels = [tup[0] for tup in channel_clips]
        omexml = self.get_omexml(
            pixel_array=image,
            channels=channels,
            name='linnarsson',
            pixel_type='uint8'
        )

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

    # Using instead of PNG functions
    reader.to_ometiff(
        channel_clips=channel_clips,
        sample=args.sample,
        json_file=args.json_file
    )
