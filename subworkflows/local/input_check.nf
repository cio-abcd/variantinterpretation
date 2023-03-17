//
// Check input samplesheet and get read channels
//

include { SAMPLESHEET_CHECK } from '../../modules/local/samplesheet_check'

workflow INPUT_CHECK {
    take:
    samplesheet // file: /path/to/samplesheet.csv

    main:
    SAMPLESHEET_CHECK ( samplesheet )
        .csv
        .splitCsv ( header:true, sep:',' )
        .map { create_vcf_channel(it) }
        .set { variants }

    emit:
    variants                                     // channel: [ val(meta), [ variants ] ]
    versions = SAMPLESHEET_CHECK.out.versions    // channel: [ versions.yml ]
}

// Function to get list of [ meta, [ fastq_1, fastq_2 ] ]
def create_vcf_channel(LinkedHashMap row) {
    // create meta map
    def meta = [:]
    meta.id         = row.sample    

    // add path(s) of the vcf file to the meta map
    def vcf_meta = []
    if (!file(row.vcf).exists()) {
        exit 1, "ERROR: Please check input samplesheet -> VCF file does not exist!\n${row.vcf}"
    }        
    vcf_meta = [ meta, [ file(row.vcf) ] ]

    return vcf_meta
}
