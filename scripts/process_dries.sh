#!/usr/bin/env bash
source ./scripts/utils.sh

set -o errexit

main() {
    # Download and process data which describes cell locations, boundaries,
    # and gene expression levels. Multiple JSON output files are produced:
    # The files are redudant, but this reduces the processing that needs
    # to be done on the client-side.

    JSON_IN="$INPUT/giotto.cells.json"

    CLI_ARGS="--json_file $JSON_IN"
    add_arg 'cells' 'giotto'
    add_arg 'factors' 'giotto'

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
    eval $CMD
}

### Globals

GIOTTO_URL='https://vitessce-data.s3.amazonaws.com/source-data/giotto'

### Main

main
