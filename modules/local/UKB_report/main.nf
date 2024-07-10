process UKB_REPORT {
    tag "$sample_name"
    label 'process_single'
    conda "conda-forge::python=3.9.18 conda-forge::pandas=2.1.0 conda-forge::openpyxl=3.1.2"
   
    input:
    tuple val(sample_name), path(tsv)
    val(refseq_list)
    val(variantDBi)

    output:
    path("${sample_name}_final_processed.xlsx")  , emit: final_xlsx
    path("${sample_name}_removed_variants.xlsx") , emit: removed_variants
    path("log_${sample_name}.log")               , emit: log
    path "versions.yml"                          , emit: versions

    //when:
    //task.ext.when == null || task.ext.when

    script:
    """  
    WES_varianten_v1_unix.py \\
        --vembrane_table ${tsv} \\
        --refseq_list ${refseq_list} \\
        --variant_DBi ${variantDBi} \\
        --outfile  ${sample_name}_final_processed.xlsx \\
        --removed_variants ${sample_name}_removed_variants.xlsx > log_${sample_name}.log
    
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
