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
}

### Main

main "$@"