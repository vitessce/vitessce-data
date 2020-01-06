import numpy as np
import pandas as pd
from pathlib import Path
from pyimzml.ImzMLParser import ImzMLParser
import zarr

import argparse


class IMSDataset:
    def __init__(self, imzml_file, ibd_file, micro_res=0.5, ims_res=10):
        self.parser = ImzMLParser(filename=imzml_file, ibd_file=ibd_file)
        self.micro_res = micro_res
        self.ims_res = ims_res
        self.ims_px_in_micro = ims_res / micro_res

    def __get_min_max_coords(self):
        coords = np.array(self.parser.coordinates)
        x_min, y_min, _ = np.min(coords, axis=0)
        x_max, y_max, _ = np.max(coords, axis=0)
        return x_min, y_min, x_max, y_max

    def to_columnar(self, mz_precision=4, dtype="uint32"):
        mzs, _ = self.parser.getspectrum(0)
        coords = np.array(dataset.parser.coordinates)
        x, y, _ = coords.T

        coords_df = pd.DataFrame(
            {
                "x": x,
                "y": y,
                "micro_x_topleft": x * self.ims_px_in_micro - self.ims_px_in_micro,
                "micro_y_topleft": y * self.ims_px_in_micro - self.ims_px_in_micro,
                "micro_px_width": np.repeat(self.ims_px_in_micro, len(coords)),
            },
            dtype=dtype,
        )

        intensities = np.zeros((len(coords_df), len(mzs)))
        for i in range(len(coords)):
            _, coord_intensities = self.parser.getspectrum(i)
            intensities[i, :] = coord_intensities

        intensities = pd.DataFrame(
            intensities, columns=np.round(mzs, mz_precision).astype(str), dtype=dtype
        )

        return coords_df.join(intensities)

    def to_array(self):
        x_min, y_min, x_max, y_max = self.__get_min_max_coords()
        mz_lengths = self.parser.mzLengths
        if not (mz_lengths.count(mz_lengths[0]) == len(mz_lengths)):
            raise ValueError("The number of m/z is not the same at each coordinate.")

        arr = np.zeros((x_max - x_min + 1, y_max - y_min + 1, mz_lengths[0]))

        for idx, (x, y, _) in enumerate(self.parser.coordinates):
            _, intensities = self.parser.getspectrum(idx)
            arr[x - x_min, y - y_min, :] = intensities

        return arr

    def write_zarr(self, path, dtype="i4"):
        arr = self.to_array()
        # zarr.js does not support compression yet
        z_arr = zarr.open(path, mode="w", shape=arr.shape, compressor=None, dtype=dtype)
        z_arr[:, :, :] = arr


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create zarr from Spraggins dataset.")
    parser.add_argument(
        "--imzml_file", required=True, help="imzML file from Jeff Spraggins' lab.",
    )
    parser.add_argument(
        "--ibd_file",
        required=True,
        help="Corresponding ibd file from Jeff Spraggin's lab",
    )
    args = parser.parse_args()

    dataset = IMSDataset(parser.imzml_file, parser.ibd_file)
    dataset.write_zarr(f"spraggins.zarr")
