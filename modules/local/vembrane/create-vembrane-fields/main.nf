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
    env fields,     emit: fields
    env header,     emit: header

    when:
    task.ext.when == null || task.ext.when

    script:
    def args   = task.ext.args   ? (task.ext.args.endsWith(",") ? task.ext.args : task.ext.args + ",") : '' 
    def prefix = task.ext.prefix ?: "${meta.id}"

    // check if vcf file is gzipped
    def vcf_list = vcf.collect { it.toString() }
    def vcf_zip  = vcf_list[0].endsWith('.gz')
    def command1 = vcf_zip ? 'zcat' : 'cat'

    // check if strings have comma in the end
    def format_field_withend = format_fields ? (format_fields.endsWith(",")  ? format_fields : format_fields + ",") : ''
    def info_field_withend   = info_fields   ? (info_fields.endsWith(",")    ? info_fields   : info_fields + ",")   : ''

    """
    if [[ '$annotation_fields' == 'all' ]]; then
        # get CSQ field names
        csq_string=\$($command1 $vcf | awk -F'Format: ' '/CSQ/ && /^#/{ \\
            gsub(/">/, "", \$2); \\
            gsub(/\\|/, ", ", \$2); \\
            print \$2
        }')
    else
        # define CSQ field names
        csq_string=$annotation_fields
    fi

    #convert FORMAT fields to vembrane format
    format_vembrane=\$(create_vembrane_fields.py \\
        --column_name FORMAT \\
        --fields_with_sampleindex all \\
        --sampleindex 0 \\
        "$format_field_withend")

    info_vembrane=\$(create_vembrane_fields.py \\
        --column_name INFO \\
        --fields_with_sampleindex all \\
        --sampleindex 0 \\
        "$info_field_withend")

    #convert annotation fields to vembrane format
    csq_vembrane=\$(create_vembrane_fields.py \\
        --column_name CSQ \\
        "\$csq_string")

    #output fields
    fields=`echo "$args" \$format_vembrane \$info_vembrane \$csq_vembrane` \\
    header=`echo "$args" "$format_field_withend" "$info_field_withend" \$csq_string`
    """
}
