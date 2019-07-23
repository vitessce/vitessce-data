#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

main() {
    # Download and process data which describes cell locations,
    # and gene expression levels. Multiple JSON output files are produced:
    # The files are redudant, but this reduces the processing that needs
    # to be done on the client-side.

    get_CLI_args "$@"

    # EXPRESSION_TSV_IN="$INPUT/cao.expression.tsv"
    #
    # CLI_ARGS="--tsv_file $EXPRESSION_TSV_IN"
    # add_CLI_ARGS 'cells' 'cao'

    echo "Download and process cells..."

    # Expression matrix, with 2M cell columns, is too big for me to unzip right now.
    # It looks like this:
    #
    # gene	sci3-me-001.GTCGGAGTTTGAGGTAGAA	sci3-me-001.ATTAGTCTGTGTATAATACG
    # ENSMUSG00000051951.5|Xkr4	0	0
    # ENSMUSG00000103377.1|Gm37180	0	0
    # ENSMUSG00000104017.1|Gm37363	0	0

    # if [ ! -e "$EXPRESSION_TSV_IN" ]
    # then
    #     wget "https://cells.ucsc.edu/mouse-organogenesis/exprMatrix.tsv.gz" -O "$EXPRESSION_TSV_IN.gz"
    #     gunzip -df "$EXPRESSION_TSV_IN"
    # fi

    COORDS_TSV_IN="$INPUT/cao.coords.tsv"

    if [ ! -e "$COORDS_TSV_IN" ]
    then
        wget "https://cells.ucsc.edu/mouse-organogenesis/tSNE.coords.tsv.gz" -O "$COORDS_TSV_IN.gz"
        gunzip -df "$COORDS_TSV_IN"
    fi

    META_TSV_IN="$INPUT/cao.meta.tsv"

    if [ ! -e "$META_TSV_IN" ]
    then
        wget "https://cells.ucsc.edu/mouse-organogenesis/meta.tsv" -O "$META_TSV_IN"
    fi

    # CELLS_OUT="$OUTPUT/cao.cells.json"
    # if [ -e "$CELLS_OUT" ]
    # then
    #     echo "Skipping cells -- output already exists: $CELLS_OUT"
    # else
    #     echo 'Generating cells JSON may take a while...'
    #     CMD="$BASE/python/cao_tsv_reader.py $CLI_ARGS"
    #     echo "Running: $CMD"
    #     echo 'TODO!!!'
    #     # eval $CMD
    # fi
}

### Main

main "$@"
