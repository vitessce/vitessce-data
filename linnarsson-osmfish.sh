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

  echo
  echo 'AWS:'
  if [[ "$CI" = 'true' ]]
  then
    echo 'CI: Skip push to AWS'
  else
    aws s3 cp --recursive "$OUTPUT" s3://"$S3_TARGET"
  fi
}

### Globals

BASE=`dirname "$0"`
S3_TARGET=`cat s3_target.txt`

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
  TRANSORM_IN="$OUTPUT/linnarsson.transform.json"
  # Stored in the OUTPUT directory by the previous step.

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
  "$BASE/python/counts_hdf5_reader.py" \
    --hdf5 "$HDF5_IN" \
    --transform "$TRANSORM_IN" \
    > "$JSON_OUT"
  head "$JSON_OUT"
}

process_images() {
  PKLAB_URL='http://pklab.med.harvard.edu/viktor/data/spatial/linnarson'
  HDF5_IN="$INPUT/linnarsson.imagery.hdf5"

  for CHANNEL in 'polyT' 'nuclei'; do
    JSON_OUT="$OUTPUT/linnarsson.$CHANNEL.json"
    PNG_OUT="$OUTPUT/linnarsson.$CHANNEL.png"

    if [ -e "$PNG_OUT" ] && [ -e "$JSON_OUT" ]
    then
      echo "Skipping $CHANNEL imagery -- output already exists: $PNG_OUT"
      continue
    fi

    [ -e "$HDF5_IN" ] || \
      wget "$PKLAB_URL/Nuclei_polyT.int16.sf.hdf5" -O "$HDF5_IN"

    "$BASE/python/img_hdf5_reader.py" \
      --hdf5 "$HDF5_IN" \
      --channel "$CHANNEL" \
      --json_out "$JSON_OUT" \
      --png_out "$PNG_OUT" \
      --sample 5 \
      --s3_target "$S3_TARGET"
    echo "head $JSON_OUT:"
    head "$JSON_OUT"
  done
}

### Main

main
