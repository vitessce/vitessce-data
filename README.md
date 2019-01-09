# hubmap-data-loader
Utils for loading HuBMAP data formats

Working with data from [Linnarson Lab](http://linnarssonlab.org/osmFISH/availability/):
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
