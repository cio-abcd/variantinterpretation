process DUMP_WARNINGS {
    label 'process_single'

    input:
    path template_yml
    path warnings

    output:
    path 'warnings_multiqc_mqc.yml' , emit: mqc_yml

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    awk '{print "      <li> "\$0" </li>"}' $warnings > all_warnings.txt

    sed  '/PLACEHOLDER/{
        s/PLACEHOLDER//g
        r all_warnings.txt
    }' $template_yml > warnings_multiqc_mqc.yml
    """
}
