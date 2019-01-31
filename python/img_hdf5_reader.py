from h5py import File
import numpy as np
import png


class ImgHdf5Reader:
    def __init__(self, filename):
        self.data = File(filename, 'r')

    def keys(self):
        '''
        # >>> path = 'fixtures/Nuclei_polyT.int16.sf.hdf5'
        # >>> reader = ImgHdf5Reader(path)
        # >>> len(reader.keys())
        # 2
        # >>> sorted(list(reader.keys()))
        # ['nuclei', 'polyT']

        '''
        return self.data.keys()

    def __getitem__(self, key):
        return self.data[key]

    def sample(self, key, step):
        '''
        # >>> path = 'fixtures/Nuclei_polyT.int16.sf.hdf5'
        # >>> reader = ImgHdf5Reader(path)
        # >>> sample = reader.sample('polyT', 100)
        # >>> sample.shape
        # (318, 517)

        '''
        return self.data[key][::step, ::step]

    def scale_sample(self, key, step, max_allowed):
        '''
        Assumes there are no negative values

        # >>> path = 'fixtures/Nuclei_polyT.int16.sf.hdf5'
        # >>> reader = ImgHdf5Reader(path)
        # >>> reader.scale_sample('polyT', 100, 255).shape
        # (318, 517)

        '''
        sample = self.sample(key, step)
        max_found = np.max(sample)

        return sample / max_found * max_allowed

    def to_png(self, key, step, path):
        '''
        # >>> path = 'fixtures/Nuclei_polyT.int16.sf.hdf5'
        # >>> reader = ImgHdf5Reader(path)
        # >>> reader.to_png('polyT', 20, '/tmp/polyT-20.png')
        # >>> reader.to_png('nuclei', 20, '/tmp/nuclei-20.png')
        '''
        MAX_ALLOWED = 256
        NP_TYPE = np.int8

        scaled_sample = self.scale_sample(key, step, MAX_ALLOWED)\
            .astype(NP_TYPE)
        image = png.from_array(scaled_sample, mode='L')
        # TODO: Would like "L;4" but get error message.
        # TODO: Online PNG compression tools reduce size by 50%...
        #       Check Python PNG encoding options.
        image.save(path)
