#!/usr/bin/env python3
import pyvips
import argparse
import os

# pyvips can run into issues with conda environments. Recommend to use a
# clean environment, brew install vips and pip install pyvips


def tile_ometiff(filename, channel_pages, output_directory):
    for (channel, page) in channel_pages:
        image = pyvips.Image.tiffload(filename, page=page)

        path = os.path.join(
            output_directory,
            'linnarsson.images.{}'.format(channel)
        )

        if not os.path.exists(path):
            os.mkdir(path)

        pyvips.Image.dzsave(image, os.path.join(path, channel))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create tiles with DeepZoom file.')
    parser.add_argument(
        '--ometiff_file',
        help='OME-TIFF image to be tiled.')
    parser.add_argument(
        '--channel_page_pairs', required=True, nargs='+',
        help='Colon-delimited pairs of channels and page values')
    parser.add_argument(
        '--output_directory', required=True,
        help='Directory for output')
    args = parser.parse_args()

    channel_pages = [pair.split(':') for pair in args.channel_page_pairs]

    tile_ometiff(
        filename=args.ometiff_file,
        channel_pages=channel_pages,
        output_directory=args.output_directory
    )
