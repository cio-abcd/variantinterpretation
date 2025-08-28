#!/usr/bin/env nextflow
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    variantinterpretation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Github : https://github.com/cio-abcd/variantinterpretation
----------------------------------------------------------------------------------------
*/

nextflow.enable.dsl = 2

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT FUNCTIONS / MODULES / SUBWORKFLOWS / WORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { VARIANTINTERPRETATION; MULTIQC_REPORT   } from './workflows/variantinterpretation'
include { PIPELINE_INITIALISATION } from './subworkflows/local/utils_nfcore_variantinterpretation_pipeline'
include { PIPELINE_COMPLETION     } from './subworkflows/local/utils_nfcore_variantinterpretation_pipeline'
include { getGenomeAttribute      } from './subworkflows/local/utils_nfcore_variantinterpretation_pipeline'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    GENOME PARAMETER VALUES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

//   This is an example of how to use getGenomeAttribute() to fetch parameters
//   from igenomes.config using `--genome`
params.fasta = getGenomeAttribute('fasta')

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    INPUT CHANNELS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

// Initialize files channels from parameters

ch_vep_cache                  = params.vep_cache          ? Channel.fromPath(params.vep_cache).collect()                : []
ch_fasta                      = params.fasta              ? Channel.fromPath(params.fasta).collect()                    : Channel.empty()
ch_transcriptlist             = params.transcriptlist     ? Channel.fromPath(params.transcriptlist).collect()           : []
ch_datavzrd_config            = params.datavzrd_config    ? Channel.fromPath(params.datavzrd_config).collect()          : Channel.fromPath("$projectDir/assets/datavzrd_config_template.yaml", checkIfExists: true)
ch_annotation_colinfo         = params.annotation_colinfo ? Channel.fromPath(params.annotation_colinfo).collect()       : Channel.fromPath("$projectDir/assets/annotation_colinfo.tsv", checkIfExists: true)
ch_bedfile			          = params.bedfile            ? Channel.fromPath(params.bedfile).collect()		            : []
ch_custom_filters             = params.custom_filters     ? Channel.fromPath(params.custom_filters).collect()           : []

// Initialize value channels from parameters

ch_vep_cache_version          = params.vep_cache_version       ?: Channel.empty()
ch_vep_genome                 = params.vep_genome              ?: Channel.empty()
ch_vep_species                = params.vep_species             ?: Channel.empty()
ch_annotation_fields          = params.annotation_fields       ?: ''

// VEP extra files
ch_vep_extra_files            = []

// WES WGS switch
// ch_library_type               = params.library_type             ?: ''

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    NAMED WORKFLOWS FOR PIPELINE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

//
// WORKFLOW: Run main analysis pipeline depending on type of input
//
workflow CIOABCD_VARIANTINTERPRETATION {

    take:
    ch_samplesheet        // channel: samplesheet read in from --input
    ch_library_type       // channel: WES WGS switch given by --library_type

    main:

    //
    // WORKFLOW: Run pipeline
    //
    VARIANTINTERPRETATION (
        ch_samplesheet,
        ch_fasta,
        ch_vep_cache,
        ch_vep_cache_version,
        ch_vep_genome,
        ch_vep_species,
        ch_vep_extra_files,
        ch_annotation_fields,
        ch_transcriptlist,
        ch_datavzrd_config,
        ch_annotation_colinfo,
        ch_bedfile,
        ch_custom_filters,
        ch_library_type
    )

    ch_versions = VARIANTINTERPRETATION.out.ch_versions
    ch_multiqc_files = VARIANTINTERPRETATION.out.ch_multiqc_files
    ch_warnings = VARIANTINTERPRETATION.out.ch_warnings

    MULTIQC_REPORT (
        ch_versions,
        ch_multiqc_files,
        ch_warnings,
    )

    emit:
    multiqc_report = MULTIQC_REPORT.out.multiqc_report // channel: /path/to/multiqc_report.html

}
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow {

    main:

    //
    // SUBWORKFLOW: Run initialisation tasks
    //
    PIPELINE_INITIALISATION (
        params.version,
        params.help,
        params.validate_params,
        params.monochrome_logs,
        args,
        params.outdir,
        params.input
    )

    //
    // WORKFLOW: Run main workflow
    //
    CIOABCD_VARIANTINTERPRETATION (PIPELINE_INITIALISATION.out.samplesheet)

    //
    // SUBWORKFLOW: Run completion tasks
    //
    PIPELINE_COMPLETION (
        params.email,
        params.email_on_fail,
        params.plaintext_email,
        params.outdir,
        params.monochrome_logs,
        params.hook_url,
        CIOABCD_VARIANTINTERPRETATION.out.multiqc_report
    )
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
