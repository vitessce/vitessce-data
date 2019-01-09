# hubmap-data-loader
Utils for loading HuBMAP data formats

```
>>> from loom_reader import LoomReader
>>> lr = LoomReader('fixtures/osmFISH.loom')

>>> clusters = lr.clusters()
>>> clusters[4].name
'pyramidal L4'
>>> sorted(clusters[4].cell_ids)[:3]
['104', '110', '111']

>>> lr.tsne()['42']
(-6.917270183563232, 16.644561767578125)

>>> lr.xy()['42']
(21164.715090522037, 35788.13777399956)

```
