#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

main() {
    # Download and process data which describes cell locations, boundaries,
    # and gene expression levels. Multiple JSON output files are produced:
    # The files are redudant, but this reduces the processing that needs
    # to be done on the client-side.

    get_CLI_args "$@"

    CSV_IN="$INPUT/wang.csv"
    PNG_IN="$INPUT/wang.png"

    CLI_ARGS="--csv_file $CSV_IN"
    add_CLI_ARGS 'cells' 'wang'
    add_CLI_ARGS 'molecules' 'wang'
    add_CLI_ARGS 'genes' 'wang'
    add_CLI_ARGS 'images' 'wang'

    echo "Download and process cells..."

    WANG_URL='https://github.com/JEFworks/MERmaid/blob/ac5b204f9645dd5e2a4ed696a9308b25938344fe/public'

    if [ ! -e "$CSV_IN" ]
    then
        wget "$WANG_URL/data.csv.gz?raw=true" -O "$CSV_IN.gz"
        gunzip -df "$CSV_IN"
    fi

    [ -e "$PNG_IN" ] || \
        wget "$WANG_URL/bg.png?raw=true" -O "$PNG_IN"

    IMAGE_OUT="$OUTPUT/wang.png"
    if [ -e "$IMAGE_OUT" ]
    then
        echo "Skipping image -- output already exists: $IMAGE_OUT"
    else
        cp $PNG_IN $OUTPUT/wang.png
    fi

    TILE_BASE='wang.images'
    TILE_PATH="$OUTPUT/$TILE_BASE"
    if [ -e "$OUTPUT/wang.images/info.json" ]
    then
        echo "Skipping tile -- output already exists: $TILE_PATH"
    else
        URL_PREFIX="https://s3.amazonaws.com/$CLOUD_TARGET"
        mkdir -p "$TILE_PATH"
        JSON_STRING='{ "type": "image", "url": "'$URL_PREFIX'/wang.png" }'
        echo $JSON_STRING > "$TILE_PATH/info.json"
    fi

    CELLS_OUT="$OUTPUT/wang.cells.json"
    if [ -e "$CELLS_OUT" ]
    then
        echo "Skipping cells -- output already exists: $CELLS_OUT"
    else
        echo 'Generating cells JSON may take a while...'
        CMD="$BASE/python/wang_csv_reader.py $CLI_ARGS"
        echo "Running: $CMD"
        eval $CMD
    fi
}

### Main

main "$@"
