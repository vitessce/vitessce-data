#!/usr/bin/env python3

from apeer_ometiff_library import io, omexmlClass
import numpy as np

from pathlib import Path
import datetime


def create_omexml(image_array, channel_names):
    metadata = omexmlClass.OMEXML()
    image = metadata.image()
    image.AcquisitionDate = datetime.datetime.now().isoformat()

    pixels = image.Pixels
    pixels.SizeX = image_array.shape[2]
    pixels.SizeY = image_array.shape[1]
    pixels.SizeC = image_array.shape[0]
    pixels.PixelType = str(image_array.dtype)

    pixels.channel_count = len(channel_names)
    for i, name in enumerate(channel_names):
        pixels.Channel(i).Name = name

    return f'<?xml version="1.0" encoding="UTF-8"?>\n{metadata}'


if __name__ == "__main__":
    outfile = (
        Path("fake-files") / "input" / "spraggins" / "spraggins.mxif.ome.tif"
    )
    arr = np.arange(4 * 50 * 50).reshape((4, 50, 50))
    channel_names = [
        "DAPI - Hoescht (nuclei)",
        "FITC - Laminin (basement membrane)",
        "Cy3 - Synaptopodin (glomerular)",
        "Cy5 - THP (thick limb)",
    ]
    omexml_string = create_omexml(arr, channel_names)
    io.write_ometiff(str(outfile), arr, omexml_string)
