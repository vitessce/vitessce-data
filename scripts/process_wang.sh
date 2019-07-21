#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

main() {
    # Download and process data which describes cell locations, boundaries,
    # and gene expression levels. Multiple JSON output files are produced:
    # The files are redudant, but this reduces the processing that needs
    # to be done on the client-side.

    get_CLI_args "$@"

    CSV_IN="$INPUT/mermaid.csv"
    PNG_IN="$INPUT/mermaid.png"

    CLI_ARGS="--csv_file $CSV_IN"
    add_CLI_ARGS 'cells' 'mermaid'
    add_CLI_ARGS 'molecules' 'mermaid'
    add_CLI_ARGS 'images' 'mermaid'

    echo "Download and process cells..."

    if [ -e "$CSV_IN" ]
    then
        wget "$MERMAID_URL/data.csv.gz" -O "$CSV_IN.gz"
        gunzip -df "$CSV_IN"
    fi

    [ -e "$PNG_IN" ] || \
        wget "$MERMAID_URL/bg.png" -O "$PNG_IN"

    IMAGE_OUT="$OUTPUT/mermaid.png"
    if [ -e "$IMAGE_OUT" ]
    then
        echo "Skipping image -- output already exists: $IMAGE_OUT"
    else
        cp $PNG_IN $OUTPUT/mermaid.png
    fi

    TILE_BASE='mermaid.images'
    TILE_PATH="$OUTPUT/$TILE_BASE"
    if [ -e "$OUTPUT/mermaid.images/info.json" ]
    then
        echo "Skipping tile -- output already exists: $TILE_PATH"
    else
        URL_PREFIX="https://s3.amazonaws.com/$S3_TARGET"
        mkdir -p "$OUTPUT/mermaid.images/"
        JSON_STRING='{ "type": "image", "url": "'$URL_PREFIX'/mermaid.png" }'
        echo $JSON_STRING > "$OUTPUT/mermaid.images/info.json"
    fi

    CELLS_OUT="$OUTPUT/mermaid.cells.json"
    if [ -e "$CELLS_OUT" ]
    then
        echo "Skipping cells -- output already exists: $CELLS_OUT"
    else
        echo 'Generating cells JSON may take a while...'
        CMD="$BASE/python/mermaid_csv_reader.py $CLI_ARGS"
        echo "Running: $CMD"
        eval $CMD
    fi
}

### Globals

MERMAID_URL='https://jef.works/MERmaid'

### Main

get_CLI_args "$@"
main
