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

    for DATASET in linnarsson dries wang cao spraggins vanderbilt; do
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
            -t "$S3_TARGET"
    done

    echo 'AWS:'
    if [[ "$CI" = 'true' ]] || [[ "$NO_PUSH" = 'true' ]]
    then
        echo 'CI: Skip push to AWS and GCS'
    else
        # Exclude the *HUGE* PNGs in the base directory:
        # The tiles for S3 are in subdirectories;
        # We keep the PNGs around because it takes a long time to generate them.
        TILES_BASE='vanderbilt.images'
        aws s3 cp --exclude "$OUTPUT/*.ome.tif*" --recursive "$OUTPUT" s3://"$S3_TARGET"
        gsutil cp "$OUTPUT/vanderbilt/$TILES_BASE/*.ome.tif*" gs://vitessce-data/$TILES_BASE
    fi
}

### Globals

BASE=`pwd`
S3_TARGET=`cat s3_target.txt`

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
