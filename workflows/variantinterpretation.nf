/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT LOCAL MODULES/SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { CHECKBEDFILE		                        } from '../modules/local/bedfile/checkbedfile/main'
include { TAGROI                                    } from '../subworkflows/local/vcf_roi_tagging/main'
include { BCFTOOLS_INDEX                            } from '../modules/nf-core/bcftools/index/main'
include { SAMTOOLS_DICT                             } from '../modules/nf-core/samtools/dict/main'
include { SAMTOOLS_FAIDX                            } from '../modules/nf-core/samtools/faidx/main'
include { CHECKVCF                                  } from '../subworkflows/local/check_vcf/main'
include { VCFPROC                                   } from '../subworkflows/local/process_vcf/main'
include { MERGE_VCFS                                } from '../subworkflows/local/merge_vcfs/main'
include { ENSEMBLVEP_FILTERVEP as TRANSCRIPT_FILTER } from '../modules/nf-core/ensemblvep/filtervep/main'
include { ENSEMBLVEP_VEP                            } from '../modules/nf-core/ensemblvep/vep/main'
include { TSV_CONVERSION                            } from '../subworkflows/local/tsv_conversion/main'
include { VARIANTFILTER as PRESETS_FILTER_REPORT    } from '../subworkflows/local/variantfilter/main'
include { HTML_REPORT                               } from '../subworkflows/local/html_report/main'
include { TMB_CALCULATE	    	                    } from '../modules/local/tmbcalculation/main'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT NF-CORE MODULES/SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { MULTIQC                     } from '../modules/nf-core/multiqc/main'
include { paramsSummaryMap            } from 'plugin/nf-schema'
include { paramsSummaryMultiqc        } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { softwareVersionsToYAML      } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { methodsDescriptionText      } from '../subworkflows/local/utils_nfcore_variantinterpretation_pipeline'
include { DUMP_WARNINGS               } from '../modules/local/multiqcreport_warnings'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
workflow VARIANTINTERPRETATION {

    take:
    ch_samplesheet
    ch_fasta
    ch_vep_cache
    ch_vep_cache_version
    ch_vep_genome
    ch_vep_species
    ch_vep_extra_files
    ch_annotation_fields
    ch_transcriptlist
    ch_datavzrd_config
    ch_annotation_colinfo
    ch_bedfile
    _ch_consequence_tmb     // unused: TMBCALCULATION reads params.filter_consequence via ext.args
    ch_custom_filters

    main:
    // gather versions of each process
    ch_versions = channel.empty()
    // gather QC reports for multiQC
    ch_multiqc_files = channel.empty()
    // gather warnings
    ch_warnings = channel.empty()

    //
    // Check parameter combinations and give warnings
    //
    if (!params.vep) log.warn("WARNING: You deactivated VEP-based annotation. Downstream processes are working properly only with VEP-annotated VCF file as input!")
    if (!params.tsv && params.report) error("ERROR: Needs to create TSV file for generating HTML report.")
    if (!params.tsv && params.calculate_tmb) error("ERROR: Need to create TSV file for calculating TMB.")
    if (!params.bedfile && params.tag_roi) error("ERROR: Need to specify bedfile for region-of-interest tagging.")
    if (!params.bedfile && params.calculate_tmb) error("ERROR: Need to specify bedfile for calculating TMB.")
    if (!params.read_depth && params.calculate_tmb) error("ERROR: Need to specify the read_depth FORMAT field for calculating TMB.")

    def ch_versions = channel.empty()
    def ch_multiqc_files = channel.empty()
    //
    // Index vcf and reference files
    //

    // create tbi index for vcf
    BCFTOOLS_INDEX ( ch_samplesheet )
    ch_versions = ch_versions.mix(BCFTOOLS_INDEX.out.versions)
    vcf_tbi = ch_samplesheet.join(BCFTOOLS_INDEX.out.tbi)

    // create sequence dictionary and faidx index of reference FASTA
    fasta_ref = ch_fasta.map { fasta_file -> ['ref', fasta_file] }
    SAMTOOLS_DICT( fasta_ref )
    ch_versions = ch_versions.mix(SAMTOOLS_DICT.out.versions)
    SAMTOOLS_FAIDX( fasta_ref, [[], []], [] )
    ch_versions = ch_versions.mix(SAMTOOLS_FAIDX.out.versions)

    //
    // VCF tests
    //

    CHECKVCF (
        vcf_tbi,
        fasta_ref,
        SAMTOOLS_DICT.out.dict,
        SAMTOOLS_FAIDX.out.fai
    )
    ch_versions = ch_versions.mix(CHECKVCF.out.versions)
    ch_warnings = ch_warnings.mix(CHECKVCF.out.warnings)
    ch_multiqc_files = ch_multiqc_files.mix(CHECKVCF.out.multiqc_reports)

    //
    // Check bedfiles
    //

    if (params.bedfile) {
        CHECKBEDFILE ( ch_bedfile )
        ch_min_bedfile=CHECKBEDFILE.out.bedfile_min
        ch_versions = ch_versions.mix(CHECKBEDFILE.out.versions)
    }

    //
    // ROI-tagging of VCF entries
    //
    if (params.tag_roi && CHECKBEDFILE.out.bed_valid) {
        TAGROI (    ch_min_bedfile,
                    vcf_tbi)
        ch_versions = ch_versions.mix(TAGROI.out.versions)
        tagroi_vcf=TAGROI.out.vcf_tbi
    } else {
        tagroi_vcf=vcf_tbi
    }

    //
    // VCF filtering and normalization
    //
    VCFPROC (
            tagroi_vcf,
            ch_fasta
    )
    ch_versions = ch_versions.mix(VCFPROC.out.versions)

    //
    // Merging VCF files by groups
    //

    if (params.merge_vcfs) {
        MERGE_VCFS (
            VCFPROC.out.vcf
        )
        ch_versions = ch_versions.mix(VCFPROC.out.versions)

        proc_vcf=MERGE_VCFS.out.vcf
    } else {
        proc_vcf=VCFPROC.out.vcf
    }

    //
    // MODULE: VEP annotation
    //

    proc_vcf=proc_vcf
        .map { meta, vcf -> tuple( meta, vcf, []) }

    if (params.vep) {
        ENSEMBLVEP_VEP( proc_vcf,
                        ch_vep_genome,
                        ch_vep_species,
                        ch_vep_cache_version,
                        ch_vep_cache,
                        fasta_ref,
                        ch_vep_extra_files)
        ch_vcf = ENSEMBLVEP_VEP.out.vcf
        ch_versions = ch_versions.mix(ENSEMBLVEP_VEP.out.versions)
        ch_multiqc_files = ch_multiqc_files.mix(ENSEMBLVEP_VEP.out.report)
    } else {
        ch_vcf = proc_vcf
    }

    // Filtering for transcripts
    if ( params.transcriptfilter || (params.transcriptlist!=[]) ) {
        TRANSCRIPT_FILTER(  ch_vcf,
                            ch_transcriptlist
        )
        ch_vcf_tf = TRANSCRIPT_FILTER.out.output
        ch_versions = ch_versions.mix(TRANSCRIPT_FILTER.out.versions)
    } else {
        ch_vcf_tf = ch_vcf
    }

    // Use custom filters to tag variants and create subsets
    if (params.custom_filters) {
        PRESETS_FILTER_REPORT ( ch_vcf_tf,
                                ch_custom_filters)
        ch_vcf_tag = PRESETS_FILTER_REPORT.out.vcf
        ch_versions = ch_versions.mix(PRESETS_FILTER_REPORT.out.versions)
    } else {
        ch_vcf_tag = ch_vcf_tf
    }

    //
    // MODULE: TSV conversion with vembrane table
    //

    if ( params.tsv ) {

        TSV_CONVERSION (ch_vcf_tag,
                        ch_annotation_fields
        )
        ch_tsv = TSV_CONVERSION.out.tsv
        ch_versions = ch_versions.mix(TSV_CONVERSION.out.versions)

        //
        // MODULE: HTML report with datavzrd
        //
        if ( params.report ) {
            // need to combine TSV file with datavzrd_config and annotation_col.tsv for report generation
            tsv_config = ch_tsv.combine(ch_datavzrd_config)
            tsv_config_colinfo = tsv_config.combine(ch_annotation_colinfo)
            // generate report
            HTML_REPORT ( tsv_config_colinfo )
            ch_versions = ch_versions.mix(HTML_REPORT.out.versions)
        }

        //
        // MODULE: TMB calculation
        //
        if ( params.bedfile && params.calculate_tmb ) {
                if ( CHECKBEDFILE.out.bed_valid ) {
                        TMB_CALCULATE ( TSV_CONVERSION.out.tsv,
                                        ch_min_bedfile
                    )
                    ch_versions = ch_versions.mix(TMB_CALCULATE.out.versions)
            }
        }
    }

    emit:
    ch_versions
    ch_multiqc_files
    ch_warnings

}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW WITH MULTIQC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow MULTIQC_REPORT {

    take:

    ch_versions
    ch_multiqc_files
    ch_warnings

    main:

    //
    // Collate and save software versions
    //
    def topic_versions = channel.topic("versions")
        .distinct()
        .branch { entry ->
            versions_file: entry instanceof Path
            versions_tuple: true
        }

    def topic_versions_string = topic_versions.versions_tuple
        .map { process, tool, version ->
            [ process[process.lastIndexOf(':')+1..-1], "  ${tool}: ${version}" ]
        }
        .groupTuple(by:0)
        .map { process, tool_versions ->
            tool_versions.unique().sort()
            "${process}:\n${tool_versions.join('\n')}"
        }

    def ch_collated_versions = softwareVersionsToYAML(ch_versions.mix(topic_versions.versions_file))
        .mix(topic_versions_string)
        .collectFile(
            storeDir: "${outdir}/pipeline_info",
            name:  'variantinterpretation_software_'  + 'mqc_'  + 'versions.yml',
            sort: true,
            newLine: true
        )

    //
    // MODULE: MultiQC
    //
    ch_multiqc_files = ch_multiqc_files.mix(ch_collated_versions)
    def ch_summary_params = paramsSummaryMap(workflow, parameters_schema: "nextflow_schema.json")
    def ch_workflow_summary = channel.value(paramsSummaryMultiqc(ch_summary_params))
    ch_multiqc_files = ch_multiqc_files.mix(ch_workflow_summary.collectFile(name: 'workflow_summary_mqc.yaml'))
    def ch_multiqc_custom_methods_description = multiqc_methods_description
        ? file(multiqc_methods_description, checkIfExists: true)
        : file("${projectDir}/assets/methods_description_template.yml", checkIfExists: true)
    def ch_methods_description = channel.value(methodsDescriptionText(ch_multiqc_custom_methods_description))

    // CUSTOM: collect warnings for multiqc report
    ch_multiqc_warnings_template = params.multiqc_warnings_template ?
        file(params.multiqc_warnings_template, checkIfExists: true) :
        file("$projectDir/assets/warnings_multiqc_template.yml", checkIfExists: true)


    ch_warnings_yaml = channel.empty()
    DUMP_WARNINGS(ch_multiqc_warnings_template, ch_warnings.unique().collectFile(name: "collated_warnings.txt", newLine: true))
    ch_warnings_yaml = DUMP_WARNINGS.out.mqc_yml.collect().ifEmpty([])

    ch_multiqc_files = ch_multiqc_files.mix(ch_warnings_yaml)
    ch_multiqc_files = ch_multiqc_files.mix(ch_methods_description.collectFile(name: 'methods_description_mqc.yaml', sort: true))
    
    MULTIQC(
        ch_multiqc_files.flatten().collect().map { files ->
            [
                [id: 'variantinterpretation'],
                files,
                multiqc_config
                    ? file(multiqc_config, checkIfExists: true)
                    : file("${projectDir}/assets/multiqc_config.yml", checkIfExists: true),
                multiqc_logo ? file(multiqc_logo, checkIfExists: true) : [],
                [],
                [],
            ]
        }
    )
    emit:multiqc_report = MULTIQC.out.report.map { _meta, report -> [report] }.toList() // channel: /path/to/multiqc_report.html
    versions       = ch_versions                 // channel: [ path(versions.yml) ]
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
