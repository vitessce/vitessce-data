#!/usr/bin/env bash
source ./scripts/utils.sh

set -o errexit

main() {
    # Download and process data which describes cell locations, boundaries,
    # and gene expression levels. Multiple JSON output files are produced:
    # The files are redudant, but this reduces the processing that needs
    # to be done on the client-side.

    CSV_IN="$INPUT/mermaid.csv"
    PNG_IN="$INPUT/mermaid.png"

    CLI_ARGS="--csv_file $CSV_IN"
    add_arg 'cells' 'mermaid'
    add_arg 'molecules' 'mermaid'
    add_arg 'images' 'mermaid'

    echo "Download and process cells..."

    [ -e "$CSV_IN" ] || \
    (wget "$MERMAID_URL/data.csv.gz" -O "$CSV_IN.gz" && gunzip -df "$CSV_IN")

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
    if [ -e "TILE_PATH" ]
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
        return
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

main
