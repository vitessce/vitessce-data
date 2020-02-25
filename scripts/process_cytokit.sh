#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

main() {
    # Download and process CSV which describes cell locations and CODEX data.

    get_CLI_args "$@"
    CYTOKIT_IN="$INPUT/cytokit.csv"

    CLI_ARGS="--cytokit $CYTOKIT_IN"
    add_CLI_ARGS 'cells' 'cytokit'

    echo "Download and process cells..."

    if [ ! -e "$CYTOKIT_IN" ]
    then
        wget "https://vitessce-data.s3.amazonaws.com/source-data/cytokit/cytokit.csv" -O "$CYTOKIT_IN"
    fi

    CELLS_OUT="$OUTPUT/cytokit.cells.json"
    if [ -e "$CELLS_OUT" ]
    then
        echo "Skipping cells -- output already exists: $CELLS_OUT"
    else
        echo 'Generating cells JSON may take a while...'
        CMD="$BASE/python/cytokit_reader.py $CLI_ARGS"
        echo "Running: $CMD"
        eval $CMD
    fi
}

### Main

main "$@"
