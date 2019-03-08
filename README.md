# 🚄  vitessce-data

Utils to pre-process data for [vitessce](http://github.com/hms-dbmi/vitessce/#readme)

Right now, the focus is reading the particular formats supplied by
the [Linnarson Lab](http://linnarssonlab.org/osmFISH/availability/)
and translating them into JSON for our viewer.

JSON is our target format right now because it is easily read by Javascript,
and not so inefficient as to cause problems with storage or processing.
For example: The mRNA HDF5 is 30M, but as JSON it is still only 37M.

Python scripts can be called individually, or `linnarsson-osmfish.sh`
will do everything and drop the results in `big-files/`, and push it to S3.
