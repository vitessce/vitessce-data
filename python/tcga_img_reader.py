#!/usr/bin/env python3

import json


def image_dict():
    s3_target = open('s3_target.txt').read().strip()
    url = 'https://s3.amazonaws.com/{}/tcga.images/info.json'.format(
        s3_target
    )
    image_dict = {
        'TCGA': {
            'sample': 1,
            'tileSource': 'https://s3.amazonaws.com/{}/tcga/'.format(s3_target)
        + 'tcga.tiles/tcga.dzi'
        }
    }

    return image_dict


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create JSON with tile data from TCGA svs.')
    parser.add_argument(
        '--images_file', type=argparse.FileType('x'),
        help='JSON file which will include image location.')
    args = parser.parse_args()

    if args.images_file:
        json.dump(image_dict(), args.images_file, indent=1)
