#!/usr/bin/env python3

from h5py import File
from numcodecs import Zlib
import zarr

import argparse
import json
import urllib
from pathlib import Path

from tile_zarr_base import tile_zarr

DEFAULT_COMPRESSOR = Zlib(level=1)
DEFAULT_TILE_SIZE = 512


def create_dimensions(channel_names):
    return [
        {"field": "channel", "type": "nominal", "values": channel_names},
        {"field": "y", "type": "quantitative", "values": None},
        {"field": "x", "type": "quantitative", "values": None},
    ]


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
        return self.data[channel][::sample, ::sample]

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
        sampled = self.sample_image(channel, sample).clip(0, clip)
        # 255 displays as black... color table issue?
        return sampled / clip * (max_allowed - 1)

    def to_zarr(
        self,
        output_path,
        channels,
        sample,
        tile_size,
        is_pyramid_base=False,
        compressor=DEFAULT_COMPRESSOR
    ):
        data_shape, data_dtype = self._get_shape_and_dtype(channels)
        out_shape = (len(channels), *data_shape[::-1])
        arr_kwargs = {
            "chunks": (1, tile_size, tile_size),
            "compressor": compressor,
            "shape": out_shape,
            "dtype": data_dtype,
        }

        if is_pyramid_base:
            group = zarr.open(str(output_path))
            z = group.create("0", **arr_kwargs)
        else:
            z = zarr.open(str(output_path), **arr_kwargs)

        for idx, channel in enumerate(channels):

            img = self.sample_image(
                channel=channel,
                sample=sample,
            ).astype(data_dtype)

            z[idx] = img.T

            z.attrs['dimensions'] = create_dimensions(channels)

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


def write_raster_json(
    json_file,
    url,
    name,
    channel_names,
    is_pyramid=False,
    transform={"translate": {"y": 0, "x": 0}, "scale": 1}
):
    raster_json = {
        "schema_version": "0.0.1",
        "images": [
            {
                "name": name,
                "url": url,
                "type": "zarr",
                "metadata": {
                    "dimensions": create_dimensions(channel_names),
                    "is_pyramid": is_pyramid,
                    "transform": transform,
                },
            }
        ],
    }
    json.dump(raster_json, json_file, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create PNG files and one JSON file with metadata')
    parser.add_argument(
        '--hdf5', required=True,
        help='HDF5 file with raster data')
    parser.add_argument(
        '--zarr_file', required=True,
        help='Directory to write zarr output to.')
    parser.add_argument(
        '--channels', required=True,
        help='List of channels to include in zarr image.')
    parser.add_argument(
        '--dest_url', required=True,
        help='Output URL to zarr store.')
    parser.add_argument(
        '--sample', default=1, type=int,
        help='Sample 1 pixel out of N')
    parser.add_argument(
        '--tile_size', default=DEFAULT_TILE_SIZE,
        type=int, help='Size of zarr image tiles.'
    )
    parser.add_argument(
        '--raster_json', required=True, type=argparse.FileType('x'),
        help='JSON file which will include image dimensions and location')
    parser.add_argument(
        "--raster_name", required=True, help="Image name for metadata.",
    )
    parser.add_argument(
        "--as_pyramid",
        action="store_false",
        help="Whether to generate image pyramid."
    )
    args = parser.parse_args()

    reader = ImgHdf5Reader(args.hdf5)

    zarr_path = Path(args.zarr_file)
    channels = [c for c in args.channels.split(',')]
    is_pyramid = args.as_pyramid
    full_dest_url = urllib.parse.urljoin(
        args.dest_url, zarr_path.name
    )

    reader.to_zarr(
        output_path=zarr_path,
        channels=channels,
        sample=args.sample,
        tile_size=args.tile_size,
        is_pyramid_base=is_pyramid,
    )

    if is_pyramid:
        tile_zarr(str(zarr_path / "0"))
        # Consolidate metadata into single .zmetadata for pyramid
        # https://zarr.readthedocs.io/en/stable/tutorial.html#consolidating-metadata
        z_group = zarr.open(str(zarr_path))
        zarr.consolidate_metadata(z_group.store)

    write_raster_json(
        json_file=args.raster_json,
        url=full_dest_url,
        name=args.raster_name,
        channel_names=channels,
        is_pyramid=is_pyramid,
    )
