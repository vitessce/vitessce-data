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
  if [[ "$CI" = 'true' ]] || [[ "$NO_PUSH" = 'true' ]]
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
  CELLS_OUT="$OUTPUT/linnarsson.cells.json"
  CLUSTER_OUT="$OUTPUT/linnarsson.cluster.json"
  TRANSFORM_OUT="$OUTPUT/linnarsson.transform.json"
  GENES_OUT="$OUTPUT/linnarsson.genes.json"
  NEIGHBORHOODS_OUT="$OUTPUT/linnarsson.neighborhoods.json"

  if [ -e "$CELLS_OUT" ]
  then
    echo "Skipping cells -- output already exists: $CELLS_OUT"
    return
  fi

  echo "Download and process cells..."

  [ -e "$LOOM_IN" ] || \
    wget "$OSMFISH_URL/osmFISH_SScortex_mouse_all_cells.loom" -O "$LOOM_IN"
  [ -e "$PKL_IN" ] || \
    wget "$BLOBS_URL/osmFISH/data/polyT_seg.pkl" -O "$PKL_IN"

  echo 'Generating cells JSON may take a while...'
  "$BASE/python/cell_reader.py" \
    --loom "$LOOM_IN" \
    --pkl "$PKL_IN" \
    --save_transform "$TRANSFORM_OUT" \
    --cells_out "$CELLS_OUT" \
    --cluster_out "$CLUSTER_OUT" \
    --genes_out "$GENES_OUT"
    # TODO: too slow right now for tests: need to make smaller sample.
    # --neighborhoods_out "$NEIGHBORHOODS_OUT"
  echo "head $CELLS_OUT:"
  head "$CELLS_OUT"
  echo "head $CLUSTER_OUT:"
  cut -c 1-80 "$CLUSTER_OUT" | head
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

  echo 'Generating molecules JSON may take a while...'
  "$BASE/python/counts_hdf5_reader.py" \
    --hdf5 "$HDF5_IN" \
    --transform "$TRANSORM_IN" \
    > "$JSON_OUT"
  echo "head $JSON_OUT:"
  head "$JSON_OUT"
}

process_images() {
  # NOTE: The name is actually "Linnarsson", with two "S"s, but this is the URL.
  PKLAB_URL='http://pklab.med.harvard.edu/viktor/data/spatial/linnarson'
  HDF5_IN="$INPUT/linnarsson.imagery.hdf5"

  for CHANNEL_CLIP in 'polyT:200' 'nuclei:20'; do
    CHANNEL=`echo $CHANNEL_CLIP | cut -d ':' -f 1`
    CLIP=`echo $CHANNEL_CLIP | cut -d ':' -f 2`
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
      --clip $CLIP \
      --s3_target "$S3_TARGET"
    echo "head $JSON_OUT:"
    head "$JSON_OUT"
  done
}

### Main

main
