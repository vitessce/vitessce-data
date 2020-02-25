#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

main() {
    # Download and process data which describes cell locations,
    # and gene expression levels. Multiple JSON output files are produced:
    # The files are redudant, but this reduces the processing that needs
    # to be done on the client-side.

    get_CLI_args "$@"
    CYTOKIT_IN="$INPUT/cytokit.csv"

    CLI_ARGS="--cytokit $CYTOKIT_IN"
    add_CLI_ARGS 'cells' 'cytokit'

    echo "Download and process cells..."

    if [ ! -e "$CYTOKIT_IN" ]
    then
        echo 'TODO'
        exit 1
        # wget "https://cells.ucsc.edu/mouse-organogenesis/tSNE.coords.tsv.gz" -O "$TSV_TSNE_IN.gz"
        # gunzip -df "$TSV_TSNE_IN"
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
