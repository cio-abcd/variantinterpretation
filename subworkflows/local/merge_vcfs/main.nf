//
// Merge VCF files to multi-sample VCF files.
//

include { BCFTOOLS_SAMPLERENAME            } from '../../../modules/local/bcftools/samplerename/main'
include { BCFTOOLS_INDEX as INDEX_RENAME   } from '../../../modules/nf-core/bcftools/index/main'
include { BCFTOOLS_MERGE                   } from '../../../modules/nf-core/bcftools/merge/main'

workflow MERGE_VCFS {
    take:
    vcf                // channel: [ val(meta), path(vcf), path(tbi) ]

    main:
    ch_versions = Channel.empty()

    // rename samples within VCF files: add 'sample' from samplesheet as prefix to current name.
    BCFTOOLS_SAMPLERENAME(vcf)
    ch_versions = ch_versions.mix(BCFTOOLS_SAMPLERENAME.out.versions)

    // Indexing needed before merging
    INDEX_RENAME ( BCFTOOLS_SAMPLERENAME.out.vcf )
    ch_versions = ch_versions.mix(INDEX_RENAME.out.versions)
    vcf_tbi = BCFTOOLS_SAMPLERENAME.out.vcf.join(INDEX_RENAME.out.tbi) // merge channels

    // first need to merge the channel them by group
    vcf_tbi
        .map {meta, vcf, tbi ->
                [meta.group, [meta, vcf, tbi]] // first set group as first element and group tuples by group
        }
        .groupTuple()
        .map {group, ch_vcfs ->
            def metadata = [group: group, samples: ch_vcfs.collect { it[0].sample }, id: group] // collect sample names, set meta.id to group
            def vcfs = ch_vcfs.collect { it[1] }.flatten() // collect vcfs
            def tbis = ch_vcfs.collect { it[2] } // collect tbis
            [metadata, vcfs, tbis]
        }
        .set { group_vcf_tbi }

    // Merging VCF files
    BCFTOOLS_MERGE(group_vcf_tbi,[])
    ch_versions = ch_versions.mix(BCFTOOLS_MERGE.out.versions)

    emit:
    vcf         =   BCFTOOLS_MERGE.out.merged_variants     // merged vcf files
    versions    =   ch_versions                            // path: versions.yml
}
