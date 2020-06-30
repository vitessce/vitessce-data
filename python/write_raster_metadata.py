#!/usr/bin/env python3

import json
import argparse
from pathlib import Path


def _dir_path(string):
    path = Path(string)
    if path.is_dir():
        return path
    else:
        raise Exception(f'"{string}" is not a directory')


def gather_image_metadata(image_dir):
    images = []
    for fp in image_dir.glob('*.image.json'):
        with open(fp, 'r') as f:
            images.append(json.load(f))
    return images


def write_metadata(json_out, image_metadata, render_layers):
    raster_json = {
        'schemaVersion': '0.0.2',
        'renderLayers': render_layers,
        'images': image_metadata
    }
    json.dump(raster_json, json_out, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Combine individual images into single raster schema"
    )
    parser.add_argument(
        "--raster_json",
        type=argparse.FileType("x"),
        required=True,
        help="Write raster metadata into single output.",
    )
    parser.add_argument(
        '--image_metadata_dir',
        required=True,
        help="Path to directory with image metadata",
    )
    parser.add_argument(
        '--render_layers',
        required=True,
        help="List of names of images in the order to be rendered.",
    )
    args = parser.parse_args()
    img_dir = _dir_path(args.image_metadata_dir)
    image_metadata = gather_image_metadata(img_dir)
    write_metadata(
        args.raster_json, image_metadata, args.render_layers.split(',')
    )
