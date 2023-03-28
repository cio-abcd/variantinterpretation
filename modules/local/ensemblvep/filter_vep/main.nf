process ENSEMBLVEP_FILTER {
    tag "$meta.id"
    label 'process_single'

    conda "bioconda::ensembl-vep=108.2"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/ensembl-vep:108.2--pl5321h4a94de4_0' :
        'quay.io/biocontainers/ensembl-vep:108.2--pl5321h4a94de4_0' }"

    input:
    tuple val(meta), path(vcf)
    path transcriptlist

    output:
    tuple val(meta), path("*.vcf")         , emit: vcf
    path "versions.yml"                    , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    def listfilter = transcriptlist ? "-f \"Feature in $transcriptlist\"" : ""

    """
    filter_vep \\
        $args \\
        -i $vcf \\
        --format vcf \\
        -o ${prefix}.filt.vcf \\
        --soft_filter \\
        $listfilter \\

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        ensemblvep: \$( echo \$(vep --help 2>&1) | sed 's/^.*Versions:.*ensembl-vep : //;s/ .*\$//')
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}.filt.vcf.gz
    touch ${prefix}.summary.html

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        ensemblvep: \$( echo \$(vep --help 2>&1) | sed 's/^.*Versions:.*ensembl-vep : //;s/ .*\$//')
    END_VERSIONS
    """
}
