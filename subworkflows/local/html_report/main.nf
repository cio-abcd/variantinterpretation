//
// Generate HTMl report
//

include { PREPROCESS_DATAVZRD } from '../../../modules/local/datavzrd/preprocess/main'
include { DATAVZRD            } from '../../../modules/local/datavzrd/datavzrd/main'


workflow HTML_REPORT {
    take:
    tsv_config_colinfo        // channel: [ val(meta), path(tsv), path(datavzrd_config), path(annotation_colinfo) ]

    main:
    ch_versions = Channel.empty()

    // Split TSV files and create datavzrd config file
    PREPROCESS_DATAVZRD ( tsv_config_colinfo )
    ch_versions = ch_versions.mix(PREPROCESS_DATAVZRD.out.versions)

    // render datavzrd report
    DATAVZRD ( PREPROCESS_DATAVZRD.out.split_tsv_config )
    ch_versions = ch_versions.mix(DATAVZRD.out.versions)

    emit:
    report      =   DATAVZRD.out.report     // channel: [ val(meta), report_{prefix}/ ]
    versions    =   ch_versions             // path: versions.yml
}
