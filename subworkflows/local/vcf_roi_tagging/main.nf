
include { PREPAREBEDFILE                            } from '../../../modules/local/bedfile/preparebedfile/main'
include { TABIX_BGZIP as FIRST_COMPRESS             } from '../../../modules/nf-core/tabix/bgzip/main'
include { TABIX_BGZIP as SECOND_COMPRESS            } from '../../../modules/nf-core/tabix/bgzip/main'
include { TABIX_TABIX                               } from '../../../modules/nf-core/tabix/tabix/main'
include { BCFTOOLS_INDEX                            } from '../../../modules/nf-core/bcftools/index/main'
include { BCFTOOLS_INDEX as TAGROI_INDEX            } from '../../../modules/nf-core/bcftools/index/main'
include { BCFTOOLS_ANNOTATE as BCFTOOLS_ADDROI      } from '../../../modules/nf-core/bcftools/annotate/main'
include { BCFTOOLS_ANNOTATE as BCFTOOLS_RMVROI      } from '../../../modules/nf-core/bcftools/annotate/main'
include { VEMBRANE_TAG as FILTER_TAGROI             } from '../../../modules/local/vembrane/tag/main'

workflow TAGROI {

    take:
    bedfile             // path to BED file
    vcf_tbi             // channel: [ val(meta), path(vcf), path(tbi) ]

    main:

    ch_versions = Channel.empty()
    annotation_header = Channel.fromPath("$projectDir/bin/header_line.txt").collect()

    // Include a boolean flag in the provided BED file for bcftools annotate
    PREPAREBEDFILE (
        bedfile
    )
    ch_versions = ch_versions.mix(PREPAREBEDFILE.out.versions)
    ch_tagbedfile = PREPAREBEDFILE.out.tagged_bedfile.map{it -> [ [ id:it.baseName ], it ] }

    // Compress with BGZIP and index with tabix
    FIRST_COMPRESS (
        ch_tagbedfile
    )
    TABIX_TABIX (
        FIRST_COMPRESS.out.output
    )

    ch_posttabix = FIRST_COMPRESS.out.output.map{ in -> in[1] }.collect() // isolate filepath
    ch_posttabix_idx = TABIX_TABIX.out.tbi.map{ in -> in[1] }.collect() // isolate filepath

    ch_versions = ch_versions.mix(FIRST_COMPRESS.out.versions)
    ch_versions = ch_versions.mix(TABIX_TABIX.out.versions)

    // Annotate regions contained in the provided BED-file using INFO/ROI='TRUE'

    BCFTOOLS_ADDROI (
        vcf_tbi,
        ch_posttabix,
        ch_posttabix_idx,
        annotation_header
    )
    ch_versions = ch_versions.mix(BCFTOOLS_ADDROI.out.versions)

    // Tag FILTER field in VCF

    ch_tagarg = channel.value('--tag not_in_ROI="INFO[\'ROI\'] == \'TRUE\'"')

    FILTER_TAGROI (
        BCFTOOLS_ADDROI.out.vcf,
        ch_tagarg
    )
    ch_versions.mix(FILTER_TAGROI.out.versions)

    // Re-Compress and Index VCF after vembrane decompression

    SECOND_COMPRESS(
        FILTER_TAGROI.out.vcf
    )

    TAGROI_INDEX(
        SECOND_COMPRESS.out.output
    )
    ch_versions.mix(TAGROI_INDEX.out.versions)
    ch_removeroi = SECOND_COMPRESS.out.output.join(TAGROI_INDEX.out.tbi)

    // Remove INFO/ROI=TRUE to keep INFO-Tag number consistent
    // Generate index for mixing with output data for downstream processes

    BCFTOOLS_RMVROI (
        ch_removeroi, [], [], []
    )

    BCFTOOLS_INDEX  (
        BCFTOOLS_RMVROI.out.vcf
    )
    ch_posttagging = BCFTOOLS_RMVROI.out.vcf.join(BCFTOOLS_INDEX.out.tbi)

    emit:
    vcf_tbi     =   ch_posttagging
    versions    =   ch_versions                     // channel: [ versions.yml ]
}
