#!/usr/bin/env python3

from h5py import File
import dask.array as da
import dask
from numcodecs import Zlib
import zarr
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

    def to_zarr(self, channels, sample, json_file, zarr_file, tiles_url):
        # zarr default BLOSC not supported in browser
        COMPRESSOR = Zlib(level=1)
        TILE_SIZE = 512
        PYRAMID_GROUP = "pyramid"

        data_shape, data_dtype = self._get_shape_and_dtype(channels)

        # Create mutable store
        store = zarr.DirectoryStore(zarr_file)
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
                "tileSource": f"{tiles_url}/{PYRAMID_GROUP}/",
                "minZoom": -max_level,  # deck.gl is flipped
                "domain": [int(min_val), int(max_val)]
            }

            images.append(array.T)

        # Stack arrays using dask and rechunk to tile sizes (i.e. (2, 512, 512)
        chunks = (len(channels), TILE_SIZE, TILE_SIZE)
        da.array(images).rechunk(chunks).to_zarr(
            zarr_file,
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
        '--zarr_file', required=True,
        help='Directory to write zarr output to.')
    parser.add_argument(
        '--channels', required=True,
        help='List of channels to include in zarr image.')
    parser.add_argument(
        '--tiles_url', required=True,
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
        tiles_url=args.tiles_url,
        zarr_file=args.zarr_file,
    )
