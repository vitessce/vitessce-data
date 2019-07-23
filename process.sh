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
    echo
    echo 'Input:'
    ls -lh "$INPUT"/

    echo
    echo 'Output:'
    ls -lh "$OUTPUT"/

    echo
    echo "Processing Linnarsson data"
    ./scripts/process_linnarsson.sh -b "$BASE" -i "$INPUT/linnarsson" -o "$OUTPUT/linnarsson" -t "$S3_TARGET"

    echo
    echo "Processing Dries data"
    ./scripts/process_dries.sh -b "$BASE" -i "$INPUT/dries" -o "$OUTPUT/dries" -t "$S3_TARGET"

    echo
    echo "Processing Wang data"
    ./scripts/process_wang.sh -b "$BASE" -i "$INPUT/wang" -o "$OUTPUT/wang" -t "$S3_TARGET"

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
[ -d "$INPUT/linnarsson" ] || mkdir "$INPUT/linnarsson"
[ -d "$INPUT/dries" ] || mkdir "$INPUT/dries"
[ -d "$INPUT/wang" ] || mkdir "$INPUT/wang"

[ -d "$OUTPUT" ] || mkdir "$OUTPUT"
[ -d "$OUTPUT/linnarsson" ] || mkdir "$OUTPUT/linnarsson"
[ -d "$OUTPUT/dries" ] || mkdir "$OUTPUT/dries"
[ -d "$OUTPUT/wang" ] || mkdir "$OUTPUT/wang"


### Main

main
