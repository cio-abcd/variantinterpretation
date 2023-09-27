//
// Tag VCF file with predefined filters.
//

include { VEMBRANE_CREATE_TAGS } from '../../../modules/local/vembrane/create-vembrane-tags/main'
include { VEMBRANE_TAG         } from '../../../modules/local/vembrane/tag/main'
include { VEMBRANE_FILTER      } from '../../../modules/local/vembrane/filter/main'


workflow VARIANTFILTER {
    take:
    vcf                 // channel: [ val(meta), vcf ]
    predefined_filters  // path: TSV file with predefined filters

    main:
    ch_versions = Channel.empty()

    // create once vembrane tag argument from custom filters
    VEMBRANE_CREATE_TAGS (predefined_filters)
    ch_versions = ch_versions.mix(VEMBRANE_CREATE_TAGS.out.versions)

    // convert vembrane tag command to value channel for reusing it in each vcf
    ch_filtercmd = VEMBRANE_CREATE_TAGS.out.tagargs.first()

    // tag vcf files with custom filters
    VEMBRANE_TAG (  vcf,
                    ch_filtercmd
    )
    ch_versions = ch_versions.mix(VEMBRANE_TAG.out.versions)

    // split VCF files by used filters
    ch_filters = Channel.of(params.used_filters.split())
    VEMBRANE_FILTER(VEMBRANE_TAG.out.vcf,
                    ch_filters
    )
    ch_versions = ch_versions.mix(VEMBRANE_FILTER.out.versions)

    // merge channels with unfiltered and filtered VCF files to create HTML report for each of them
    allvcfs = VEMBRANE_FILTER.out.vcf.concat(VEMBRANE_TAG.out.vcf)

    emit:
    vcf      =   allvcfs          // channel: [ val(meta), .vcf ]
    versions =   ch_versions      // path: versions.yml
}
