#!/usr/bin/env bash
set -o errexit

BASE=`dirname "$0"`
BLOBS_URL='https://storage.googleapis.com/linnarsson-lab-www-blobs/blobs'

INPUT="$BASE/big-files/input"
OUTPUT="$BASE/big-files/output"

[ -d "$INPUT" ] || mkdir "$INPUT"
[ -d "$OUTPUT" ] || mkdir "$OUTPUT"

process_mrna() {
  MRNA_IN="$INPUT/mrna.molecules.hdf5"
  MRNA_OUT="$OUTPUT/mrna.molecules.json"

  if [ -e "$MRNA_OUT" ]
  then
    echo "Skipping mRNA -- Output already exists: $MRNA_OUT"
    return
  fi

  echo "Download and process mRNA..."

  [ -e "$MRNA_IN" ] || \
    curl --silent "$BLOBS_URL/osmFISH/data/mRNA_coords_raw_counting.hdf5" \
    > "$MRNA_IN"
  which h5dump && \
    h5dump "$MRNA_IN" | head

  echo 'Generating JSON will take a while...'
  "$BASE/python/counts_hdf5_reader.py" "$MRNA_IN" > "$MRNA_OUT"
  head "$MRNA_OUT"
}

process_mrna
