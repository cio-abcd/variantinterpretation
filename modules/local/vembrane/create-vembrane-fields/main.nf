process VEMBRANE_CREATE_FIELDS {
    tag "$meta.id"
    label 'process_single'
    conda "conda-forge::python=3.8.3"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/python:3.8.3' :
        'quay.io/biocontainers/python:3.8.3' }"

    input:
    tuple val(meta), path(vcf)
    val annotation_fields
    val format_fields
    val info_fields

    output:
    env fields           , emit: fields
    env header           , emit: header
    path "versions.yml"  , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args   = task.ext.args   ? (task.ext.args.endsWith(",") ? task.ext.args : task.ext.args + ",") : ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    // check if vcf file is gzipped
    def vcf_list = vcf.collect { it.toString() }
    def vcf_zip  = vcf_list[0].endsWith('.gz')
    def command1 = vcf_zip ? 'zcat' : 'cat'

    """
    #CSQ annotation fields
    if [[ -n '$annotation_fields' ]]; then
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
    csq_vembrane=\$(create_vembrane_fields.py \\
        --column_name CSQ \\
        --fields_with_sampleindex None \\
        --input_fields \$csq_string)

    csq_header=\$(create_vembrane_fields.py \\
        --column_name CSQ \\
        --header \\
        --fields_with_sampleindex None \\
        --input_fields \$csq_string)
    else
        csq_vembrane=""
        csq_header=""
    fi

    #FORMAT FIELDS
    if [[ -n '$format_fields' ]]; then
        format_vembrane=\$(create_vembrane_fields.py \\
            --column_name FORMAT \\
            --fields_with_sampleindex all \\
            --sampleindex 0 \\
            --end_with_comma \\
            --input_fields $format_fields)
        #extract header line
        format_header=\$(create_vembrane_fields.py \\
            --header \\
            --fields_with_sampleindex None \\
            --column_name FORMAT \\
            --end_with_comma \\
            --input_fields $format_fields)
    else
        format_vembrane=""
        format_header=""
    fi

    #INFO FIELDS
    if [[ -n '$info_fields' ]]; then
        info_vembrane=\$(create_vembrane_fields.py \\
            --column_name INFO \\
            --fields_with_sampleindex None \\
            --end_with_comma \\
            --input_fields $info_fields)

        #extract header
        info_header=\$(create_vembrane_fields.py \\
            --header \\
            --fields_with_sampleindex None \\
            --column_name INFO \\
            --end_with_comma \\
            --input_fields $info_fields)
    else
        info_vembrane=""
        info_header=""
    fi

    #output fields
    fields=`echo "$args" \$format_vembrane \$info_vembrane \$csq_vembrane` \\
    header=`echo "$args" \$format_header \$info_header \$csq_header`

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
