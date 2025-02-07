process ONCOKB_ANNOTATOR {
    tag "$meta"
    label 'process_single'
    conda "shahcompbio::oncokb-annotator"
       
    input:
    tuple val(meta), path(vcf2maf_out)
    val(token)
   
    output:
    tuple val(meta), path("${meta}_oncokb_out.maf"), emit: vcf2mafout
    tuple val(meta), path("log_${meta}_oncokb_annotation_stdout.log"), emit: log_vcf2maf
    
    //when:
    //task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta}"
    """
    MafAnnotator.py -i ${vcf2maf_out} -o ${prefix}_oncokb_out.maf -b ${token} > log_${prefix}_oncokb_annotation_stdout.log 2>&1
    """
}
