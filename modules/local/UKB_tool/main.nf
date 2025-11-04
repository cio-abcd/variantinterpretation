process UKB_FILTER {
    tag "$meta.id"
    conda "conda-forge::python=3.9.18 conda-forge::pandas=2.1.0 conda-forge::openpyxl=3.1.2"
    errorStrategy 'ignore'

    cpus 1
    memory "20 GB"

    input:
    tuple val(meta), path(tsv)
    val(refseq_list)
    val(variantDBi)
    val(library_type)

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
    WXS_process_variants_filter.py \\
        --vembrane_table ${tsv} \\
        --refseq_list ${refseq_list} \\
        --variant_DBi ${variantDBi} \\
        --analysis ${library_type} \\
        --tmb_output ${prefix}_tmb.csv \\
        --outfile  ${prefix}_filtered_variants.maf \\
        --removed_variants ${prefix}_removed_variants.xlsx | tee log_${prefix}.log

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}

process ONCOKB_ANNOTATOR_UKB {
    tag "$meta.id"
    label 'process_single'
    conda "conda-forge::python=3.9.18 conda-forge::requests==2.31.0 conda-forge::urllib3==1.26.8 conda-forge::kiwisolver==1.2.0"
    secret 'oncokb_token'
    errorStrategy 'ignore'

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

workflow UKB_tool {
    take:
    ch_tsv
    refseq_list
    variantDBi
    ch_library_type

    main:

	filtout = UKB_FILTER(ch_tsv, refseq_list, variantDBi, ch_library_type)
	oncokb_out = ONCOKB_ANNOTATOR_UKB(
		filtout.variants_filtered_maf
	)

	tmb = filtout.tmb.map{it -> it[1]}
	annotated_variants = WXS_ANNOTATION_UKB(oncokb_out.oncokb_out).annotated_variants

	emit:
	annotated_variants
    tmb
}
