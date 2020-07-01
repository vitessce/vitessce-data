#!/usr/bin/env bash
set -o errexit

. ./scripts/utils.sh

DATASET='satija'

main() {
    get_CLI_args "$@"

    # The variables $BASE, $INPUT, $OUTPUT, $CLOUD_TARGET
    # come from running the get_CLI_args line above.

    SNAKEMAKE_CMD="snakemake
        --cores 1
        --snakefile $BASE/snakemake/$DATASET/Snakefile
        --directory $BASE/snakemake/$DATASET
        --config INPUT=$INPUT OUTPUT=$OUTPUT CLOUD_TARGET=$CLOUD_TARGET"
    
    eval $SNAKEMAKE_CMD --dryrun
    eval $SNAKEMAKE_CMD
}

### Main

main "$@"
