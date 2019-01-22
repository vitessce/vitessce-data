from h5py import File
import numpy as np
import png


class ImgHdf5Reader:
    def __init__(self, filename):
        self.data = File(filename, 'r')

    def keys(self):
        '''
        >>> path = 'fixtures/Nuclei_polyT.int16.sf.hdf5'
        >>> reader = ImgHdf5Reader(path)
        >>> len(reader.keys())
        2
        >>> sorted(list(reader.keys()))
        ['nuclei', 'polyT']

        '''
        return self.data.keys()

    def __getitem__(self, key):
        return self.data[key]

    def sample(self, key, step):
        '''
        >>> path = 'fixtures/Nuclei_polyT.int16.sf.hdf5'
        >>> reader = ImgHdf5Reader(path)
        >>> sample = reader.sample('polyT', 100)
        >>> sample.shape
        (318, 517)

        '''
        return self.data[key][::step, ::step]

    def scale_sample(self, key, step, max_allowed):
        '''
        Assumes there are no negative values

        >>> path = 'fixtures/Nuclei_polyT.int16.sf.hdf5'
        >>> reader = ImgHdf5Reader(path)
        >>> reader.scale_sample('polyT', 100, 255).shape
        (318, 517)

        '''
        sample = self.sample(key, step)
        max_found = np.max(sample)

        return sample / max_found * max_allowed

    def scaled_sample_to_png(self, key, step, max_allowed, path):
        '''
        >>> path = 'fixtures/Nuclei_polyT.int16.sf.hdf5'
        >>> reader = ImgHdf5Reader(path)
        >>> handle = open('/tmp/sampled.png', 'wb')
        >>> reader.scaled_sample_to_png('polyT', 100, 256, handle)

        '''
        scaled_sample = self.scale_sample(key, step, max_allowed)
        scaled_sample = scaled_sample.astype(np.int8)
        image = png.from_array(scaled_sample, mode='L')
        image.save(path)
