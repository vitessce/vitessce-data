#!/usr/bin/env python3

import numpy as np
import pandas as pd
from pyimzml.ImzMLParser import ImzMLParser
from numcodecs import Zlib
import zarr

import argparse
import json
from collections import namedtuple
from pathlib import Path

CoordExtent = namedtuple("CoordExtent", "x_min y_min x_max y_max")

# Pyimzml dtype specification
DTYPE_DICT = {
    'f': np.float32,
    'd': np.float64,
    'i': np.int32,
    'l': np.int64,
}


class IMSDataset:
    """Converts IMS data stored as imzML into columnar or ndarray formats

    :param imzml_file: path to `.imzML` file.
    :param ibd_file: path to associated `.ibd` file.
    :param micro_res: microscopy resolution in nm (used for scaling).
    :param ims_res: IMS resolution in nm (used for scaling).
    """

    def __init__(self, imzml_file, ibd_file, micro_res, ims_res):
        # When passing the ibd path explicitly,
        # the file object must be opened manually
        self.parser = ImzMLParser(
            filename=imzml_file, ibd_file=open(ibd_file, "rb")
        )
        self.micro_res = micro_res
        self.ims_res = ims_res
        self.ims_px_in_micro = ims_res / micro_res  # scaling factor

        mz_lengths = self.parser.mzLengths
        if not (mz_lengths.count(mz_lengths[0]) == len(mz_lengths)):
            raise ValueError(
                "The number of m/z is not the same at each coordinate."
            )
        self.mzs, _ = self.parser.getspectrum(0)
        self.domain = None

    def _get_min_max_coords(self):
        coords = np.array(self.parser.coordinates)
        x_min, y_min, _ = np.min(coords, axis=0)
        x_max, y_max, _ = np.max(coords, axis=0)
        return CoordExtent(x_min, y_min, x_max, y_max)

    def _format_mzs(self, precision=4):
        return np.round(self.mzs, precision).astype(str)

    def to_columnar(self, dtype="uint32"):
        coords = np.array(self.parser.coordinates)
        x, y, _ = coords.T

        coords_df = pd.DataFrame(
            {
                "x": x,
                "y": y,
                "micro_x_topleft": self.ims_px_in_micro * (x - 1),
                "micro_y_topleft": self.ims_px_in_micro * (y - 1),
                "micro_px_width": np.repeat(self.ims_px_in_micro, len(coords)),
            },
            dtype=dtype,
        )

        # Pre-allocate memory for array of known dimensions for performance.
        intensities = np.zeros((len(coords_df), len(self.mzs)))

        # Fill array with intensities rather than using list comprehension.
        for i in range(len(coords)):
            _, coord_intensities = self.parser.getspectrum(i)
            intensities[i, :] = coord_intensities

        intensities_df = pd.DataFrame(
            intensities, columns=self._format_mzs(), dtype=dtype,
        )

        return coords_df.join(intensities_df)

    def to_array(self):
        extent = self._get_min_max_coords()

        # Pre-allocate memory for 3D array of known dimensions (mz, x, y).
        # Better performance filling contiguous memory allocation.
        arr = np.zeros(
            (
                self.parser.mzLengths[0],
                extent.y_max - extent.y_min + 1,
                extent.x_max - extent.x_min + 1,
            )
        )

        # Use the shifted x and y coordinates to index into 3D array.
        # Fill the mz dimension for the particular x, y coordinate.
        # This seems to be the safest/most reliable way get the
        # correct ordering of intensities in the 3D array, since
        # the array will be filled the same regardless of the
        # ordering of the coordinates yielded by the parser.
        #
        # Ex.
        #
        # for idx, coord in enumerate(self.parser.coordinates):
        # print(coord)
        # (0, 0)      (0, 0)       (1, 2)
        # (0, 1)      (1, 0)       (1, 0)
        # (0, 2)      (0, 1)       (0, 2)
        # (1, 0)  vs  (1, 1)   vs  (0, 0)
        # (1, 1)      (0, 2)       (0, 1)
        # (1, 2)      (1, 2)       (1, 2)
        #
        for idx, (x, y, _) in enumerate(self.parser.coordinates):
            _, intensities = self.parser.getspectrum(idx)
            arr[:, y - extent.y_min, x - extent.x_min] = intensities

        return arr

    def write_zarr(self, path, dtype=None, compressor=None, chunks=None):
        arr = self.to_array()
        extent = self._get_min_max_coords()

        if chunks is None:
            # If chunk size not specified, optimized for 2D access:
            # Each mz offset is a contiguous 2D image channel.
            chunks = [
                1,
                None,
                None,
            ]

        if dtype is None:
            # Get corresponding dtype from pyimzml spec
            dtype = DTYPE_DICT[self.parser.intensityPrecision]

        # zarr.js does not support compression yet
        # https://github.com/gzuidhof/zarr.js/issues/1
        z_arr = zarr.open(
            path,
            mode="w",
            shape=arr.shape,
            compressor=compressor,
            dtype=dtype,
            chunks=chunks,
        )
        # write array with metadata
        z_arr[:, :, :] = arr
        self.domain = [int(np.min(z_arr)), int(np.max(z_arr))]
        self.translate = [
            int(extent.y_min * self.ims_px_in_micro),
            int(extent.x_min * self.ims_px_in_micro),
        ]
        z_arr.attrs["domain"] = self.domain
        z_arr.attrs["transform"] = {
            "translate": self.translate,
            "scale": self.ims_px_in_micro,
        }

        z_arr.attrs["mz"] = self._format_mzs().tolist()


def write_metadata_json(
    json_file, zarr_store_url, zarr_path, domain, scale, translate
):
    json_out = {
        "dimensions": ["mz", "y", "x"],
        "zarrConfig": {"store": zarr_store_url, "path": zarr_path},
        "domain": domain,
        "transform": {"scale": scale, "translate": translate},
    }
    json.dump(json_out, json_file, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create zarr from Spraggins dataset."
    )
    parser.add_argument(
        "--imzml_file",
        required=True,
        help="imzML file from Jeff Spraggins' lab.",
    )
    parser.add_argument(
        "--ibd_file",
        required=True,
        help="Corresponding ibd file from Jeff Spraggins' lab",
    )
    parser.add_argument(
        "--ims_zarr",
        required=True,
        help="Write the IMS data to this zarr file.",
    )
    # FileType('x'): exclusive file creation, fails if file already exits.
    parser.add_argument(
        "--ims_metadata",
        type=argparse.FileType("x"),
        required=True,
        help="Write the metadata about the IMS zarr store on S3.",
    )
    parser.add_argument(
        "--zarr_store_url",
        required=True,
        help="Destination for zarr output in cloud.",
    )
    args = parser.parse_args()

    dataset = IMSDataset(
        args.imzml_file, args.ibd_file, micro_res=0.5, ims_res=10
    )
    dataset.write_zarr(args.ims_zarr, compressor=Zlib(level=1))
    write_metadata_json(
        args.ims_metadata,
        args.zarr_store_url,
        Path(args.ims_zarr).name,
        dataset.domain,
        dataset.ims_px_in_micro,
        dataset.translate,
    )
