#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

main() {
    # Download and process data which describes cell locations, boundaries,
    # and gene expression levels. Multiple JSON output files are produced:
    # The files are redudant, but this reduces the processing that needs
    # to be done on the client-side.

    get_CLI_args "$@"

    JSON_IN="$INPUT/giotto.cells.json"

    CLI_ARGS="--json_file $JSON_IN"
    add_CLI_ARGS 'cells' 'giotto'
    add_CLI_ARGS 'factors' 'giotto'

    echo "Download and process cells..."

    [ -e "$JSON_IN" ] || \
        wget "https://vitessce-data.s3.amazonaws.com/source-data/giotto/giotto.cells.json" -O "$JSON_IN"

    JSON_OUT="$OUTPUT/giotto.cells.json"
    if [ -e "$JSON_OUT" ]
    then
        echo "Skipping cells -- output already exists: $JSON_OUT"
    else
        echo 'Generating cells JSON may take a while...'
        CMD="$BASE/python/giotto_json_reader.py $CLI_ARGS"
        echo "running: $CMD"
        eval $CMD
    fi
}

### Main

main "$@"
