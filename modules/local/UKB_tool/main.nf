process UKB_TOOL {
    tag "$meta.id"
    conda "conda-forge::python=3.9.18 conda-forge::pandas=2.1.0 conda-forge::openpyxl=3.1.2 conda-forge::requests"
    //errorStrategy 'ignore'
    maxForks 1

    cpus 1
    memory "200 GB"
    time 5.h

    input:
    tuple val(meta), path(tsv)
    val(library_type)

    output:
    tuple val(meta), path("${meta.id}_tmb.csv")                     , emit: tmb
    tuple val(meta), path("${meta.id}_removed_variants.shard_*.xlsx")       , emit: removed_variants
    tuple val(meta), path("${meta.id}_annotated_variants.xlsx"), emit: annotated_variants
    path "versions.yml"                                    , emit: versions

    script:
    def prefix = "${meta.id}"
    """
    WXS_process_variants_filter.py \\
        'paired' \\
        ${library_type} \\
        ${tsv} \\
        --tmb_output ${prefix}_tmb.csv \\
        --outfile  ${prefix}_filtered_variants.maf \\
        --annotated_outfile  ${prefix}_annotated_variants.xlsx \\
        --removed_variants ${prefix}_removed_variants | tee log_${prefix}.log

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}

process UKB_TOOL_ONCOKB {
    tag "$meta.id"
    conda "conda-forge::python=3.9.18 conda-forge::pandas=2.1.0 conda-forge::openpyxl=3.1.2 conda-forge::requests"
    //errorStrategy 'ignore'
    secret 'oncokb_token'
    maxForks 1

    cpus 1
    memory "200 GB"
    time 5.h

    input:
    tuple val(meta), path(tsv)
    val(library_type)

    output:
    tuple val(meta), path("${meta.id}_tmb.csv")                     , emit: tmb
    tuple val(meta), path("${meta.id}_removed_variants.shard_*.xlsx")       , emit: removed_variants
    tuple val(meta), path("${meta.id}_annotated_variants.xlsx"), emit: annotated_variants
    path "versions.yml"                                    , emit: versions

    script:
    def prefix = "${meta.id}"
    """
    WXS_process_variants_filter.py \\
        'paired' \\
        ${library_type} \\
        ${tsv} \\
        --use_oncokb_token \$oncokb_token \\
        --tmb_output ${prefix}_tmb.csv \\
        --outfile  ${prefix}_filtered_variants.maf \\
        --annotated_outfile  ${prefix}_annotated_variants.xlsx \\
        --removed_variants ${prefix}_removed_variants | tee log_${prefix}.log

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}

