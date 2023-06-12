/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    VALIDATE INPUTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

def summary_params = NfcoreSchema.paramsSummaryMap(workflow, params)

// Validate input parameters
WorkflowVariantinterpretation.initialise(params, log)

// TODO nf-core: Add all file path parameters for the pipeline to the list below
// Check input path parameters to see if they exist
def checkPathParamList = [ 
       params.input,
       params.fasta,
       params.multiqc_config,
       params.vep_cache,
       params.transcriptlist
]
for (param in checkPathParamList) { if (param) { file(param, checkIfExists: true) } }

// Check mandatory parameters
if (params.input) { ch_input = file(params.input) } else { exit 1, 'Input samplesheet not specified!' }

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    CONFIG FILES & INPUT CHANNELS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

ch_multiqc_config          = Channel.fromPath("$projectDir/assets/multiqc_config.yml", checkIfExists: true)
ch_multiqc_custom_config   = params.multiqc_config ? Channel.fromPath( params.multiqc_config, checkIfExists: true ) : Channel.empty()
ch_multiqc_logo            = params.multiqc_logo   ? Channel.fromPath( params.multiqc_logo, checkIfExists: true ) : Channel.empty()
ch_multiqc_custom_methods_description = params.multiqc_methods_description ? file(params.multiqc_methods_description, checkIfExists: true) : file("$projectDir/assets/methods_description_template.yml", checkIfExists: true)

// Initialize files channels from parameters

vep_cache                  = params.vep_cache          ? Channel.fromPath(params.vep_cache).collect()                : []
fasta                      = params.fasta              ? Channel.fromPath(params.fasta).collect()                    : Channel.empty()
transcriptlist             = params.transcriptlist     ? Channel.fromPath(params.transcriptlist).collect()           : []

// Initialize value channels from parameters

vep_cache_version          = params.vep_cache_version       ?: Channel.empty()
vep_genome                 = params.vep_genome              ?: Channel.empty()
vep_species                = params.vep_species             ?: Channel.empty()
extraction_fields          = params.extraction_fields       ?: Channel.empty()

// Convert specific format field parameters of variant callers
if ( params.format_fields ) {
    if (params.format_fields == 'mutect2') {
        format_fields = Channel.value('AF AD DP')
    } else if (params.format_fields == 'freebayes') {
        format_fields = Channel.value('AD DP')
    } else {
        format_fields = params.format_fields
    }
} else {
    Channel.empty()
}

// VEP extra files
vep_extra_files            = []

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT LOCAL MODULES/SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

//
// SUBWORKFLOW: Consisting of a mix of local and nf-core/modules
//
include { INPUT_CHECK           } from '../subworkflows/local/input_check'
include { ENSEMBLVEP_FILTER     } from '../modules/local/ensemblvep/filter_vep/main'
include { ENSEMBLVEP_VEP        } from '../modules/local/ensemblvep/vep/main'
include { VEMBRANE_TABLE        } from '../subworkflows/local/vembrane_table/main'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT NF-CORE MODULES/SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

//
// MODULE: Installed directly from nf-core/modules
//
include { BCFTOOLS_INDEX	      } from '../modules/nf-core/bcftools/index/main'
include { BCFTOOLS_NORM               } from '../modules/nf-core/bcftools/norm/main' 
include { MULTIQC                     } from '../modules/nf-core/multiqc/main'
include { CUSTOM_DUMPSOFTWAREVERSIONS } from '../modules/nf-core/custom/dumpsoftwareversions/main'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

// Info required for completion email and summary
def multiqc_report = []

workflow VARIANTINTERPRETATION {

    ch_versions = Channel.empty()

    //
    // SUBWORKFLOW: Read in samplesheet, validate and stage input files
    //
    input = INPUT_CHECK (
        ch_input
    )
    ch_versions = ch_versions.mix(INPUT_CHECK.out.versions)    

    ///
    // bcftools index module
    ///

    BCFTOOLS_INDEX (	input.variants
                   )
    ch_versions = ch_versions.mix(BCFTOOLS_INDEX.out.versions)

    ///
    // splitting multiallelic sites into biallelic
    ///

    ch_norm = input.variants
    ch_norm = ch_norm.join(BCFTOOLS_INDEX.out.tbi)

    BCFTOOLS_NORM (     ch_norm,
                        fasta
		  )
    ch_versions = ch_versions.mix(BCFTOOLS_NORM.out.versions)

    ///
    // VEP annotation module
    //
    if (params.vep) {
        ENSEMBLVEP_VEP( BCFTOOLS_NORM.out.vcf,
                        vep_genome,
                        vep_species,
                        vep_cache_version,
                        vep_cache,
                        fasta,
                        vep_extra_files)
        ch_versions = ch_versions.mix(ENSEMBLVEP_VEP.out.versions)

        // Filtering for transcripts
        if ( params.transcriptfilter || (params.transcriptlist!=[]) ) {
            ENSEMBLVEP_FILTER( ENSEMBLVEP_VEP.out.vcf,
                               transcriptlist
            )
            ch_versions = ch_versions.mix(ENSEMBLVEP_FILTER.out.versions)
        }
    }

    ///
    // MODULE: TSV conversion with vembrane table
    ///

    if ( params.tsv ) {
        if ( params.transcriptfilter || (params.transcriptlist!=[]) ) {
            VEMBRANE_TABLE ( ENSEMBLVEP_FILTER.out.vcf,
                             extraction_fields,
                             format_fields
            )
        } else {
            VEMBRANE_TABLE ( ENSEMBLVEP_VEP.out.vcf,
                             extraction_fields,
                             format_fields
            )
        }
        ch_versions = ch_versions.mix(VEMBRANE_TABLE.out.versions)
    }

    // dump software versions
    ch_version_yaml = Channel.empty()
    CUSTOM_DUMPSOFTWAREVERSIONS(ch_versions.unique().collectFile(name: 'versions.yml'))
    ch_version_yaml = CUSTOM_DUMPSOFTWAREVERSIONS.out.mqc_yml.collect()

    //
    // MODULE: MultiQC
    //
    workflow_summary    = WorkflowVariantinterpretation.paramsSummaryMultiqc(workflow, summary_params)
    ch_workflow_summary = Channel.value(workflow_summary)

    methods_description    = WorkflowVariantinterpretation.methodsDescriptionText(workflow, ch_multiqc_custom_methods_description)
    ch_methods_description = Channel.value(methods_description)

    ch_multiqc_files = Channel.empty()
    ch_multiqc_files = ch_multiqc_files.mix(ch_workflow_summary.collectFile(name: 'workflow_summary_mqc.yaml'))
    ch_multiqc_files = ch_multiqc_files.mix(ch_methods_description.collectFile(name: 'methods_description_mqc.yaml'))
    ch_multiqc_files = ch_multiqc_files.mix(CUSTOM_DUMPSOFTWAREVERSIONS.out.mqc_yml.collect())    

    MULTIQC (
        ch_multiqc_files.collect(),
        ch_multiqc_config.toList(),
        ch_multiqc_custom_config.toList(),
        ch_multiqc_logo.toList()
    )
        multiqc_report = MULTIQC.out.report.toList()

}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    COMPLETION EMAIL AND SUMMARY
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow.onComplete {
    if (params.email || params.email_on_fail) {
        NfcoreTemplate.email(workflow, params, summary_params, projectDir, log, multiqc_report)
    }
    NfcoreTemplate.summary(workflow, params, log)
    if (params.hook_url) {
        NfcoreTemplate.IM_notification(workflow, params, summary_params, projectDir, log)
    }
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
