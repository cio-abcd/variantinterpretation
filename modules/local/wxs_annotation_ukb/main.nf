process WXS_ANNOTATION_UKB {
    tag "$meta.id"
    //label 'process_single'
    cpus 1
    memory "40 GB"
    conda "conda-forge::python=3.9.18 conda-forge::pandas=2.1.0 conda-forge::openpyxl=3.1.2"

    input:
    tuple val(meta), path(onco_maf)

    output:
    tuple val(meta), path("*_annotated_variants.xlsx")     , emit: annotated_variants
    tuple val(meta), path("log_*.log")                     , emit: log_annotated_variants
    path "versions.yml"                                    , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    WXS_annotation.py \\
        --onco_maf ${onco_maf} \\
        --annotated_outfile ${prefix}_annotated_variants.xlsx > log_${prefix}.log

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
