#!/usr/bin/env bash
set -o errexit

die() { set +v; echo "$*" 1>&2 ; exit 1; }

main() {
  process_cells
  process_molecules
  process_images

  echo
  echo 'input:'
  ls -lh "$INPUT"/*

  echo
  echo 'output:'
  ls -lh "$OUTPUT"/*
}

### Globals

BASE=`dirname "$0"`

BLOBS_URL='https://storage.googleapis.com/linnarsson-lab-www-blobs/blobs'
OSMFISH_URL='http://linnarssonlab.org/osmFISH'

if [[ "$CI" = 'true' ]]
then
  wget() {
    die "Add fixture to 'fake-files/input': Should not 'wget' in test run: 'wget $*'"
  }
  FILES="$BASE/fake-files"
else
  FILES="$BASE/big-files"
fi

INPUT="$FILES/input"
OUTPUT="$FILES/output"

[ -d "$INPUT" ] || mkdir "$INPUT"
[ -d "$OUTPUT" ] || mkdir "$OUTPUT"

### Functions

process_cells() {
  LOOM_IN="$INPUT/linnarsson.cells.loom"
  PKL_IN="$INPUT/linnarsson.cells.pkl"
  JSON_OUT="$OUTPUT/linnarsson.cells.json"
  TRANSFORM_OUT="$OUTPUT/linnarsson.transform.json"

  if [ -e "$JSON_OUT" ]
  then
    echo "Skipping cells -- output already exists: $JSON_OUT"
    return
  fi

  echo "Download and process cells..."

  [ -e "$LOOM_IN" ] || \
    wget "$OSMFISH_URL/osmFISH_SScortex_mouse_all_cells.loom" -O "$LOOM_IN"
  [ -e "$PKL_IN" ] || \
    wget "$BLOBS_URL/osmFISH/data/polyT_seg.pkl" -O "$PKL_IN"

  echo 'Generating JSON may take a while...'
  "$BASE/python/cell_reader.py" \
    --loom "$LOOM_IN" \
    --pkl "$PKL_IN" \
    --save_transform "$TRANSFORM_OUT" \
    > "$JSON_OUT"
  head "$JSON_OUT"
}

process_molecules() {
  HDF5_IN="$INPUT/linnarsson.molecules.hdf5"
  JSON_OUT="$OUTPUT/linnarsson.molecules.json"

  if [ -e "$JSON_OUT" ]
  then
    echo "Skipping molecules -- output already exists: $JSON_OUT"
    return
  fi

  echo "Download and process molecules..."

  [ -e "$HDF5_IN" ] || \
    wget "$BLOBS_URL/osmFISH/data/mRNA_coords_raw_counting.hdf5" -O "$HDF5_IN"
  which h5dump && \
    h5dump "$HDF5_IN" | head

  echo 'Generating JSON may take a while...'
  "$BASE/python/counts_hdf5_reader.py" "$HDF5_IN" > "$JSON_OUT"
  head "$JSON_OUT"
}

process_images() {
  echo 'TODO: images'
}

### Main

main
