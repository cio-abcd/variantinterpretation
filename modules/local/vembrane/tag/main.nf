process VEMBRANE_TAG {
    tag "$meta.id"
    label 'process_low'

    conda "bioconda::vembrane=1.0.1"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/vembrane:1.0.1--pyhdfd78af_0':
        'quay.io/biocontainers/vembrane:1.0.1--pyhdfd78af_0' }"

    input:
    tuple val(meta), path(vcf)
    val tagargs

    output:
    tuple val(meta), path("*.vcf"), emit: vcf
    path "versions.yml"           , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    vembrane tag \\
        --output ${prefix}_tag.vcf \\
        --output-fmt vcf \\
        $tagargs \\
        $args \\
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
