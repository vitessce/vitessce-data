#!/usr/bin/env python3

import json
import argparse
from pathlib import Path


def gather_image_metadata(image_dir):
    images = []
    for fp in image_dir.glob('*.image.json'):
        with open(fp, 'r') as f:
            images.append(json.load(f))
    return images


def write_metadata(json_out, image_metadata):
    raster_json = {
        'schema_version': '0.0.1',
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
    args = parser.parse_args()
    image_metadata = gather_image_metadata(Path(args.image_metadata_dir))
    write_metadata(args.raster_json, image_metadata)
