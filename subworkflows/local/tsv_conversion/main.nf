//
// Convert into TSV format
//

include { VEMBRANE_CREATE_FIELDS } from '../../../modules/local/vembrane/create-vembrane-fields/main'
include { VEMBRANE_VEMBRANETABLE } from '../../../modules/local/vembrane/table/main'


workflow TSV_CONVERSION {
    take:
    vcf                 // channel: [ val(meta), vcf ]
    annotation_fields   // value: Annotation fields in INFO column

    main:
    ch_versions = Channel.empty()

    VEMBRANE_CREATE_FIELDS (vcf,
                            annotation_fields
    )
    ch_versions = ch_versions.mix(VEMBRANE_CREATE_FIELDS.out.versions)

    VEMBRANE_VEMBRANETABLE ( vcf,
                            VEMBRANE_CREATE_FIELDS.out.fields,
                            VEMBRANE_CREATE_FIELDS.out.header
    )
    ch_versions = ch_versions.mix(VEMBRANE_VEMBRANETABLE.out.versions)

    emit:
    tsv      =   VEMBRANE_VEMBRANETABLE.out.tsv // channel: [ val(meta), .tsv ]
    versions =   ch_versions                    // path: versions.yml
}
