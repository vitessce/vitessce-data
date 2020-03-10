#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

main() {
    # Download and process data which describes an imaging
    # mass spectrometry (IMS) experiment. A single zarr store is created.

    get_CLI_args "$@"
    IMZML_IN="$INPUT/spraggins.ims.imzml"
    IBD_IN="$INPUT/spraggins.ims.ibd"
    ZARR_OUT="$OUTPUT/spraggins.ims.zarr"
    JSON_OUT="$OUTPUT/spraggins.ims.json"

    CLI_ARGS="--imzml_file $IMZML_IN --ibd_file $IBD_IN --ims_zarr $ZARR_OUT --ims_metadata $JSON_OUT"

    echo "Download and process IMS data..."

    SPRAGGINS_URL="https://vitessce-data.s3.amazonaws.com/source-data/spraggins"

    [ -e "$IMZML_IN" ] || \
        wget "$SPRAGGINS_URL/spraggins.ims.imzml" -O "$IMZML_IN"
    [ -e "$IBD_IN" ] || \
        wget "$SPRAGGINS_URL/spraggins.ims.ibd" -O "$IBD_IN"

    if [ -e "$ZARR_OUT" ]
    then
        echo "Skipping zarr -- output already exists: $ZARR_OUT"
    else
        echo 'Generating IMS zarr may take a while...'
        CMD="$BASE/python/imzml_reader.py $CLI_ARGS"
        echo "Running: $CMD"
        eval $CMD
    fi

    TILES_BASE='spraggins.images'
    TILES_PATH="$OUTPUT/$TILES_BASE"
    if [ -e "$TILES_PATH" ]
    then
        echo "Skipping tiling -- output already exists: $TILES_PATH"
    else
        if [ -e "$INPUT/spraggins.ome.tif" ]
        then
          echo "Not copying $INPUT/spraggins.ome.tif from s3 - already exists or testing"
        else
          aws s3 cp s3://vitessce-data/source-data/spraggins/spraggins.ome.tif "$INPUT/spraggins.ome.tif"
        fi
        RELEASE=${CLOUD_TARGET//vitessce-data\//}
        SERVER_URL="https://vitessce-data.storage.googleapis.com/$RELEASE/spraggins/"
        CMD='docker run --rm
            -e "SERVER_URL='$SERVER_URL'"
            -e "PREFIX=spraggins"
            -e "PYRAMID_TYPE=tiff"
            --mount "type=bind,src='$INPUT'/spraggins.ome.tif,destination=/input.ome.tif"
            --mount "type=bind,src='$OUTPUT',destination=/output_dir"
            --name tiler gehlenborglab/ome-tiff-tiler:v0.0.7'
        echo "Running: $CMD"
        eval $CMD
        # vitessce relies on this naming strategy, whereas the docker image is more general
        mv "$TILES_PATH/tiff.json" "$OUTPUT/spraggins.raster.json" || \
          sudo mv "$TILES_PATH/tiff.json" "$OUTPUT/spraggins.raster.json"
    fi
}

### Main

main "$@"
