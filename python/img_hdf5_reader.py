#!/usr/bin/env python3

from h5py import File
from apeer_ometiff_library import io, omexmlClass
import dask.array as da
import dask
from numcodecs import Zlib
import zarr
import xml.etree.ElementTree as et
import datetime
import numpy as np
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

    def sample_image(self, channel, sample, use_dask=False):
        '''
        >>> path = 'fake-files/input/linnarsson/linnarsson.imagery.hdf5'
        >>> reader = ImgHdf5Reader(path)
        >>> sampled = reader.sample_image('polyT', 2)
        >>> sampled.shape
        (25, 25)

        '''
        data = (
            self.data[channel]
            if not use_dask
            else da.array(self.data[channel])
        )
        return data[::sample, ::sample]

    def scale_sample(self, channel, sample, max_allowed, clip, use_dask=False):
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
        sampled = self.sample_image(channel, sample, use_dask).clip(0, clip)
        # 255 displays as black... color table issue?
        return sampled / clip * (max_allowed - 1)

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

    def to_zarr(self, channels, sample, json_file, zarr_url):
        # zarr default BLOSC not supported in browser
        COMPRESSOR = Zlib(level=1)
        TILE_SIZE = 512
        PYRAMID_GROUP = "pyramid"

        data_shape, data_dtype = self._get_shape_and_dtype(channels)

        # Create mutable store
        zarr_path = json_file.name.replace('.json', '.zarr')
        store = zarr.DirectoryStore(zarr_path)
        root = zarr.group(store=store, overwrite=True)
        pyramid_root = root.create_group(PYRAMID_GROUP, overwrite=True)

        # Determine number of levels for pyramid
        s_height, s_width = [dim // sample for dim in data_shape]
        if s_height < TILE_SIZE and s_width < TILE_SIZE:
            max_level = 0
        else:
            # create all levels up to 512 x 512
            max_level = (
                int(np.ceil(np.log2(np.maximum(s_height, s_width)))) - 9
            )
            max_level -= 1  # zero indexed

        channel_data = {}
        images = []
        for idx, channel in enumerate(channels):

            array = self.sample_image(
                channel=channel,
                sample=sample,
                use_dask=True,
            ).astype(data_dtype)

            min_val, max_val = dask.compute(array.min(), array.max())

            channel_data[channel] = {
                "sample": sample,
                "tileSource": f"{zarr_url}/{PYRAMID_GROUP}/",
                "minZoom": -max_level,  # deck.gl is flipped
                "range": [int(min_val), int(max_val)]
            }

            images.append(array.T)

        # Stack arrays using dask and rechunk to tile sizes (i.e. (2, 512, 512)
        chunks = (len(channels), TILE_SIZE, TILE_SIZE)
        da.array(images).rechunk(chunks).to_zarr(
            zarr_path,
            component=f"{PYRAMID_GROUP}/00",
            compressor=COMPRESSOR
        )
        json.dump(channel_data, json_file, indent=2)

        # Add metadata
        z = pyramid_root.get("00")
        z.attrs["channels"] = channels

    def _get_shape_and_dtype(self, channels):
        shapes, dtypes = zip(
            *[(self.data[c].shape, self.data[c].dtype) for c in channels]
        )
        # Compare dimension sizes to make sure all same size
        shape = []
        for shared_dimension in zip(*shapes):
            first_el = shared_dimension[0]
            all_same = all(dim == first_el for dim in shared_dimension)
            if not all_same:
                raise ValueError(
                    f"Data stored in {channels} are not the same shape."
                )
            shape.append(first_el)
        # Ensure same dtype.
        first_dtype = dtypes[0]
        all_same = all(dtype == first_dtype for dtype in dtypes)
        if not all_same:
            raise ValueError(
                f"Dtypes are not the same for {channels}: {dtypes}"
            )

        return shape, first_dtype


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create PNG files and one JSON file with metadata')
    parser.add_argument(
        '--hdf5', required=True,
        help='HDF5 file with raster data')
    parser.add_argument(
        '--json_file', required=True, type=argparse.FileType('x'),
        help='JSON file which will include image dimensions and location')
    parser.add_argument(
        '--channels', required=True,
        help='List of channels to include in zarr image.')
    parser.add_argument(
        '--zarr_url', required=True,
        help='Output URL to zarr store.')
    parser.add_argument(
        '--sample', default=1, type=int,
        help='Sample 1 pixel out of N')
    args = parser.parse_args()

    reader = ImgHdf5Reader(args.hdf5)

    channels = [c for c in args.channels.split(',')]
    reader.to_zarr(
        channels=channels,
        sample=args.sample,
        json_file=args.json_file,
        zarr_url=args.zarr_url,
    )
