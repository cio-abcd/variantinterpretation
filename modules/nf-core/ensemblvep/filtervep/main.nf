process ENSEMBLVEP_FILTERVEP {
    tag "$meta.id"
    label 'process_single'

    conda "bioconda::ensembl-vep=108.2"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/ensembl-vep:110.0--pl5321h2a3209d_0' :
        'biocontainers/ensembl-vep:108.2--pl5321h2a3209d_0' }"

    input:
    tuple val(meta), path(input)
    path transcriptlist

    output:
    tuple val(meta), path("*.${extension}"), emit: output
    path "versions.yml"                    , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args   = task.ext.args   ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    extension  = task.ext.suffix ?: "vcf"
    def listfilter = transcriptlist ? "--filter \"Feature in $transcriptlist\"" : ""

    """
    filter_vep \\
        $args \\
        --input_file $input \\
        --output_file ${prefix}.filt.${extension} \\
        $listfilter \\

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        ensemblvep: \$( echo \$(vep --help 2>&1) | sed 's/^.*Versions:.*ensembl-vep : //;s/ .*\$//')
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    extension  = task.ext.suffix ?: "vcf"
    """
    touch ${prefix}.filt.${extension}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        ensemblvep: \$( echo \$(vep --help 2>&1) | sed 's/^.*Versions:.*ensembl-vep : //;s/ .*\$//')
    END_VERSIONS
    """
}
