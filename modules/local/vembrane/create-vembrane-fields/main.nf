process VEMBRANE_CREATE_FIELDS {
    tag "$meta.id"
    label 'process_single'
    conda "conda-forge::python=3.8.3"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/python:3.8.3' :
        'biocontainers/python:3.8.3' }"

    input:
    tuple val(meta), path(vcf)
    val annotation_fields

    output:
    env fields           , emit: fields
    env header           , emit: header
    path "versions.yml"  , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    // check if vcf file is gzipped
    def vcf_list = vcf.collect { it.toString() }
    def vcf_zip  = vcf_list[0].endsWith('.gz')
    def command1 = vcf_zip ? 'zcat' : 'cat'

    """
    #CSQ annotation fields
    if [[ '$annotation_fields' == 'all' ]]; then
        # get all CSQ field names from VCF
        #short description of code
        # first line: extract the comment line (starting with "#") with the CSQ string in the name and split at "Format: "
        # second line: the last character of the string is ">", will be removed.
        # third line: csq fields are separated by "|", replace it with whitespaces
        csq_string=\$($command1 $vcf | awk -F'Format: ' '/CSQ/ && /^#/{ \\
            gsub(/">/, "", \$2); \\
            gsub(/\\|/, " ", \$2); \\
            print \$2
        }')
    else
        csq_string="$annotation_fields"
    fi

    #create vembrane format
    create_vembrane_fields.py \\
        --csq_fields \$csq_string \\
        --file_out vembrane_string.txt \\
        $args

    #output fields
    fields=`head -n 1 vembrane_string.txt`
    header=`tail -n 1 vembrane_string.txt`

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
