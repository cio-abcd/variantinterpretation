process TMB_CALCULATE {
    tag "$meta.id"
    label 'process_single'

    conda "conda-forge::python=3.8.3 conda-forge::pandas=2.0.3 conda-forge::numpy=1.25.1 conda-forge::matplotlib=3.6.3 conda-forge::seaborn=0.12.2 conda-forge::pyranges=0.0.117"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mulled-v2-371b28410c3e53c7f9010677515b1b0eb3764999:0267f53936b6c04b051e07833c218f1fdd2a7cac-0' :
        'biocontainers/mulled-v2-371b28410c3e53c7f9010677515b1b0eb3764999:0267f53936b6c04b051e07833c218f1fdd2a7cac-0' }"

    input:
    tuple val(meta), path(tsv)
    path bedfile
    path consequence_tmb

    output:
    tuple val(meta), path("*.txt"), emit: TMB_txt
    tuple val(meta), path("*.png"), emit: TMB_png
    path "versions.yml"           , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    # Calculate TMB
    calculate_TMB.py \\
        --file_in $tsv \\
        --bedfile $bedfile \\
        --filter_consequence $consequence_tmb \\
        $args \\
        --file_out ${prefix}.txt \\
        --plot_out ${prefix}.png

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
