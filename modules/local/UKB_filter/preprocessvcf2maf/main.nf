process PREPROCESSVCF2MAF {
    tag "$meta"
    label 'process_single'
    conda "bioconda::bcftools=1.17=h3cc50cf_1"
       
    input:
    tuple val(meta), path(variants)
    tuple val(meta), path(vep_annotated_vcf)
   
    output:
    tuple val(meta), path("${meta}_filtered_variants.vcf"), emit: filtered_variants
    
    //when:
    //task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta}"
    """
    bcftools index ${vep_annotated_vcf}
    bcftools view -O v -R ${variants} ${vep_annotated_vcf} | grep -Ef <(awk 'BEGIN{FS=OFS="\t";print "#"};{print "^"\$1,\$2,"[^\t]+",\$3,\$4"\t"}' "${variants}") > ${prefix}_filtered_variants.vcf
    """
}
