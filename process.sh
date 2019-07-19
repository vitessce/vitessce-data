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
    echo 'input:'
    ls -lh "$INPUT"/

    echo
    echo 'output:'
    ls -lh "$OUTPUT"/

    sh ./scripts/process_linnarsson.sh
    sh ./scripts/process_dries.sh
    sh ./scripts/process_wang.sh

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

export BASE=`dirname "$0"`
export S3_TARGET=`cat s3_target.txt`

if [[ "$CI" = 'true' ]]
then
    wget() {
        die "Add fixture to 'fake-files/input': Should not 'wget' in test run: 'wget $*'"
    }
    FILES="$BASE/fake-files"
else
    FILES="$BASE/big-files"
fi

export INPUT="$FILES/input"
export OUTPUT="$FILES/output"

[ -d "$INPUT" ] || mkdir "$INPUT"
[ -d "$OUTPUT" ] || mkdir "$OUTPUT"

### Main

main
