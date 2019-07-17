#!/usr/bin/env bash
set -o errexit

die() { set +v; echo "$*" 1>&2 ; exit 1; }

if [ "$#" -ne 0 ]; then
    die 'Collects source data, processes it, and pushes to S3.
No commandline arguments, but looks for two environment variables:
  "NO_PUSH=true" will fetch and process data, but not push to S3.
  "CI=true" will use fixtures, rather than fetching, and also will not push to S3.
'
fi

main() {
  process_linnarson_cells
  process_linnarson_molecules
  process_linnarson_images
  process_giotto
  process_mermaid

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
    aws s3 cp --exclude "$OUTPUT/*.png" --recursive "$OUTPUT" s3://"$S3_TARGET"
  fi
}

### Globals

BASE=`dirname "$0"`
S3_TARGET=`cat s3_target.txt`

BLOBS_URL='https://storage.googleapis.com/linnarsson-lab-www-blobs/blobs'
OSMFISH_URL='http://linnarssonlab.org/osmFISH'
GIOTTO_URL='https://vitessce-data.s3.amazonaws.com/source-data/giotto'
MERMAID_URL='https://jef.works/MERmaid'

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
  DATA_TITLE=$2

  FILE="$OUTPUT/$DATA_TITLE.$FILE_TYPE.json"
  if [ -e "$FILE" ]
  then
    echo "$FILE_TYPE output already exists: $FILE"
  else
    CLI_ARGS="$CLI_ARGS --${FILE_TYPE}_file $FILE"
  fi

}

process_linnarson_cells() {
  # Download and process data which describes cell locations, boundaries,
  # and gene expression levels. Multiple JSON output files are produced:
  # The files are redudant, but this reduces the processing that needs
  # to be done on the client-side.

  LOOM_IN="$INPUT/linnarsson.cells.loom"
  PKL_IN="$INPUT/linnarsson.cells.pkl"

  CLI_ARGS="--integers --loom $LOOM_IN --pkl $PKL_IN"
  add_arg 'cells' 'linnarsson'
  add_arg 'clusters' 'linnarsson'
  add_arg 'genes' 'linnarsson'
  add_arg 'neighborhoods' 'linnarsson'
  add_arg 'factors' 'linnarsson'

  echo "Download and process cells..."

  [ -e "$LOOM_IN" ] || \
    wget "$OSMFISH_URL/osmFISH_SScortex_mouse_all_cells.loom" -O "$LOOM_IN"
  [ -e "$PKL_IN" ] || \
    wget "$BLOBS_URL/osmFISH/data/polyT_seg.pkl" -O "$PKL_IN"

  JSON_OUT="$OUTPUT/linnarsson.cells.json"
  if [ -e "$JSON_OUT" ]
  then
    echo "Skipping cells -- output already exists: $JSON_OUT"
    return
  fi

  echo 'Generating cells JSON may take a while...'
  CMD="$BASE/python/cell_reader.py $CLI_ARGS"
  echo "running: $CMD"
  $CMD
}

process_linnarson_molecules() {
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

process_linnarson_images() {
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
      --sample 8 \
      --json_file "$JSON_OUT"
    echo "head $JSON_OUT:"
    head "$JSON_OUT"
  fi

  TILES_BASE='linnarsson.tiles'
  TILES_PATH="$OUTPUT/$TILES_BASE"
  if [ -e "$TILES_PATH" ]
  then
    echo "Skipping tiling -- output already exists: $TILES_PATH"
  else
    URL_PREFIX="https://s3.amazonaws.com/$S3_TARGET/$TILES_BASE"
    iiif_static.py $OUTPUT/*.png --prefix=$URL_PREFIX --dst=$TILES_PATH --max-image-pixels=2000000000
  fi
}

process_giotto() {
  # Download and process data which describes cell locations, boundaries,
  # and gene expression levels. Multiple JSON output files are produced:
  # The files are redudant, but this reduces the processing that needs
  # to be done on the client-side.

  JSON_IN="$INPUT/giotto.cells.json"

  CLI_ARGS="--json_file $JSON_IN"
  add_arg 'cells' 'giotto'
  add_arg 'factors' 'giotto'

  echo "$CLI_ARGS"

  echo "Download and process cells..."

  [ -e "$JSON_IN" ] || \
    wget "$GIOTTO_URL/giotto.cells.json" -O "$JSON_IN"

  JSON_OUT="$OUTPUT/giotto.cells.json"
  if [ -e "$JSON_OUT" ]
  then
    echo "Skipping cells -- output already exists: $JSON_OUT"
    return
  fi

  echo 'Generating cells JSON may take a while...'
  CMD="$BASE/python/giotto_json_reader.py $CLI_ARGS"
  echo "running: $CMD"
  $CMD
}

process_mermaid() {
  # Download and process data which describes cell locations, boundaries,
  # and gene expression levels. Multiple JSON output files are produced:
  # The files are redudant, but this reduces the processing that needs
  # to be done on the client-side.

  CSV_IN="$INPUT/mermaid.csv"

  CLI_ARGS="--csv_file $CSV_IN"
  add_arg 'cells' 'mermaid'
  add_arg 'molecules' 'mermaid'
  add_arg 'images' 'mermaid'

  echo "Download and process cells..."

  if [ -e "$CSV_IN" ]
  then
    echo "Skipping csv -- output already exists: $CSV_IN"
  else
    wget "$MERMAID_URL/data.csv.gz" -O "$CSV_IN.gz"
    gunzip -df "$CSV_IN"
    mv
  fi

  PNG_IN="$INPUT/mermaid.png"
  if [ -e "$PNG_IN" ]
  then
    echo "Skipping image -- output already exists: $PNG_IN"
  else
    wget "$MERMAID_URL/bg.png" -O "$PNG_IN"
  fi

  CELLS_OUT="$OUTPUT/memrmaid.cells.json"
  if [ -e "$CELLS_OUT" ]
  then
    echo "Skipping cells -- output already exists: $CELLS_OUT"
    return
  fi

  cp $INPUT/mermaid.png $OUTPUT/mermaid.png

  URL_PREFIX="https://s3.amazonaws.com/$S3_TARGET"
  mkdir -p "$OUTPUT/mermaid.images/"
  JSON_STRING='{ "type": "image", "url": "'$URL_PREFIX'/mermaid.png" }'
  echo $JSON_STRING > "$OUTPUT/mermaid.images/info.json"

  echo 'Generating cells JSON may take a while...'
  CMD="$BASE/python/mermaid_csv_reader.py $CLI_ARGS"
  echo "running: $CMD"
  $CMD
}

### Main

main
