//
// Index, pre-filter and normalize VCF variant files
//

include { BCFTOOLS_INDEX as INDEX_FILT    } from '../../../modules/nf-core/bcftools/index/main'
include { BCFTOOLS_INDEX as INDEX_NORM    } from '../../../modules/nf-core/bcftools/index/main'
include { BCFTOOLS_VIEW  as VCFFILTER     } from '../../../modules/nf-core/bcftools/view/main'
include { BCFTOOLS_NORM                   } from '../../../modules/nf-core/bcftools/norm/main'

workflow VCFPROC {
    take:
    vcf_tbi             // channel: [ val(meta), path(vcf), path(tbi) ]
    fasta               // path: fastq file for bcftools norm

    main:
    ch_versions = Channel.empty()
    ch_multiqc_reports = Channel.empty()

    //
    // VCF filtering
    //

    if (params.filter_vcf) {
        // filter
        VCFFILTER(vcf_tbi,[],[],[])
        ch_versions = ch_versions.mix(VCFFILTER.out.versions)
        // index
        INDEX_FILT ( VCFFILTER.out.vcf )
        ch_versions = ch_versions.mix(INDEX_FILT.out.versions)
        // merge channels
        proc_vcf_tbi = VCFFILTER.out.vcf.join(INDEX_FILT.out.tbi)
    } else {
        proc_vcf_tbi = vcf_tbi
    }

    //
    // BCFtools norm
    // split multiallelic into biallelic sites as requirement for vembrane
    // optional arguments for left-align indels, remove duplicates, etc.
    //

    fasta_meta = fasta.map { fasta -> tuple([ id:'genome' ], fasta) }

    BCFTOOLS_NORM ( proc_vcf_tbi,
                    fasta_meta
    )
    ch_versions = ch_versions.mix(BCFTOOLS_NORM.out.versions)
    // index
    INDEX_NORM ( BCFTOOLS_NORM.out.vcf )
    ch_versions = ch_versions.mix(INDEX_NORM.out.versions)
    // merge channels
    vcf_norm_tbi = BCFTOOLS_NORM.out.vcf.join(INDEX_NORM.out.tbi)

    emit:
    vcf_norm_tbi    =   vcf_norm_tbi                   // channel: [ val(meta), .vcf, .tbi ]
    versions        =   ch_versions                    // path: versions.yml
}
