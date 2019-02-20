import numpy as np


def get_transform(metadata):
    xy_array = np.array([cell['xy'] for cell in metadata.values()])
    max_xy = np.max(xy_array, axis=0)
    min_xy = np.min(xy_array, axis=0)
    domain = 2000
    # Limited by raster-based picking in deck.gl:
    # https://github.com/uber/deck.gl/issues/2658#issuecomment-463293063
    return {
        'x_shift': - (max_xy[0] + min_xy[0]) / 2,
        'y_shift': - (max_xy[1] + min_xy[1]) / 2,
        'x_scale': domain / (max_xy[0] - min_xy[0]),
        'y_scale': domain / (max_xy[1] - min_xy[1])
    }


def apply_transform(transform, xy):
    # TODO: Rounding should be based on precision of input.
    return [
        round((xy[0] + transform['x_shift']) * transform['x_scale'], 2),
        round((xy[1] + transform['y_shift']) * transform['y_scale'], 2)
    ]
