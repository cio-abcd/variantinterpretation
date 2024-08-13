# cio-abcd/variantinterpretation: Output

## Introduction

This document describes the output produced by the pipeline. Most of the plots are taken from the MultiQC report, which summarises results at the end of the pipeline.

The directories listed below will be created in the results directory after the pipeline has finished. All paths are relative to the top-level results directory.

## Pipeline overview

The pipeline is built using [Nextflow](https://www.nextflow.io/) and processes data generating the following output:

- [Pre-annotation output](#pre-annotation-output)
  - [vcf checks](#vcf-checks) - Checks VCF files for structure, integrity and several other criteria.
  - [vcf preprocessing](#vcf-preprocessing) - Filters and normalizes variants.
  - [vcf merging](#vcf-merging) - Merges VCF files based on groups.
- [Post-annotation output](#post-annotation-output)
  - [ensemblvep](#ensembl-vep) - Annotates VCF files and reports summary.
  - [transcriptfilter](#transcriptfilter) - Optional filters for specific transcripts.
  - [custom filters](#custom-filters) - Tags VCF file with custom filters, which triggers creation of separate TSV and HTML files for filtered subsets.
- [Reports](#reports)
  - [TSV report](#tsv-report) - Generates TSV files based on VCF files and selected fields.
  - [HTMl report](#html-report) - Generates HTML reports based on TSV files.
  - [Tumor mutational burden](#tumor-mutational-burden) - Calculates the TMB per sample based on provided cutoffs and the TSV files.
  - [MultiQC](#multiqc) - Aggregates report describing results and QC from the whole pipeline.
  - [Pipeline information](#pipeline-information) - Reports metrics generated during the workflow execution.

### Pre-annotation output

#### VCF checks

<details markdown="1">
<summary>Output files</summary>

- `reports/multiqc/input/vcfchecks/`
  - `bcftools_stats/`: Statistics about the VCF file from `bcftools stats` as .txt file, included in multiQC report.
  - `*_warnings.txt`: VCF WARNING messages included in the multiQC report.

</details>

This module checks the VCF file for structure, integrity and several criteria to avoid misleading pipeline errors.

#### VCF preprocessing

<details markdown="1">
<summary>Output files</summary>

- `reports/multiqc/input/bcftools_norm/`: Normalized VCF input as gzipped vcf file using `bcftools norm`.
- `vcfs/preannotation_filter/`: If `filter_pass = true`, contains gzipped vcf files only with variants filtered prior to annotation in the FILTER columns.

</details>

Can perform optional filtering for variants based on FILTER column entries with the `filter_vcf` parameter.
Also runs variant normalization using `bcftools norm` with optional InDel left-alignment.

#### VCF merging

<details markdown="1">
<summary>Output files</summary>

- `vcfs/merged_vcfs/`: Contains vcf files with merged samples based on the 'group' column within the `samplesheet.csv`.

</details>

Can optionally merge VCF files based on the 'group' column in the `samplesheet.csv` file.
Activated via the `--merge_vcfs` parameter.

### Post-annotation output

#### Ensembl VEP

<details markdown="1">
<summary>Output files</summary>

- `vcfs/ensemblvep/`
  - `*.summary.html`: Summary VEP report.
  - `*.vcf.gz`: Gzipped VCF file containing the input variants annotated with VEP. The CSQ string gives information about added columns by VEP.
  </details>

Annotation performed by the variant effect predictor (VEP) software.

#### Transcriptfilter

<details markdown="1">
<summary>Output files</summary>

- `vcfs/transcriptfiltered/`
  - `*.filt.vcf`: VCF file with all variants and additional FILTER column flag.
  </details>

#### Custom filters

<details markdown="1">
<summary>Output files</summary>

- `vcfs/customfilters/`
  - `tagged/*_tag.vcf`: VCF file with all custom filters tagged in the FILTER column.
  - `filtered/*_{filtername}.vcf`: VCF file subset only containing variants from specific filter subset.
  </details>

### Reports

#### TSV report

<details markdown="1">
<summary>Output files</summary>

- `reports/TSV/`
  - `*.tsv`: TSV file containing all fields provided by --extraction_fields, default: CHROM, POS, REF, ALT
  </details>

#### HTML report

<details markdown="1">
<summary>Output files</summary>

- `reports/HTML/`
  - `report_*/`: Folder containing HTML and Excel file for final report. Index.html contains main HTML report file.
  </details>

#### Tumor mutational burden

<details markdown="1">
<summary>Output files</summary>

- `reports/tmb/`
  - `*.txt`: TXT file containing the initial and subsequent counts of eligible mutations based on the provided TMB module thresholds and the final TMB value (mutations/MBp) calculated from the vembrane TSV output after applying allele frequency, coverage and population frequency thresholds.
  - `*.png`: Non-interactive stacked Barplot visualizing the count of mutations (# of mutations) grouped by their variant consequence against their respective allele frequency (in %). Mutations are binned based on their allele frequency (bins = 100) and the lower and upper allele frequency thresholds are plotted as grey dashed lines. Variant Consequences are picked from the Ensembl VEP variant classes on the first unique entry of a mutation based on their genomic position.
  </details>

#### MultiQC

<details markdown="1">
<summary>Output files</summary>

- `reports/multiqc/`
  - `multiqc_report.html`: a standalone HTML file that can be viewed in your web browser.
  - `multiqc_data/`: directory containing parsed statistics from the different tools used in the pipeline.
  - `multiqc_plots/`: directory containing static images from the report in various formats.

</details>

#### Pipeline information

<details markdown="1">
<summary>Output files</summary>

- `reports/pipeline_info/`
  - Reports generated by Nextflow: `execution_report.html`, `execution_timeline.html`, `execution_trace.txt` and `pipeline_dag.dot`/`pipeline_dag.svg`.
  - Reports generated by the pipeline: `pipeline_report.html`, `pipeline_report.txt` and `software_versions.yml`. The `pipeline_report*` files will only be present if the `--email` / `--email_on_fail` parameter's are used when running the pipeline.
  - Reformatted samplesheet files used as input to the pipeline: `samplesheet.valid.csv`.
  - Parameters used by the pipeline run: `params.json`.

</details>
