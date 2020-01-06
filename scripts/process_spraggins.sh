#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

main() {
    # Download and process data which describes cell locations, boundaries,
    # and gene expression levels. Multiple JSON output files are produced:
    # The files are redudant, but this reduces the processing that needs
    # to be done on the client-side.

    get_CLI_args "$@"

    IMZML_IN="$INPUT/spraggins.imzml"
    IBD_IN="$INPUT/spraggins.ibd"

    CLI_ARGS="--imzml_file $IMZML_IN --ibd_file $IBD_IN"
    add_CLI_ARGS 'ims' 'spraggins'

    echo "Download and process IMS data..."

    # SPRAGGINS_URL "https://vitessce-data.s3.amazonaws.com/source-data/spraggins"
    SPRAGGINS_URL="http://localhost:8000"

    [ -e "$IMZML_IN" ] || \
        wget "$SPRAGGINS_URL/VAN0001-RK-1-21-IMS.imzML" -O "$IMZML_IN"
    [ -e "$IBD_IN" ] || \
        wget "$SPRAGGINS_URL/VAN0001-RK-1-21-IMS.ibd" -O "$IBD_IN"

    
    ZARR_OUT="$OUTPUT/spraggins.zarr"
    if [ -e "$ZARR_OUT" ]
    then
        echo "Skipping zarr -- output already exists: $ZARR_OUT"
    else
        echo 'Generating cells JSON may take a while...'
        CMD="$BASE/python/imzml_reader.py $CLI_ARGS"
        echo "Running: $CMD"
        eval $CMD
    fi
}

### Main

main "$@"