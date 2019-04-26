#!/usr/bin/env bash
set -o errexit

die() { set +v; echo "$*" 1>&2 ; exit 1; }

if [ "$#" -ne 0 ]; then
    die 'Collects source data from the Linnarsson Lab, processes it, and pushes to S3.
No commandline arguments, but looks for two environment variables:
  "NO_PUSH=true" will fetch and process data, but not push to S3.
  "CI=true" will use fixtures, rather than fetching, and also will not push to S3.
'
fi

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
    # Exclude the *HUGE* PNGs in the base directory:
    # The tiles for S3 are in subdirectories;
    # We keep the PNGs around because it takes a long time to generate them.
    aws s3 cp --recursive "$OUTPUT" --exclude "$OUTPUT"/*.png s3://"$S3_TARGET"
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

add_arg() {
  # Helper for process_cells to build argument list.

  FILE_TYPE=$1
  FILE="$OUTPUT/linnarsson.$FILE_TYPE.json"
  if [ -e "$FILE" ]
  then
    echo "$FILE_TYPE output already exists: $FILE"
  else
    CLI_ARGS="$CLI_ARGS --${FILE_TYPE}_file $FILE"
  fi
}

process_cells() {
  # Download and process data which describes cell locations, boundaries,
  # and gene expression levels. Multiple JSON output files are produced:
  # The files are redudant, but this reduces the processing that needs
  # to be done on the client-side.

  LOOM_IN="$INPUT/linnarsson.cells.loom"
  PKL_IN="$INPUT/linnarsson.cells.pkl"

  CLI_ARGS="--integers --loom $LOOM_IN --pkl $PKL_IN"
  add_arg 'cells'
  add_arg 'clusters'
  add_arg 'genes'
  add_arg 'neighborhoods'
  add_arg 'factors'

  echo "Download and process cells..."

  [ -e "$LOOM_IN" ] || \
    wget "$OSMFISH_URL/osmFISH_SScortex_mouse_all_cells.loom" -O "$LOOM_IN"
  [ -e "$PKL_IN" ] || \
    wget "$BLOBS_URL/osmFISH/data/polyT_seg.pkl" -O "$PKL_IN"

  echo 'Generating cells JSON may take a while...'
  CMD="$BASE/python/cell_reader.py $CLI_ARGS"
  echo "running: $CMD"
  $CMD
}

process_molecules() {
  # Download and process data which describes molecule locations.
  # In structure, this is the simplest data, but it is also the largest.

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

  echo 'Generating molecules JSON may take a while...'
  "$BASE/python/counts_hdf5_reader.py" \
    --hdf5 "$HDF5_IN" \
    > "$JSON_OUT"
  echo "head $JSON_OUT:"
  head "$JSON_OUT"
}

process_images() {
  # Download and process raster data from HDF5 and produce PNGs.
  # Down the road we may want HiGlass, or some other solution:
  # This is a stopgap.

  # NOTE: The name is actually "Linnarsson", with two "S"s, but this is the URL.
  PKLAB_URL='http://pklab.med.harvard.edu/viktor/data/spatial/linnarson'
  HDF5_IN="$INPUT/linnarsson.imagery.hdf5"
  JSON_OUT="$OUTPUT/linnarsson.images.json"

  if [ -e "$JSON_OUT" ]
  then
    echo "Skipping big image generation -- output already exists: $JSON_OUT"
  else
    echo "Download and generate big images..."

    [ -e "$HDF5_IN" ] || \
      wget "$PKLAB_URL/Nuclei_polyT.int16.sf.hdf5" -O "$HDF5_IN"

    "$BASE/python/img_hdf5_reader.py" \
      --hdf5 "$HDF5_IN" \
      --channel_clip_pairs polyT:200 nuclei:20 \
      --json_file "$JSON_OUT"
    echo "head $JSON_OUT:"
    head "$JSON_OUT"
  fi

  if [ -e "$OUTPUT/tiles" ]
  then
    echo "Skipping tiling -- output already exists: $OUTPUT/tiles"
  else
    iiif_static.py $OUTPUT/*.png --dst=$OUTPUT/tiles --max-image-pixels=2000000000
  fi
}

### Main

main
