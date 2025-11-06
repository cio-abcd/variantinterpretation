process UKB_TOOL {
    tag "$meta.id"
    conda "conda-forge::python=3.9.18 conda-forge::pandas=2.1.0 conda-forge::openpyxl=3.1.2 conda-forge::requests"
    //errorStrategy 'ignore'
    secret 'oncokb_token'

    cpus 1
    memory "40 GB"

    input:
    tuple val(meta), path(tsv)
    val(refseq_list)
    val(variantDBi)
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
        ${refseq_list} \\
        ${variantDBi} \\
        ${tsv} \\
        --tmb_output ${prefix}_tmb.csv \\
        --outfile  ${prefix}_filtered_variants.maf \\
        --removed_variants ${prefix}_removed_variants | tee log_${prefix}.log

    MafAnnotator.py -i ${prefix}_filtered_variants.maf -o ${prefix}_oncokb_out.maf -r GRCh38 -b \$oncokb_token

    WXS_annotation.py \\
        --onco_maf ${prefix}_oncokb_out.maf \\
        --annotated_outfile ${prefix}_annotated_variants.xlsx > log_${prefix}.log

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}

