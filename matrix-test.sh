#!/usr/bin/env bash
set -o errexit

die() { set +v; echo "$*" 1>&2 ; exit 1; }

./python/tsv-to-mrmatrix.py \
  fake-files/input/fake.tsv \
  fake-files/output/fake.hdf5

h5dump fake-files/output/fake.hdf5
