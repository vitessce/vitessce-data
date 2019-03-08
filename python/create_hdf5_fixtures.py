#!/usr/bin/env python3

from h5py import File
import numpy as np

with File('/tmp/linnarsson.imagery.hdf5', 'w') as f:
    polyT = np.array([range(50) for x in range(50)])
    dataset = f.create_dataset('polyT', dtype='i', data=polyT)
    nuclei = np.array([range(50) for x in range(50)])
    dataset = f.create_dataset('nuclei', dtype='i', data=nuclei)
