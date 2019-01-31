from pickle import load


class SegPickleReader:
    def __init__(self, filename):
        with open(filename, 'rb') as f:
            self.data = load(f)

    def __repr__(self):
        return str(self.data)

    def __getitem__(self, key):
        return self.data[key]
