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
    ### Rename output BED as tagged_*
    tagged_bed='tagged_$bedfile'
    ### Add annotation column
    sed 's/\$/\tTRUE/g' $bedfile > \$tagged_bed

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        bash: \$(bash --version | grep -oh 'version .\\..\\...' | sed 's/version //g' -)
    END_VERSIONS
    """
}
