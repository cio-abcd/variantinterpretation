process DATAVZRD {
    tag "$meta.id"
    label 'process_single'

    conda "conda-forge::datavzrd=2.22.0"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/datavzrd:2.23.2' :
        'quay.io/biocontainers/datavzrd:2.23.2' }"

    input:
    tuple val(meta), path(split_tsv), path(datavzrd_config_rend)

    output:
    tuple val(meta), path('report_*')     , emit: report
    path "versions.yml"                   , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    datavzrd $args \\
        $datavzrd_config_rend \\
        --output report_${prefix}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        datavzrd: \$(echo \$(datavzrd --version 2>&1) | sed 's/^.*datavzrd //; s/Using.*\$//' ))
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        datavzrd: \$(echo \$(datavzrd --version 2>&1) | sed 's/^.*datavzrd //; s/Using.*\$//' ))
    END_VERSIONS
    """
}
