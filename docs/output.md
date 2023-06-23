# cio-abcd/variantinterpretation: Output

## Introduction

This document describes the output produced by the pipeline. Most of the plots are taken from the MultiQC report, which summarises results at the end of the pipeline.

The directories listed below will be created in the results directory after the pipeline has finished. All paths are relative to the top-level results directory.

<!-- TODO nf-core: Write this documentation describing your workflow's output -->

## Pipeline overview

The pipeline is built using [Nextflow](https://www.nextflow.io/) and processes data using the following steps:

- [vcf tests](#vcftests) - Checks vcf file for structure, integrity and several criteria.
- [vcf proc](#vcfproc) - Filters and normalizes variant sin vcf file.
- [ensemblvep](#ensemblvep) - Annotates VCF file and reports summary.
- [transcriptfilter](#transcriptfilter) - Filters for specific transcripts.
- [vembrane table](#vembranetable) - Generates TSV output based on provided VEP annotation fields
- [datavzrd](#datavzrd) - Generates HTML report based on TSV file.
- [TMB calculate](#tmbcalculate) - Calculates the TMB per sample based on provided cutoffs from vembrane TSV output
- [MultiQC](#multiqc) - Aggregate report describing results and QC from the whole pipeline.
- [Pipeline information](#pipeline-information) - Report metrics generated during the workflow execution.

### VCF tests

<details markdown="1">
<summary>Output files</summary>

- `vcftests/`
  - `bcftools_stats/`: Statistics about the VCF file from `bcftools stats` as .txt file.
  - `*_warnings.txt`: VCF check messages of WARNINGs that will be displayed in the multiQC report.

</details>

This module checks the VCf file for structure, integrity and several criteria to avoid wrongly annotated variants or misleading pipeline errors.
It comprises of three tools:

- [GATK4 ValidateVariants](https://gatk.broadinstitute.org/hc/en-us/articles/360037057272-ValidateVariants)
- [bcftools stats](https://samtools.github.io/bcftools/bcftools.html#stats)
- custom python script

The following table gives an overview about the criteria and whether this gives an error crashing the pipeline or just a warning message in the multiQC report:

| criteria                                     | log-level | description                                                                                                                                                                                                                  | tool                     |
| -------------------------------------------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| VCF file format                              | ERROR     | Checks if general structure of vcf file is adherent to VCF file format.                                                                                                                                                      | `GATK4 ValidateVariants` |
| uncompressed or bgzip compressed             | ERROR     | Checks if file is either uncompressed or bgzip compressed. gzipped files with `.vcf.gz` ending give an error during indexing.                                                                                                | `bcftools index`         |
| single-sample VCF                            | ERROR     | multi-sample VCF files are not supported.                                                                                                                                                                                    | `bcftools stats`         |
| "chr" prefix in CHROM column                 | ERROR     | Checks if each chromosome column in the vcf file contains the "chr" prefix.                                                                                                                                                  | `python script`          |
| matching to reference genome                 | ERROR     | Checks if provided VCF file matches the provided FASTA reference genome. Especially can differentiate between GRCh37 and GRCh38. If left-alignment of indels is activated, `bcftools norm` also checks the reference genome. | `GATK4 ValidateVariants` |
| only passed filters                          | WARNING   | Checks if the FILTER column contains entries other than "PASS" or ".". NOTE: These can be removed with the the `filter_pass` parameter in the vcfproc module.                                                                | `python script`          |
| no-ALT entries                               | WARNING   | Genomic VCF files (gVCFs) are supported but can dramatically increase the runtime of VEP.                                                                                                                                    | `bcftools stats`         |
| no multiallelic sites                        | WARNING   | Checks if the VCF file contains multiallelic variants and gives a warning. NOTE: These will be automatically split wiht `bcftools norm` in the vcfproc module.                                                               | `bcftools stats`         |
| contains other variants than SNVs and InDels | WARNING   | Checks if VCF file contains other variants.                                                                                                                                                                                  | `bcftools stats`         |
| previous VEP annotation present              | WARNING   | Checks if previous VEP annotation is present by checking for VEP in the header and if INFO column already contains a CSQ key.                                                                                                | `python script`          |

### VCF proc

<details markdown="1">
<summary>Output files</summary>

- `vcfproc/`
  - `bcftools_norm/`: Normalized VCf input as gzipped vcf file using `bcftools norm`.
  - `passfilter/`: If `filter_pass = true`, contains gzipped vcf files only with variants containing "PASS" or "." in the FILTER columns.

</details>

Can perform optional filtering for variants based on FILTER column entries with the `filter_vcf` parameter.
Also runs variant normalization using `bcftools norm` with optional InDel left-alignment.

### Ensembl VEP

<details markdown="1">
<summary>Output files</summary>

- `ensemblvep/`
  - `*.summary.html`: Summary VEP report.
  - `*.vcf.gz`: Gzipped VCF file containing the input variants annotated with VEP. The CSQ string gives information about added columns by VEP.
  </details>

[VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) annotated variants based on provided public databases. It provides biological information as protein consequence and effect prediction as well as co-located variants from existing databases giving information, e.g., about population allele frequencies. For full overview, see the [VEP annotation sources](https://www.ensembl.org/info/docs/tools/vep/script/vep_cache.html) and [VEP command flags](https://www.ensembl.org/info/docs/tools/vep/script/vep_options.html).

### Transcriptfilter

<details markdown="1">
<summary>Output files</summary>

- `ensemblvep/`
  - `*.filt.vcf`: VCF file with all variants and additional FILTER column flag.
  </details>

[VEP_filter](https://www.ensembl.org/info/docs/tools/vep/script/vep_filter.html) is a separate script in the Ensembl VEP package that separates the filter step form vep. This module has a hard-coded configuration "--soft_filter" to prevent silent dropping of variants, instead a flag "filter_vep_fail/filter_vep_pass" will be added to the FILTER column. A default external argument is also --only_matched, will results in annotation being dropped if it does not match the filtering criteria. That results in variants only having transcript annotations matching the filter criteria, variants without any matching transcript will be retained, but without any annotation.

### Vembrane table

<details markdown="1">
<summary>Output files</summary>

- `vembrane/`
  - `*.tsv`: TSV file containing all fields provided by --extraction_fields, default: CHROM, POS, REF, ALT
  </details>

[Vembrane table](https://github.com/vembrane/vembrane#readme) generates TSV files based on information found in the VCF header structure. It can parse Information from the FORMAT, INFO and other vcf columns and specifically parses annotation information from CSQ strings in the INFO field, see also the [VEP output documentation](https://www.ensembl.org/info/docs/tools/vep/vep_formats.html#output). It can also handle calculations between parameters and calculates the allele fraction.

### Datavzrd

<details markdown="1">
<summary>Output files</summary>

- `datavzrd/`
  - `report_*/`: Folder containing HTML and Excel file for final report. Index.html contains main HTML report file.
  </details>

[Datavzrd](https://github.com/datavzrd/datavzrd#readme) generates a HTML report from TSV files based on a YAML configuration file. The HTML report enables several features including interactive filtering, links within the data or to the internet, plotting, etc.
The configuration file is rendered using the [YTE template engine](https://github.com/yte-template-engine/yte#readme) that enables usage of python code in YAML files for dynamic rendering.
This module comes with two assets: The [datavzrd_config_template.yaml](../assets/datavzrd_config_template.yaml) which uses information about the annotation columns specified in [annotation_colinfo.tsv](../assets/annotation_colinfo.tsv) for rendering the datavzrd config. Find more information in the parameters help text.

### TMB calculation

<details markdown="1">
<summary>Output files</summary>

- `tmb/`
  - `*.txt`: Single value TXT file containing the TMB value calculated from the vembrane TSV output after applying allele frequency, coverage and population frequency thresholds.
  - `*.png`: Non-interactive Barplot visualizing the count of mutations against their respective allele frequency
  </details>

[TMB calculation](bin/calculate_TMB.py) generates a single value TXT file containing the Tumor Mutational Burden (TMB) as single value. The calculation will be performed on the vembrane TSV output file, allowing for prefiltering of unwanted mutations using the vep-filter step prior to TMB calculation. TMB calculation will only be performed if a [well-formatted BED file](https://genome.ucsc.edu/FAQ/FAQformat.html#format1) covering at least 1 MBp in its target regions was provided to the workflow. TMB calculation is not a unified and standarized process, thus different thresholds can be provided including a lower and upper allele frequency boundary, a minimal threshold for coverage, a maximal threshold for presence in the [gnomAD global population frequency](https://gnomad.broadinstitute.org/) and a flag to filter InDels from the calculation procedure.

### MultiQC

<details markdown="1">
<summary>Output files</summary>

- `multiqc/`
  - `multiqc_report.html`: a standalone HTML file that can be viewed in your web browser.
  - `multiqc_data/`: directory containing parsed statistics from the different tools used in the pipeline.
  - `multiqc_plots/`: directory containing static images from the report in various formats.

</details>

[MultiQC](http://multiqc.info) is a visualization tool that generates a single HTML report summarising all samples in your project. Most of the pipeline QC results are visualised in the report and further statistics are available in the report data directory.

Results generated by MultiQC collate pipeline QC from supported tools e.g. FastQC. The pipeline has special steps which also allow the software versions to be reported in the MultiQC output for future traceability. For more information about how to use MultiQC reports, see <http://multiqc.info>.

### Pipeline information

<details markdown="1">
<summary>Output files</summary>

- `pipeline_info/`
  - Reports generated by Nextflow: `execution_report.html`, `execution_timeline.html`, `execution_trace.txt` and `pipeline_dag.dot`/`pipeline_dag.svg`.
  - Reports generated by the pipeline: `pipeline_report.html`, `pipeline_report.txt` and `software_versions.yml`. The `pipeline_report*` files will only be present if the `--email` / `--email_on_fail` parameter's are used when running the pipeline.
  - Reformatted samplesheet files used as input to the pipeline: `samplesheet.valid.csv`.

</details>

[Nextflow](https://www.nextflow.io/docs/latest/tracing.html) provides excellent functionality for generating various reports relevant to the running and execution of the pipeline. This will allow you to troubleshoot errors with the running of the pipeline, and also provide you with other information such as launch commands, run times and resource usage.
