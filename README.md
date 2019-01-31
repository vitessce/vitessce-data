# 🚄  vitessce-data

Utils to pre-process data for [vitessce](http://github.com/hms-dbmi/vitessce/)

Right now, the focus is reading the particular formats supplied by
the [Linnarson Lab](http://linnarssonlab.org/osmFISH/availability/)
and translating them into JSON for our viewer.

JSON is our target format right now because it is easily read by Javascript,
and not so inefficient as to cause problems with storage or processing.
For example: The mRNA HDF5 is 30M, but as JSON it is still only 37M.

## Scripts

mRNA locations are provided in HDF5 and we translate that into JSON.
The translation will take a few minutes.
```shell
$ curl --silent https://storage.googleapis.com/linnarsson-lab-www-blobs/blobs/osmFISH/data/mRNA_coords_raw_counting.hdf5 > /tmp/mrna.molecules.hdf5
$ h5dump /tmp/mrna.hdf5 | head # Not required: Just want to show what the source data looks like.
HDF5 "/tmp/mrna.hdf5" {
GROUP "/" {
   DATASET "Acta2_Hybridization5" {
      DATATYPE  H5T_IEEE_F64LE
      DATASPACE  SIMPLE { ( 13052, 2 ) / ( 13052, 2 ) }
      DATA {
      (0,0): 18215, 20052,
      (1,0): 24916, 17015,
      (2,0): 8400, 44522,
      (3,0): 22667, 23208,
$ ./counts_hdf5_reader.py /tmp/mrna.hdf5 > /tmp/mrna.molecules.json
$ head /tmp/mrna.molecules.json
{
"Acta2_Hybridization5":[
[18215.0, 20052.0],
[24916.0, 17015.0],
[8400.0, 44522.0],
[22667.0, 23208.0],
[6336.0, 37555.0],
[9083.0, 32082.0],
[7624.0, 29461.0],
[16161.0, 6948.0],
```

Cell data is provided in two separate files. Metadata about cells is
in LOOM, while the cell polygons are in Python Pickles (which is not
a choice to be emulated: because of security problems,
Pickle should never really be used as an interchange format.)
```
TODO
```

## Python internals

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

### Imaging


Coordinates: http://pklab.med.harvard.edu/viktor/data/spatial/linnarson/mRNA_coords_updated.hdf5

Both stainings: http://pklab.med.harvard.edu/viktor/data/spatial/linnarson/Nuclei_polyT.int16.sf.hdf5
