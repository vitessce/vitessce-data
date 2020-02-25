#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

main() {

  get_CLI_args "$@"

  TILES_BASE='vanderbilt.images'
  TILES_PATH="$OUTPUT/$TILES_BASE"
  if [ -e "$TILES_PATH" ]
  then
      echo "Skipping tiling -- output already exists: $TILES_PATH"
  else
      if [ -e "$INPUT/vanderbilt.ome.tif" ]
      then
        echo "Not copying $INPUT/vanderbilt.ome.tif from s3 - already exists or testing"
      else
        aws s3 cp s3://vitessce-data/source-data/vanderbilt/vanderbilt.ome.tif "$INPUT/vanderbilt.ome.tif"
      fi
      RELEASE=${CLOUD_TARGET//vitessce-data\//}
      SERVER_URL="https://vitessce-data.storage.googleapis.com/$RELEASE/vanderbilt/"
      CMD='docker run --rm
          -e "SERVER_URL='$SERVER_URL'"
          -e "PREFIX=vanderbilt"
          -e "PYRAMID_TYPE=tiff"
          --mount "type=bind,src='$INPUT'/vanderbilt.ome.tif,destination=/input.ome.tif"
          --mount "type=bind,src='$OUTPUT',destination=/output_dir"
          --name tiler gehlenborglab/ome-tiff-tiler:v0.0.5'
      echo "Running: $CMD"
      eval $CMD
      # vitessce relies on this naming strategy, whereas the docker image is more general
      mv "$TILES_PATH/tiff.json" "$TILES_PATH/vanderbilt.raster.json" || \
        sudo mv "$TILES_PATH/tiff.json" "$TILES_PATH/vanderbilt.raster.json"
  fi
}

main "$@"
