#!/usr/bin/env python3

from tifffile import TiffFile
from apeer_ometiff_library.omexmlClass import OMEXML
from numcodecs import Zlib
import zarr
import numpy as np

import argparse
from pathlib import Path
import json
import urllib

from tile_zarr_base import tile_zarr

DEFAULT_COMPRESSOR = Zlib(level=1)
DEFAULT_TILE_SIZE = 512


def should_be_pyramid(shape):
    # Generate image pyramid if any dim >= 4096
    return bool((np.log2(shape) >= 12).any())


class OmeTiffReader:
    def __init__(self, img_path):
        self.tiff = TiffFile(str(img_path))
        self.metadata = OMEXML(self.tiff.ome_metadata)
        self.img_path = img_path
        self.base_series = self.tiff.series[0]
        self.dim_order = self.base_series.axes
        self.shape = tuple(dim for dim in self.base_series.shape if dim > 1)
        self.dtype = self.base_series.dtype

    def get_raster_dimensions(self):
        image = self.metadata.image()
        pixels = image.Pixels
        channel_names = [
            str(pixels.Channel(i).Name) for i in range(pixels.channel_count)
        ]
        return [
            {"field": "channel", "type": "nominal", "values": channel_names},
            {"field": "y", "type": "quantitative", "values": None},
            {"field": "x", "type": "quantitative", "values": None},
        ]

    def to_zarr(
        self,
        output_path,
        tile_size,
        is_pyramid_base=False,
        compressor=DEFAULT_COMPRESSOR,
    ):
        arr_kwargs = {
            "chunks": (1, tile_size, tile_size),
            "compressor": compressor,
            "shape": self.shape,
            "dtype": self.dtype,
        }

        if is_pyramid_base:
            group = zarr.open(str(output_path))
            z = group.create("0", **arr_kwargs)
        else:
            z = zarr.open(str(output_path), **arr_kwargs)

        for idx, page in enumerate(self.base_series.pages):
            z[idx] = page.asarray()


def write_raster_json(
    json_file, server_url, raster_name, dimensions, is_pyramid, transform=None
):
    if not transform:
        transform = {"translate": {"y": 0, "x": 0}, "scale": 1}
    raster_json = {
        "version": "0.0.1",
        "images": [
            {
                "name": raster_name,
                "url": server_url,
                "type": "zarr",
                "metadata": {
                    "dimensions": dimensions,
                    "is_pyramid": is_pyramid,
                    "transform": transform,
                },
            }
        ],
    }
    json.dump(raster_json, json_file, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert OME-TIFF image to full resolution zarr"
    )
    parser.add_argument(
        "--input_tiff", required=True, help="Path to input OME-TIFF"
    )
    parser.add_argument(
        "--output_zarr", required=True, help="Path or zarr output"
    )
    parser.add_argument(
        "--raster_json",
        type=argparse.FileType("x"),
        required=True,
        help="Write the metadata about the IMS zarr store on S3.",
    )
    parser.add_argument(
        "--raster_name", required=True, help="Image name for metadata.",
    )
    parser.add_argument(
        "--server_url",
        required=True,
        help="Destination for zarr output in cloud.",
    )
    parser.add_argument(
        "--tile_size", help="Tile size for zarr images.", default=512, type=int
    )

    args = parser.parse_args()

    img_path = Path(args.input_tiff)
    zarr_path = Path(args.output_zarr)
    destination_url = urllib.parse.urljoin(args.server_url, zarr_path.name)

    reader = OmeTiffReader(img_path)
    is_pyramid_base = should_be_pyramid(reader.shape)
    reader.to_zarr(zarr_path, args.tile_size, is_pyramid_base)
    if is_pyramid_base:
        tile_zarr(str(zarr_path / "0"))
    write_raster_json(
        args.raster_json,
        destination_url,
        args.raster_name,
        reader.get_raster_dimensions(),
        is_pyramid_base,
    )
