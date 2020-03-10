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
    INPUT="$FILES/input"
    OUTPUT="$FILES/output"

    for DATASET in cytokit linnarsson dries wang cao spraggins spraggins; do
        INPUT_SET="$INPUT/$DATASET"
        OUTPUT_SET="$OUTPUT/$DATASET"
        [ -d "$INPUT_SET" ] || mkdir -p "$INPUT_SET"
        [ -d "$OUTPUT_SET" ] || mkdir -p "$OUTPUT_SET"

        echo
        echo "Processing $DATASET ..."
        ./scripts/process_$DATASET.sh \
            -b "$BASE" \
            -i "$INPUT_SET" \
            -o "$OUTPUT_SET" \
            -t "$CLOUD_TARGET"
    done

    echo 'AWS:'
    if [[ "$CI" = 'true' ]] || [[ "$NO_PUSH" = 'true' ]]
    then
        echo 'CI: Skip push to AWS and GCS'
    else
        aws s3 cp --exclude "$OUTPUT/*.ome.tif*" --exclude "$OUTPUT/*.zarr/*" --recursive "$OUTPUT" s3://"$CLOUD_TARGET"
        gsutil -m cp -r "$OUTPUT/spraggins/spraggins.images" "gs://$CLOUD_TARGET/spraggins/spraggins.images"
        gsutil -m cp -r "$OUTPUT/linnarsson/linnarsson.images.zarr" "gs://$CLOUD_TARGET/linnarsson/linnarsson.images.zarr"
    fi
}

### Globals

BASE=`pwd`
CLOUD_TARGET=`cat cloud_target.txt`

if [[ "$CI" = 'true' ]]
then
    wget() {
        die "Add fixture to 'fake-files/input': Should not 'wget' in test run: 'wget $*'"
    }
    FILES="$BASE/fake-files"
else
    FILES="$BASE/big-files"
fi

### Main

main "$FILES"
