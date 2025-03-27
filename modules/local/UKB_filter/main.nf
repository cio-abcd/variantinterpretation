process UKB_FILTER {
    tag "$meta.id"
    label 'process_single'
    conda "conda-forge::python=3.9.18 conda-forge::pandas=2.1.0 conda-forge::openpyxl=3.1.2"
   
    input:
    tuple val(meta), path(tsv)
    val(refseq_list)
    val(variantDBi)

    output:
    tuple val(meta), path("*_tmb.csv")                     , emit: tmb
    tuple val(meta), path("*_filtered_variants.maf")       , emit: variants_filtered_maf
    tuple val(meta), path("*_removed_variants.xlsx")       , emit: removed_variants
    tuple val(meta), path("log_*.log")                     , emit: log
    path "versions.yml"                                    , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """  
    WXS_process_variants_filter_tmb.py \\
        --vembrane_table ${tsv} \\
        --refseq_list ${refseq_list} \\
        --variant_DBi ${variantDBi} \\
        --tmb_output ${prefix}_tmb.csv \\
        --outfile  ${prefix}_filtered_variants.maf \\
        --removed_variants ${prefix}_removed_variants.xlsx > log_${prefix}.log
    
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
