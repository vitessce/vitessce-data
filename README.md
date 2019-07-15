# 🚄  vitessce-data

Utils to pre-process data for [vitessce](http://github.com/hms-dbmi/vitessce/#readme)

Right now, the focus is reading the particular formats supplied by
the [Linnarsson Lab](http://linnarssonlab.org/osmFISH/availability/)
and translating them into JSON for our viewer.

Additionally, we have visualized data supplied by Ruben Dries and the G. C. Yuan lab


JSON is our target format right now because it is easily read by Javascript,
and not so inefficient as to cause problems with storage or processing.
For example: The mRNA HDF5 is 30M, but as JSON it is still only 37M.

## Install

`vitessce-data` requires Python 3. Use pip to install dependencies:

```
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Run

`process.sh` runs all the other scripts: It will fetch files,
if they are not already cached, and process them, if the output is not
already in `big-files/`, and push the results to S3.
