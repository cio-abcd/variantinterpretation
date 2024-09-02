process PREPAREBEDFILE {
    tag '$bed_file'
    label 'process_single'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'quay.io/nextflow/bash:latest':
        'quay.io/nextflow/bash:latest' }"

    input:
    path bedfile

    output:
    path "tagged_*"               , emit: tagged_bedfile
    path "versions.yml"           , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''

    """
    tag_bedfile.sh $bedfile

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        bash: \$(bash --version | grep -oh 'version .\\..\\...' | sed 's/version //g' -)
    END_VERSIONS
    """
}
