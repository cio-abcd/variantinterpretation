process VEMBRANE_CREATE_FIELDS {
    tag "$meta.id"
    label 'process_single'

    input:
    tuple val(meta), path(vcf)
    val extraction_fields

    output:
    env fields,     emit: fields
    env header,     emit: header

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    // check if vcf file is gzipped
    def vcf_list = vcf.collect { it.toString() }
    def vcf_zip  = vcf_list[0].endsWith('.gz')
    def command1 = vcf_zip ? 'zcat' : 'cat'

    if ( extraction_fields == 'all' )
        """
        # get CSQ field names and convert to vembrane format
        csqfields=\$($command1 $vcf | awk -F'Format: ' '/CSQ/ && /^#/{ \\
            gsub(/">/, "", \$2); \\
            split(\$2, fields, "\\\\|"); \\
            output = ""; \\
            for (i = 1; i <= length(fields); i++) { \\
                if (output != "") output = output ", "; \\
                output = output "CSQ[\\"" fields[i] "\\"]" \\
            }; \\
            print output \\
        }') \\

        # get CSQ field names for header
        csqheader=\$($command1 $vcf | awk -F'Format: ' '/CSQ/ && /^#/{
            gsub(/">/, "", \$2); \\
            split(\$2, fields, "\\\\|"); \\
            output = ""; \\
            for (i = 1; i <= length(fields); i++) { \\
                if (output != "") output = output ", "; \\
                output = output fields[i] \\
            }; \\
            print output \\
        }') \\

        fields=`echo "$args, " \$csqfields` \\
        header=`echo "$args, " \$csqheader`
        """
    else
        """
        fields=`echo "$args, " "$extraction_fields"`
        header=`echo "$args, " "$extraction_fields"`
        """
}
