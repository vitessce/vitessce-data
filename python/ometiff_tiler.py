#!/usr/bin/env python3
import pyvips
import argparse
import os


def tile_ometiff(filename, channel_pages, output_directory, data_name):
    for (channel, page) in channel_pages:
        image = pyvips.Image.tiffload(filename, page=page)

        path = os.path.join(
            output_directory,
            '{}.images.{}'.format(data_name, channel)
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
    parser.add_argument(
        '--dataset_name', required=True,
        help='Name for dataset')
    args = parser.parse_args()

    channel_pages = [pair.split(':') for pair in args.channel_page_pairs]

    tile_ometiff(
        filename=args.ometiff_file,
        channel_pages=channel_pages,
        output_directory=args.output_directory,
        data_name=args.dataset_name
    )
