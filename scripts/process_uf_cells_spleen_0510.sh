#!/usr/bin/env bash
set -o errexit

source activate vitessce-data-uf-cells-spleen-0510

pwd

snakemake \
    --cores 2 \
    --snakefile snakemake/uf-cells-spleen-0510/Snakefile \
    --directory snakemake/uf-cells-spleen-0510

