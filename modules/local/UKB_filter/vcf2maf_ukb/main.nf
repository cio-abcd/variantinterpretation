process VCF2MAF_UKB {
    tag "$meta"
    label 'process_single'
    conda "bioconda::vcf2maf=1.6.22"
       
    input:
    tuple val(meta), path(filtered_variants)
    tuple val(meta2), path(fasta)
    path(mskcc)
   
    output:
    tuple val(meta), path("${meta}_vcf2maf_out.maf"), emit: vcf2mafout
    tuple val(meta), path("log_${meta}_vcf2maf_stdout.log"), emit: log_vcf2maf
    
    //when:
    //task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta}"
    def tumor_sample = "WGS" + "${meta}".substring(0, "${meta}".lastIndexOf("_")) + "_T_1"
    def normal_sample = "WGS" + "${meta}".substring(0, "${meta}".lastIndexOf("_")) + "_N_1"
    """
    vcf2maf.pl --input-vcf ${filtered_variants} \
           --output-maf ${prefix}_vcf2maf_out.maf \
           --tumor-id ${tumor_sample} \
           --normal-id  ${normal_sample} \
           --vcf-tumor-id ${tumor_sample} \
           --vcf-normal-id ${normal_sample} \
           --ref-fasta ${fasta} \
           --species homo_sapiens \
           --cache-version 112  \
           --ncbi-build GRCh38 \
           --custom-enst ${mskcc} \
           --verbose \
           --inhibit-vep > log_${prefix}_vcf2maf_stdout.log 2>&1
    """
}
