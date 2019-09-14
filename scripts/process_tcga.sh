#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

main() {
    get_CLI_args "$@"

    process_tcga_images
}

### Functions

process_tcga_images() {
    # Download and process svs data from and tile image.

    IMAGE_IN="$INPUT/sample.svs"
    TCGA_URL="https://vitessce-data.s3.amazonaws.com/source-data/tcga/"
    JSON_OUT="$OUTPUT/tcga.images.json"

    if [ -e "$JSON_OUT" ]
    then
        echo "Skipping big image generation -- output already exists: $JSON_OUT"
    else
        echo "Download and generate big images..."

        [ -e "$IMAGE_IN" ] || \
            wget "$TCGA_URL/TCGA-AA-3495-01Z-00-DX1.67DEE36B-724E-4B4F-B3A9-B4E8CCCEFA80.svs" -O "$IMAGE_IN"

        CMD="$BASE/python/tcga_img_reader.py
            --json_file $JSON_OUT"
        echo "Running: $CMD"
        $CMD
    fi

    TILES_BASE='tcga.tiles'
    TILES_PATH="$OUTPUT/$TILES_BASE"
    if [ -e "$TILES_PATH" ]
    then
        echo "Skipping tiling -- output already exists: $TILES_PATH"
    else
        mkdir $TILES_PATH
        URL_PREFIX="https://s3.amazonaws.com/$S3_TARGET/tcga/$TILES_BASE"

        CMD='docker run --rm
            -e "PREFIX=tcga"
            --mount "type=bind,src='$INPUT'/sample.svs,destination=/input.svs"
            --mount "type=bind,src='$TILES_PATH',destination=/output_dir"
            --name tiler thomaslchan/svs-tiff-tiler:v0.0.1'
        echo "Running: $CMD"
        eval $CMD
    fi
}

### Main

main "$@"
