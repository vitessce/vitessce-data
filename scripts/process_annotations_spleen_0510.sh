#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

main() {
    # Download and process data which describes cell locations, boundaries,
    # and gene expression levels. Multiple JSON output files are produced:
    # The files are redudant, but this reduces the processing that needs
    # to be done on the client-side.

    get_CLI_args "$@"

    DATA_TITLE='annotations_spleen_0510'
    CSV_IN="$INPUT/annotations_spleen_0510.csv"

    echo "Download and process cells..."

    [ -e "$CSV_IN" ] || \
        wget "https://vitessce-data.s3.amazonaws.com/source-data/annotations_spleen_0510/annotations_spleen_0510.csv" -O "$CSV_IN"

    
    echo 'Generating factors JSON...'
    CMD="$BASE/python/annotations_csv_reader.py --csv_file $CSV_IN --factors_file $OUTPUT/HBM472.NTNN.543.factors.json --dataset_id HBM472.NTNN.543"
    echo "Running: $CMD"
    eval $CMD

    CMD="$BASE/python/annotations_csv_reader.py --csv_file $CSV_IN --factors_file $OUTPUT/HBM556.QMSM.776.factors.json --dataset_id HBM556.QMSM.776"
    echo "Running: $CMD"
    eval $CMD

    CMD="$BASE/python/annotations_csv_reader.py --csv_file $CSV_IN --factors_file $OUTPUT/HBM396.RPRR.624.factors.json --dataset_id HBM396.RPRR.624"
    echo "Running: $CMD"
    eval $CMD

    CMD="$BASE/python/annotations_csv_reader.py --csv_file $CSV_IN --factors_file $OUTPUT/HBM984.GRBB.858.factors.json --dataset_id HBM984.GRBB.858"
    echo "Running: $CMD"
    eval $CMD

    CMD="$BASE/python/annotations_csv_reader.py --csv_file $CSV_IN --factors_file $OUTPUT/HBM336.FWTN.636.factors.json --dataset_id HBM336.FWTN.636"
    echo "Running: $CMD"
    eval $CMD
}

### Main

main "$@"
