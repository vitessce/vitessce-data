import loompy
from collections import namedtuple


class LoomReader:
    def __init__(self, filename):
        self.ds = loompy.connect(filename)

    def clusters(self):
        '''
        Returns information about each cluster.

        >>> lr = LoomReader('fixtures/osmFISH.loom')
        >>> clusters = lr.clusters()
        >>> clusters[4].name
        'pyramidal L4'
        >>> sorted(clusters[4].cell_ids)[:3]
        ['104', '110', '111']
        '''
        clusters = {}
        Cluster = namedtuple('Cluster', ['name', 'cell_ids'])

        clustered_cell_zip = zip(
            self.ds.ca['Valid'],
            self.ds.ca['ClusterID'],
            self.ds.ca['ClusterName'],
            self.ds.ca['CellID']
        )
        for (valid, cluster_id, cluster_name, cell_id) in clustered_cell_zip:
            if valid:
                if cluster_id in clusters:
                    clusters[cluster_id].cell_ids.append(cell_id)
                else:
                    clusters[cluster_id] = Cluster(cluster_name, [cell_id])
        return clusters

    def tsne(self):
        '''
        Returns a tSNE pair for each valid cell.

        >>> lr = LoomReader('fixtures/osmFISH.loom')
        >>> tsne = lr.tsne()
        >>> tsne['42']
        (-6.917270183563232, 16.644561767578125)
        '''
        cells = {}

        tsne_zip = zip(
            self.ds.ca['Valid'],
            self.ds.ca['CellID'],
            self.ds.ca['_tSNE_1'],
            self.ds.ca['_tSNE_2']
        )
        for (valid, cell_id, tsne1, tsne2) in tsne_zip:
            if valid:
                cells[cell_id] = (tsne1, tsne2)
        return cells

    def xy(self):
        '''
        Returns the xy position for each valid cell.

        >>> lr = LoomReader('fixtures/osmFISH.loom')
        >>> xy = lr.xy()
        >>> xy['42']
        (21164.715090522037, 35788.13777399956)
        '''
        cells = {}

        tsne_zip = zip(
            self.ds.ca['Valid'],
            self.ds.ca['CellID'],
            self.ds.ca['X'],
            self.ds.ca['Y']
        )
        for (valid, cell_id, x, y) in tsne_zip:
            if valid:
                cells[cell_id] = (x, y)
        return cells
