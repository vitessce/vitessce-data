# hubmap-data-loader
Utils for loading HuBMAP data formats

## OSM FISH

Sample data is from [Linnarson Lab](http://linnarssonlab.org/osmFISH/availability/).

### Loom

```
>>> from loom_reader import LoomReader
>>> lr = LoomReader('fixtures/osmFISH.loom')

>>> sorted(lr.genes)[:5]
['Acta2', 'Aldoc', 'Anln', 'Apln', 'Bmp4']
>>> sorted(lr.cells)[:5]
['1', '10', '1000', '1001', '1002']

```

You can get information about clusters:
```
>>> clusters = lr.clusters()
>>> clusters[4].name
'pyramidal L4'
>>> sorted(clusters[4].cell_ids)[:3]
['104', '110', '111']

```

or cells:
```
>>> lr.tsne()['42']
(-6.917..., 16.644...)

>>> lr.xy()['42']
(21164.7..., 35788.1...)

>>> lr.by_cell('42')['Gad2']
7

```

or genes:
```
>>> lr.by_gene('Gad2')['42']
7

```

### Raw counts (HDF5)

TODO: Make small fixture

### Segmentation (Pickle)

```
>>> from segmentation_pickle_reader import SegPickleReader
>>> sp = SegPickleReader('fixtures/polyT_seg.42.pkl')
>>> sp['42']
array([[ 3750, 15088]...[ 3911, 15107]], dtype=uint32)

```
