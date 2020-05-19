from os.path import join

configfile: 'config.yml'

SRC_DIR = "src"
DATA_DIR = "data"
RAW_DIR = join(DATA_DIR, "raw")
PROCESSED_DIR = join(DATA_DIR, "processed")

GLOBUS_IDS = config['annotations_spleen_0510']

CELL_ANNOTATIONS_URL = "https://vitessce-data.s3.amazonaws.com/source-data/annotations_spleen_0510/annotations_spleen_0510.csv"
CELLS_URL = "https://giygas.compbio.cs.cmu.edu/uf-processed.tar.xz"
CL_OBO_URL = "https://raw.githubusercontent.com/obophenotype/cell-ontology/master/cl.obo"

rule all:
    input:
        expand(join(PROCESSED_DIR, "{globus_id}.cells.json"), globus_id=GLOBUS_IDS),
        expand(join(PROCESSED_DIR, "{globus_id}.factors.json"), globus_id=GLOBUS_IDS),
        expand(join(PROCESSED_DIR, "{globus_id}.cell_sets.json"), globus_id=GLOBUS_IDS),

rule process_dataset:
    input:
        cells_arrow=join(RAW_DIR, "uf_processed", "{globus_id}", "cluster_marker_genes.arrow"),
        annotations_csv=join(RAW_DIR, "annotations_spleen_0510", "{globus_id}.csv"),
        cl_obo=join(RAW_DIR, "cl.obo")
    output:
        cells_json=join(PROCESSED_DIR, "{globus_id}.cells.json"),
        factors_json=join(PROCESSED_DIR, "{globus_id}.factors.json"),
        cell_sets_json=join(PROCESSED_DIR, "{globus_id}.cell_sets.json")
    params:
        script=join(SRC_DIR, "process_dataset.py")
    shell:
        '''
        python {params.script} \
            -ic {input.cells_arrow} \
            -ia {input.annotations_csv} \
            -ico {input.cl_obo} \
            -oc {output.cells_json} \
            -of {output.factors_json} \
            -ocs {output.cell_sets_json}
        '''

rule split_annotation_csv:
    input:
        join(RAW_DIR, "annotations_spleen_0510.csv")
    output:
        join(RAW_DIR, "annotations_spleen_0510", "{globus_id}.csv")
    params:
        script=join(SRC_DIR, "split_annotation_csv.py")
    shell:
        '''
        python {params.script} \
            -i {input} \
            -o {output} \
            -gid {wildcards.globus_id}
        '''

rule convert_h5ad_to_arrow:
    input:
        join(RAW_DIR, "uf_processed", "{globus_id}", "cluster_marker_genes.h5ad")
    output:
        join(RAW_DIR, "uf_processed", "{globus_id}", "cluster_marker_genes.arrow")
    params:
        script=join(SRC_DIR, "convert_h5ad_to_arrow.py")
    shell:
        '''
        python {params.script} \
            -i {input} \
            -o {output}
        '''

# Download CSV file containing cell type annotations.
rule download_cell_annotations_data:
    output:
        join(RAW_DIR, "annotations_spleen_0510.csv")
    params:
        file_url=CELL_ANNOTATIONS_URL
    shell:
        '''
        curl -L -o {output} {params.file_url}
        '''

# Extract contents of the TAR file.
rule untar_cells_data:
    input:
        join(RAW_DIR, "uf-processed.tar.xz")
    output:
        expand(
            join(RAW_DIR, "uf_processed", "{globus_id}", "cluster_marker_genes.h5ad"),
            globus_id=GLOBUS_IDS
        )
    shell:
        '''
        tar -xvzf {input} -C {RAW_DIR} \
        && rm -r {RAW_DIR}/uf_processed \
        && mv {RAW_DIR}/uf-processed {RAW_DIR}/uf_processed
        '''

# Download TAR file containing UMAP clustering data.
rule download_cells_data:
    output:
        join(RAW_DIR, "uf-processed.tar.xz")
    params:
        file_url=CELLS_URL
    shell:
        '''
        curl -L -o {output} {params.file_url}
        '''

rule download_cl_obo:
    output:
        join(RAW_DIR, "cl.obo")
    params:
        file_url=CL_OBO_URL
    shell:
        '''
        curl -L -o {output} {params.file_url}
        '''