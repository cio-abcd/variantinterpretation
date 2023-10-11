process VCFCHECKS {
    tag "$meta.id"
    label 'process_single'
    conda "conda-forge::python=3.9.15 conda-forge::pandas=2.0.3"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mulled-v2-0594c09780adaaa41fe60b1869ba41c8905a0c98:24a8102d6795963b77f04bb83cc82c081e4a2adc-0' :
        'biocontainers/mulled-v2-0594c09780adaaa41fe60b1869ba41c8905a0c98:24a8102d6795963b77f04bb83cc82c081e4a2adc-0' }"

    input:
    tuple val(meta), path(vcf), path (stats)

    output:
    path("*_warnings.txt") , emit: warnings

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    check_vcf.py \\
        --meta_id $meta.id \\
        --vcf_in $vcf \\
        --bcftools_stats_in $stats \\
        --warnings_out ${prefix}_warnings.txt \\
        $args
    """
}
