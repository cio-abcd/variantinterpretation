process VEMBRANE_VEMBRANETABLE {
    tag "$meta.id"
    label 'process_low'

    conda "bioconda::vembrane=1.0.7"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/vembrane:1.0.1--pyhdfd78af_0':
        'biocontainers/vembrane:1.0.1--pyhdfd78af_0' }"

    input:
    tuple val(meta), path(vcf)
    val extraction_fields
    val header

    output:
    tuple val(meta), path("*.tsv"), emit: tsv
    path "versions.yml"           , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    bcftools index --tbi $vcf -o ${prefix}.ann.vcf.tbi
    vembrane table \\
        --output ${prefix}.tsv \\
        --header '$header' \\
        $args \\
        '$extraction_fields' \\
        $vcf

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        vembrane: \$(echo \$(vembrane --version 2>&1) | sed 's/^.*vembrane //; s/Using.*\$//' ))
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}.tsv
    touch ${prefix}.summary.html

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        vembrane: \$(echo \$(vembrane --version 2>&1) | sed 's/^.*vembrane //; s/Using.*\$//' ))
    END_VERSIONS
    """

}
