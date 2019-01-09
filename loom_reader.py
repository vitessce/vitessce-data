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
