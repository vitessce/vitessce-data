# 🚄  vitessce-data

Utils to pre-process data for [Vitessce](http://github.com/hms-dbmi/vitessce/#readme).

Sample datasets come from:
- [Codeluppi et al.: Spatial organization of the somatosensory cortex revealed by cyclic smFISH ](http://linnarssonlab.org/osmFISH/availability/)
- [Dries et al.: Giotto, a pipeline for integrative analysis and visualization of single-cell spatial transcriptomic data](https://www.biorxiv.org/content/10.1101/701680v1)
- [Wang et al.: Multiplexed imaging of high density libraries of RNAs with MERFISH and expansion microscopy](https://www.biorxiv.org/content/10.1101/238899v1)
- [Cao et al.: The single-cell transcriptional landscape of mammalian organogenesis](https://mouse-organogenesis.cells.ucsc.edu)

JSON is our target format right now because it is easily read by Javascript,
and not so inefficient as to cause problems with storage or processing.
For example: The mRNA HDF5 is 30M, but as JSON it is still only 37M.

## Install

`vitessce-data` requires Python 3. First, set up a clean environment. If you are using conda:
```
conda create python=3.6 -n vitessce-data
# Confirm install, and then:
source activate vitessce-data
```
Then install vips with `brew`:
```
brew install vips
```
and install other dependencies with `pip`:
```
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Develop and run

- `test.sh` exercises all the scripts, using the fixtures in `fake-files/`,
and errors if the output is not what is expected.
- `process.sh` downloads full data from the internet, caches these input files in `big-files/input`,
processes them, caches the output in `big-files/output`, and pushes to S3.

`process.sh` only performs the work necessary. To regenerate just a portion of the data,
delete the files in `big-files/output` that need to be replaced.
