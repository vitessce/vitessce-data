from h5py import File


class CountsHdf5Reader:
    def __init__(self, filename):
        self.data = File(filename, 'r')

    def keys(self):
        '''
        # >>> path = 'fixtures/mRNA_coords_raw_counting.hdf5'
        # >>> reader = CountsHdf5Reader(path)
        # >>> len(reader.keys())
        # 39
        # >>> sorted(list(reader.keys()))[:2]
        # ['Acta2_Hybridization5', 'Aldoc_Hybridization1']

        '''
        return self.data.keys()

    def __getitem__(self, key):
        '''
        # >>> path = 'fixtures/mRNA_coords_raw_counting.hdf5'
        # >>> reader = CountsHdf5Reader(path)
        # >>> reader['Acta2_Hybridization5'].shape
        # (13052, 2)
        # >>> reader['Acta2_Hybridization5'][0]
        # array([18215., 20052.])

        '''
        return self.data[key]
