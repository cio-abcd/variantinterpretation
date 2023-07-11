process PREPROCESS_DATAVZRD {
    tag "$meta.id"
    label 'process_single'

    conda "conda-forge::python=3.9.15 conda-forge::yte=1.5.1 conda-forge::pandas=2.0.3 conda-forge::numpy=1.25.2"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mulled-v2-0594c09780adaaa41fe60b1869ba41c8905a0c98:24a8102d6795963b77f04bb83cc82c081e4a2adc-0' :
        'quay.io/biocontainers/mulled-v2-0594c09780adaaa41fe60b1869ba41c8905a0c98:24a8102d6795963b77f04bb83cc82c081e4a2adc-0' }"

    input:
    tuple val(meta), path(tsv), path(datavzrd_config), path(annotation_colinfo)

    output:
    tuple val(meta), path("*.tsv"), path("*-datavzrd-config-rend.yaml") , emit: split_tsv_config
    path "versions.yml"                                                 , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    preprocess_datavzrd.py  --variant_tsv $tsv \\
                            --colinfo_tsv $annotation_colinfo \\
                            --datavzrd_template $datavzrd_config \\
                            --prefix $prefix \\
                            $args

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
