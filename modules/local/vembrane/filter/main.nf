process VEMBRANE_FILTER {
    tag "$meta.id"
    label 'process_low'

    conda "bioconda::vembrane=1.0.6"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/vembrane:1.0.6--pyhdfd78af_0':
        'biocontainers/vembrane:1.0.6--pyhdfd78af_0' }"

    input:
    tuple val(meta), path(vcf)
    each filter

    output:
    tuple val(filtmeta), path("*.vcf") , emit: vcf
    path "versions.yml"                , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    filtmeta = [:]
    filtmeta.id = "${meta.id}_${filter}"

    """
    vembrane filter \\
        --output ${prefix}_${filter}.vcf \\
        $args \\
        '"$filter" in FILTER' \\
        $vcf

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        vembrane: \$(echo \$(vembrane --version 2>&1) | sed 's/^.*vembrane //; s/Using.*\$//' ))
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}.vcf

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        vembrane: \$(echo \$(vembrane --version 2>&1) | sed 's/^.*vembrane //; s/Using.*\$//' ))
    END_VERSIONS
    """

}
