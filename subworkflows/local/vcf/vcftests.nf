//
// Convert into TSV format
//

include { GATK4_VALIDATEVARIANTS          } from '../../../modules/local/gatk4/validatevariants/main'
include { BCFTOOLS_STATS                  } from '../../../modules/nf-core/bcftools/stats/main'
include { VCFCHECKS                       } from '../../../modules/local/vcfchecks/main'

workflow VCFTESTS {
    take:
    vcf_tbi              // channel: [ val(meta), path(vcf), path(tbi) ]
    fasta_ref            // path: fasta file
    ref_dict             // path: fasta sequence dictionary file
    ref_fai              // path: fasta index file

    main:
    ch_versions = Channel.empty()
    ch_multiqc_reports = Channel.empty()

    //
    // Check VCF format integrity and reference genome correctness
    //

    GATK4_VALIDATEVARIANTS(vcf_tbi, fasta_ref, ref_dict, ref_fai)
    ch_versions = ch_versions.mix(GATK4_VALIDATEVARIANTS.out.versions)

    //
    // produce bcftools stats
    //

    BCFTOOLS_STATS (vcf_tbi,
                    [ [], []],
                    [ [], []],
                    [ [], []],
                    [ [], []],
                    [ [], []]
    )
    ch_versions        = ch_versions.mix(BCFTOOLS_STATS.out.versions)
    ch_multiqc_reports = ch_multiqc_reports.mix(BCFTOOLS_STATS.out.stats.collect{ meta, stats -> stats})

    //
    // Check VCF file
    //

    // join vcf and stats file channels
    vcf_stats=vcf_tbi
        .map { meta, vcf, tbi -> tuple(meta, vcf) }
        .join(BCFTOOLS_STATS.out.stats)

    VCFCHECKS(vcf_stats)

    emit:
    versions        =   ch_versions                    // path: versions.yml
    multiqc_reports =   ch_multiqc_reports             // path: multiQC reports
    warnings        =   VCFCHECKS.out.warnings         // path: warnings.txt
}
