process ONCOKB_ANNOTATOR_UKB {
    tag "$meta.id"
    label 'process_single'
    conda "conda-forge::python=3.9.18 conda-forge::requests==2.31.0 conda-forge::urllib3==1.26.8 conda-forge::kiwisolver==1.2.0"
    secret 'oncokb_token'

    input:
    tuple val(meta), path(variants_filtered_maf)

    output:
    tuple val(meta), path("*_oncokb_out.maf"), emit: oncokb_out
    //tuple val(meta), path("*_oncokb_annotation_stdout.log"), emit: log_oncokb

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    MafAnnotator.py -i ${variants_filtered_maf} -o ${prefix}_oncokb_out.maf -r GRCh38 -b \$oncokb_token
    """
}
