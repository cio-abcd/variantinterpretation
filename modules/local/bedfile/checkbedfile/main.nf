
process CHECKBEDFILE {
    tag '$bed_file'
    label 'process_single'

    conda "conda-forge::python=3.8.3 conda-forge::pandas=2.0.3"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mulled-v2-371b28410c3e53c7f9010677515b1b0eb3764999:0267f53936b6c04b051e07833c218f1fdd2a7cac-0' :
        'biocontainers/mulled-v2-371b28410c3e53c7f9010677515b1b0eb3764999:0267f53936b6c04b051e07833c218f1fdd2a7cac-0' }"

    input:
    path bedfile

    output:
    env  valid_structure						, emit: bed_valid
    path "minimized_*"                          , emit: bedfile_min
    path "versions.yml"							, emit: versions

    when:
    task.ext.when == null || task.ext.when

    script: // This script is bundled with the pipeline, in cio-abcd/variantinterpretation/bin/
    """
    ### Start bedfile integrity check
    process_bedfiles.py \\
        $bedfile \\
        'minimized_$bedfile'

    ### Emit control boolean that bedfile adheres to standards
    if [ -f "bed_stats_structure.txt" ]; then
        valid_structure=true
    else
        valid_structure=false
    fi

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
