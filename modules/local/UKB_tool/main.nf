process UKB_FILTER {
    tag "$meta.id"
    conda "conda-forge::python=3.9.18 conda-forge::pandas=2.1.0 conda-forge::openpyxl=3.1.2"
    errorStrategy 'ignore'

    cpus 1
    memory "40 GB"

    input:
    tuple val(meta), path(tsv)
    val(refseq_list)
    val(variantDBi)
    val(library_type)

    output:
    tuple val(meta), path("*_tmb.csv")                     , emit: tmb
    tuple val(meta), path("*_removed_variants.xlsx")       , emit: removed_variants
    tuple val(meta), path("log_*.log")                     , emit: log
    tuple val(meta), path("*_annotated_variants.xlsx"), emit: annotated_variants
    path "versions.yml"                                    , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    WXS_process_variants_filter.py \\
        --vembrane_table ${tsv} \\
        --refseq_list ${refseq_list} \\
        --variant_DBi ${variantDBi} \\
        --analysis ${library_type} \\
        --tmb_output ${prefix}_tmb.csv \\
        --outfile  ${prefix}_filtered_variants.maf \\
        --removed_variants ${prefix}_removed_variants.xlsx | tee log_${prefix}.log

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

workflow UKB_tool {
    take:
    ch_tsv
    refseq_list
    variantDBi
    ch_library_type

    main:

	/*
	filtout = UKB_FILTER(ch_tsv, refseq_list, variantDBi, ch_library_type)
	oncokb_out = ONCOKB_ANNOTATOR_UKB(
		filtout.variants_filtered_maf
	)
	*/
	filtout = UKB_FILTER(ch_tsv, refseq_list, variantDBi, ch_library_type)
	tmb = filtout.tmb.map{it -> it[1]}
	annotated_variants = filtout.annotated_variants

	emit:
	annotated_variants
    tmb
}
