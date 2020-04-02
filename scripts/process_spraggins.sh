#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

main() {
    # Download and process data which describes an imaging
    # mass spectrometry (IMS) experiment. A single zarr store is created.

    get_CLI_args "$@"

    # IMS data
    IMS_IMZML_IN="$INPUT/spraggins.ims.imzml"
    IMS_IBD_IN="$INPUT/spraggins.ims.ibd"
    IMS_ZARR_OUT="$OUTPUT/spraggins.ims.zarr"
    IMS_JSON_OUT="$OUTPUT/spraggins.ims.raster.json"

    # MXIF data
    MXIF_TIFF_IN="$INPUT/spraggins.mxif.ome.tif"
    MXIF_TILES_OUT="$OUTPUT/spraggins.images"
    MXIF_JSON_OUT="$OUTPUT/spraggins.mxif.raster.json"

    # CLOUD SOURCE
    SOURCE_URL="https://vitessce-data.s3.amazonaws.com/source-data/spraggins"

    # CLOUD TARGET
    RELEASE=${CLOUD_TARGET//vitessce-data\//}
    SERVER_URL="https://vitessce-data.storage.googleapis.com/$RELEASE/spraggins"

    echo "Download and process IMS data..."

    [ -e "$IMS_IMZML_IN" ] || \
        wget "$SOURCE_URL/spraggins.ims.imzml" -O "$IMS_IMZML_IN"
    [ -e "$IMS_IBD_IN" ] || \
        wget "$SOURCE_URL/spraggins.ims.ibd" -O "$IMS_IBD_IN"

    if [ -e "$IMS_ZARR_OUT" ]
    then
        echo "Skipping zarr -- output already exists: $IMS_ZARR_OUT"
    else
        echo 'Generating IMS zarr may take a while...'
        CMD="$BASE/python/imzml_reader.py
            --imzml_file $IMS_IMZML_IN
            --ibd_file $IMS_IBD_IN
            --ims_zarr $IMS_ZARR_OUT
            --ims_metadata $IMS_JSON_OUT
            --zarr_store_url $SERVER_URL"
        echo "Running: $CMD"
        eval $CMD
    fi

    if [ -e "$MXIF_TILES_OUT"]
    then
        echo "Skipping tiling -- output already exists: $MXIF_TILES_OUT"
    else
        if [ -e "$MXIF_TIFF_IN" ]
        then
          echo "Not copying $MXIF_TIFF_IN from s3 - already exists or testing"
        else
          wget "$SOURCE_URL/spraggins.ome.tif" -O "$MXIF_TIFF_IN"
        fi
        CMD='docker run --rm
            -e "SERVER_URL='$SERVER_URL'/"
            -e "PREFIX=spraggins"
            -e "PYRAMID_TYPE=tiff"
            --mount "type=bind,src='$MXIF_TIFF_IN',destination=/input.ome.tif"
            --mount "type=bind,src='$OUTPUT',destination=/output_dir"
            --name tiler gehlenborglab/ome-tiff-tiler:v0.0.7'
        echo "Running: $CMD"
        eval $CMD
        # vitessce relies on this naming strategy, whereas the docker image is more general
        mv "$MXIF_TILES_OUT/tiff.json" "$MXIF_JSON_OUT" || \
          sudo mv "$MXIF_TILES_OUT/tiff.json" "$MXIF_JSON_OUT"
    fi
}

### Main

main "$@"
