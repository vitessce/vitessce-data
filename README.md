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

Set up the `vitessce-data` environment using conda:

```sh
conda env create -f environment.yml
```

Users may also install the dependencies with pip:

```sh
pip install -r requirements.txt
```

## Develop and run

```sh
conda activate vitessce-data

# To update with new packages:
conda env update --file environment.yml --prune
```

- `test.sh` exercises all the scripts, using the fixtures in `fake-files/`,
and errors if the output is not what is expected.
- `process.sh` downloads full data from the internet, caches these input files in `big-files/input`,
processes them, caches the output in `big-files/output`, and pushes to S3.

`process.sh` only performs the work necessary. To regenerate just a portion of the data,
delete the files in `big-files/output` that need to be replaced.

### Configure AWS and Google Cloud CLIs

Install `aws` CLI and add to your PATH ([reference](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html)).

Install `gcloud` and `gsutil` and add to your PATH ([reference](https://cloud.google.com/storage/docs/gsutil_install#linux)).

Configure the AWS CLI by setting AWS environment variables ([reference](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)) or running `aws configure`  ([reference](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)).

Configure the Google Cloud CLI by running `gcloud auth login` ([reference](https://cloud.google.com/sdk/gcloud/reference/auth/login)).


### Creating a new release

Update the contents of `cloud_target.txt` to bump the version number. Then update the version where it is referenced in test fixtures in the `fake-files/` directory.
