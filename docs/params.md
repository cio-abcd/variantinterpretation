# cio-abcd/variantinterpretation pipeline parameters

Pipeline to add biological and clinical knowledge to genomic variants.

## Input/output options

Define where the pipeline should find input data and save output data.

| Parameter | Description | Type | Default | Required | Hidden |
|-----------|-----------|-----------|-----------|-----------|-----------|
| `input` | Path to comma-separated file containing information about the samples in the experiment. <details><summary>Help</summary><small>You will need to create a design file with information about the samples in your experiment before running the pipeline. Use this parameter to specify its location. It has to be a comma-separated file with 3 columns, and a header row.</small></details>| `string` |  | True |  |
| `outdir` | The output directory where the results will be saved. You have to use absolute paths to storage on Cloud infrastructure. | `string` |  | True |  |
| `email` | Email address for completion summary. <details><summary>Help</summary><small>Set this parameter to your e-mail address to get a summary e-mail with details of the run sent to you when the workflow exits. If set in your user config file (`~/.nextflow/config`) then you don't need to specify this on the command line for every run.</small></details>| `string` |  |  |  |
| `multiqc_title` | MultiQC report title. Printed as page header, used for filename if not otherwise specified. | `string` |  |  |  |

## VCF normalization



| Parameter | Description | Type | Default | Required | Hidden |
|-----------|-----------|-----------|-----------|-----------|-----------|
| `left_align_indels` | Enables left-alignment of Indels using bcftools norm. | `boolean` |  |  |  |
| `filter_vcf` | Only keep vcf entries which FILTER columns match the specified single string. Set to null to disable filtering. | `string` |  |  |  |
| `merge_vcfs` | If true, uses bcftools merge to create multi-sample VCF files of all files within the same group. The group can be specified as additional column in the samplesheet.csv. | `boolean` |  |  |  |

## Reference genome options

Reference genome related files and options required for the workflow.

| Parameter | Description | Type | Default | Required | Hidden |
|-----------|-----------|-----------|-----------|-----------|-----------|
| `genome` | Name of iGenomes reference. <details><summary>Help</summary><small>If using a reference genome configured in the pipeline using iGenomes, use this parameter to give the ID for the reference. This is then used to build the full paths for all required reference genome files e.g. `--genome GRCh38`. <br><br>See the [nf-core website docs](https://nf-co.re/usage/reference_genomes) for more details.</small></details>| `string` |  |  |  |
| `fasta` | Path to FASTA genome file. <details><summary>Help</summary><small>This parameter is *mandatory* if `--genome` is not specified. If you don't have a BWA index available this will be generated for you automatically. Combine with `--save_reference` to save BWA index for future runs.</small></details>| `string` |  |  |  |
| `igenomes_ignore` | Do not load the iGenomes reference config. <details><summary>Help</summary><small>Do not load `igenomes.config` when running the pipeline. You may choose this option if you observe clashes between custom parameters and those supplied in `igenomes.config`.</small></details>| `boolean` |  |  | True |

## Preprocessing options

Options related to prefiltering routines (e.g. BED file)

| Parameter | Description | Type | Default | Required | Hidden |
|-----------|-----------|-----------|-----------|-----------|-----------|
| `bedfile` | BED file of the sequencing panel used for VCF generation | `string` |  |  |  |

## Annotation options

VEP-related options for annotation of VCF files

| Parameter | Description | Type | Default | Required | Hidden |
|-----------|-----------|-----------|-----------|-----------|-----------|
| `vep` | Enable annotation using VEP | `boolean` | True |  |  |
| `vep_out_format` | Output format for VEP | `string` | vcf |  |  |
| `vep_genome` | Specify the genome used for VEP. | `string` | GRCh38 |  |  |
| `vep_species` | Specify the species used for VEP | `string` | homo_sapiens |  |  |
| `vep_cache` | Define path to offline cache used for VEP. <details><summary>Help</summary><small>Define offline cache used for VEP. Mandatory for running VEP. Has to be a file path.</small></details>| `string` |  |  |  |
| `vep_cache_version` | Version of VEP cache to use. <details><summary>Help</summary><small>Should always match the implemented VEP tool version.</small></details>| `string` | 113 |  |  |
| `vep_cache_source` | Specified VEP cache type. Either Ensembl (default, null), Refseq or merged. <details><summary>Help</summary><small>Leave empty (null) if ensembl (standard) cache is used.</small></details>| `string` |  |  |  |
| `check_existing` | Annotate dbSNP or other co-located databases. | `boolean` | True |  |  |
| `everything` | Adds lots of standard flags for annotation with VEP. | `boolean` | True |  |  |
| `no_escape` | Do not escape characters as "=" in HGSV strings. | `boolean` | True |  |  |
| `flag_pick` | Flags only one transcript based on VEP-specific criteria. <details><summary>Help</summary><small>More information about the order to pick transcripts can be found here: https://www.ensembl.org/info/docs/tools/vep/script/vep_other.html#pick</small></details>| `boolean` |  |  |  |
| `flag_pick_allele` | as --flag_pick, but per variant allele. <details><summary>Help</summary><small>Only different from --flag_pick if alternative alleles are present.</small></details>| `boolean` |  |  |  |
| `flag_pick_allele_gene` | as --flag_pick_allele, but but per variant allele and gene combination. | `boolean` | True |  |  |
| `terms` | Consequence terms to use. <details><summary>Help</summary><small>Default is Sequence Ontology. Details can be found here: http://www.sequenceontology.org/</small></details>| `string` | SO |  |  |
| `clin_sig_allele` | Provide allele-specific clinical significance. | `boolean` | True |  |  |
| `exclude_null_alleles` | Exclude variants with unknown alleles in existing databases as HGMD or COSMIC. <details><summary>Help</summary><small>Important for the --check_existing output.</small></details>| `boolean` |  |  |  |
| `no_check_alleles` | Disable check for novel alleles in existing databases. If disabled, compares by coordinate alone. <details><summary>Help</summary><small>Important for the --check_existing output.</small></details>| `boolean` |  |  |  |
| `var_synonyms` | Output also Synonyms for existing variants. <details><summary>Help</summary><small>Important for --check_existing output.</small></details>| `boolean` | True |  |  |

## Annotation filtering option

Options for filtering VCF files

| Parameter | Description | Type | Default | Required | Hidden |
|-----------|-----------|-----------|-----------|-----------|-----------|
| `transcriptfilter` | Name of annotation column that should be used to filter for transcripts, e.g. 'PICK' in the VEP cache. <details><summary>Help</summary><small>If the variant does not have any transcript annotation in the respective column, all annotations will be removed and variant is flagged in FILTER column.<br>Can work simultaneously with "transcriptlist" parameter.</small></details>| `string` |  |  |  |
| `transcriptlist` | List of transcripts for filtering. <details><summary>Help</summary><small>If the variant does not have any matching transcript, all annotations will be removed and variant is flagged in FILTER column.<br>Can work simultaneously with "transcriptfilter" parameter.</small></details>| `string` | [] |  |  |
| `custom_filters` | TSV file defining custom filters for VCF files. VCF files will be tagged with those filters in the FILTER column. <details><summary>Help</summary><small>The TSV files needs two columns: The first column contains the name of the filter (letters, numbers and underscores allowed), the second column a valid python expression defining the filter. The python expression has to follow the guidelines for vembrane, also see here: https://github.com/vembrane/vembrane#filter-expression. An example can be found in assets/custom_filters.tsv.</small></details>| `string` |  |  |  |
| `used_filters` | Define which filters from `custom_filters` will be used to subset VCF files and create separate TSV and HTML files. <details><summary>Help</summary><small>Needs to match the filter name from `custom_filters`. Multiple filters can be defined (comma-separated), but not combined.</small></details>| `string` |  |  |  |

## TSV conversion options



| Parameter | Description | Type | Default | Required | Hidden |
|-----------|-----------|-----------|-----------|-----------|-----------|
| `tsv` | Convert annotated VCF file into TSV format | `boolean` | True |  |  |
| `allele_fraction` | Specify how to extract and calculate the allele fraction from the VCF file. <details><summary>Help</summary><small>The allele fraction (AF) of a variant is not always reported directly in the VCF file, but encoded indirectly in the FORMAT column. The AF is extracted or calculated  in the `vembrane table` module.   <br>Within the FORMAT column are some standard fields from which the AF can be calculated:   <br><br>- **DP:** Depth or coverage, number of reads at this position.  <br>- **AD:** Allelic depth, Number of reads supporting REF and ALT alleles (comma-separated, can be addressed with [0] or [1] as index)  <br><br>Dividing the allelic depth by the coverage gives the AF, which can be invoked with `FORMAT_AD`. Some VCF files also directly encode the AF in the FORMAT column as `AF` field, which can be invoked with `FORMAT_AF`.  <br>For the following variant callers, some defaults were specified that can be invoked by the name of the caller:  <br><br>- **Freebayes** uses the `FORMAT_AD` method dividing ALT allele readnumbers (AD[1]) by depth (DP)   <br>- **Mutect2** uses the AF field in the FORMAT column as defined in `FORMAT_AF` method. It is a probabilistic AF estimate, hence it is different compared to AF calculated with DP and AD column. Additionally, the DP field is also in the INFO column and will be extracted, which can be greater as the DP field in the FORMAT column as it also contains uninformative reads. So there can be three different ways of calculating the AF. Sources: [[1]](https://gatk.broadinstitute.org/hc/en-us/community/posts/4566282375835-Mutect2-AF-does-not-match-AD-and-DP),[[2]](https://github.com/broadinstitute/gatk/issues/6067),[[3]](https://gatk.broadinstitute.org/hc/en-us/articles/360035532252-Allele-Depth-AD-is-lower-than-expected). </small></details>| `string` | FORMAT_AD |  |  |
| `read_depth` | Specify from which FORMAT field to extract read depth.  This will specify the column named "read_depth" in the output report and TSV file.. | `string` | DP |  |  |
| `annotation_fields` | Comma-separated CSQ field names with annotation fields from VEP annotation to include in TSV output. Can extract all annotation fields with 'all' (default). | `string` | all |  |  |
| `format_fields` | Comma-separated FORMAT field names from VCF FORMAT column to include in TSV output. Can include, e.g., allelic depth, fraction and coverage. | `string` | GT,AD[0],AD[1] |  |  |
| `info_fields` | Comma-separated INFO field names from VCF INFO column to include in TSV output. | `string` |  |  |  |

## HTML report



| Parameter | Description | Type | Default | Required | Hidden |
|-----------|-----------|-----------|-----------|-----------|-----------|
| `report` | Convert TSV file into HTML report using datavzrd. | `boolean` | True |  |  |
| `datavzrd_config` | YAML file storing the configurations for datavzrd. Will be rendered using YTE template engine interpreting python code. By default uses datavzrd_config_template.yaml in the workflow `assets/`. <details><summary>Help</summary><small>YTE rendering adds group- and column-specific datavzrd configurations that are specified in annotation_colinfo (see help text of annotation_colinfo).<br>During YAML rendering, the information from the annotation_colinfo file is accessible in the template config file.<br>These can be accessed through the respective column name. The column "data_type_value" will be converted to a dictionary.</small></details>| `string` |  |  |  |
| `annotation_colinfo` | TSV file giving information about annotations and how to render them for HTML report. <details><summary>Help</summary><small>This TSV file contains six unique columns:  <br>- identifier: Name of the corresponding annotation column in the variant TSV file. This column is used to match the variant TSV columns. The variant TSV column names will be adapted for better matching that needs to be considered when defining those identifiers: The matching is case-insensitive, disregards "CSQ_" prefixes and only allows letters, numbers and underscores. Square brackets will be replaced with a "-", Mathematical operands in variant TSV column names will be replaced with literal strings: "+" is replaced with "-plus-", "-" with "-minus-", "*" with "-times-", "/" with "-divided-by-", "%" with "-modulus-". For example: If the variant TSV column name is FORMAT_AD[1]/FORMAT_DP, the identifier has to have the name FORMAT_AD-1--divided-by-FORMAT_DP and can have lower or upper cases.<br><br>- label: new label that will be shown in HTML report if display = normal.  <br><br>- group: The columns of the variant TSV file will be splitted into group-specific TSV files to make the report better accessible. This column defines the specific group names. Each group will be linked to each other. However, accessing columns between groups in the datavzrd_config file is not possible.  <br><br>- display: Allows 'normal', 'detail' and 'hidden'  according to the display-mode parameter in datavzrd. "normal" shows the column, "detail" puts it in detail view accessible with "+", "hidden" does not show it in the HTML report, but in the exported excel table.  <br><br>- data_type and data_type_value: Both columns determines implemented automatic rendering in this workflow:<br>  - data_type=__integer or float__: Will create a [ticks plot](https://vega.github.io/vega-lite/docs/tick.html)<br>    - if data_type_value=min=NUM1,max=NUM2 key-value pairs are specified, will set the range of tick plot.<br>  - data_type=__string__: Creates heatmap plot if `data_type_value` has fieldname=color key=value pairs specifying the color literally or in hexcode.<br>  - data_type=___link__: Creates a hyperlink if `data_type_value` provides name=url key=value pairs. Can refer to entries of the same row and group with the respective column name in curly brackets in lower cases.<br><br>The order of the rows in this file determines the order of columns shown in the HTML report.<br>Each group report will always show the identifier columns "chrom", "pos", "ref", "alt", "id", and "Feature" that are needed to reference between group tables.</small></details>| `string` |  |  |  |

## TMB Calculation options

Options related to cutoffs in TMB calculation

| Parameter | Description | Type | Default | Required | Hidden |
|-----------|-----------|-----------|-----------|-----------|-----------|
| `calculate_tmb` | Enable TMB calculation | `boolean` |  |  |  |
| `min_af` | Minimal allele frequency cutoff for TMB calculation | `number` | 0 |  |  |
| `max_af` | Maximal allele frequency cutoff for TMB calculation | `number` | 1 |  |  |
| `min_cov` | Minimal coverage cutoff for TMB calculation | `integer` | 10 |  |  |
| `max_popfreq` | Maximal population allele frequency in the gnomAD global population for TMB calculation | `number` | 0.02 |  |  |
| `filter_muttype` | Define if only SNVs, SNVs and MNVs or all mutation types should be selected for TMB calculation | `string` | snv |  |  |
| `population_db` | Define an alternative population database to filter annotated mutations based on population frequency | `string` |  |  |  |
| `panelsize_threshold` | Expected panelsize threshold which should be surpassed to calculate TMB | `integer` | 1000000 |  |  |

## Institutional config options

Parameters used to describe centralised config profiles. These should not be edited.

| Parameter | Description | Type | Default | Required | Hidden |
|-----------|-----------|-----------|-----------|-----------|-----------|
| `custom_config_version` | Git commit id for Institutional configs. | `string` | master |  | True |
| `custom_config_base` | Base directory for Institutional configs. <details><summary>Help</summary><small>If you're running offline, Nextflow will not be able to fetch the institutional config files from the internet. If you don't need them, then this is not a problem. If you do need them, you should download the files from the repo and tell Nextflow where to find them with this parameter.</small></details>| `string` | https://raw.githubusercontent.com/nf-core/configs/master |  | True |
| `config_profile_name` | Institutional config name. | `string` |  |  | True |
| `config_profile_description` | Institutional config description. | `string` |  |  | True |
| `config_profile_contact` | Institutional config contact information. | `string` |  |  | True |
| `config_profile_url` | Institutional config URL link. | `string` |  |  | True |

## Max job request options

Set the top limit for requested resources for any single job.

| Parameter | Description | Type | Default | Required | Hidden |
|-----------|-----------|-----------|-----------|-----------|-----------|
| `max_cpus` | Maximum number of CPUs that can be requested for any single job. <details><summary>Help</summary><small>Use to set an upper-limit for the CPU requirement for each process. Should be an integer e.g. `--max_cpus 1`</small></details>| `integer` | 16 |  |  |
| `max_memory` | Maximum amount of memory that can be requested for any single job. <details><summary>Help</summary><small>Use to set an upper-limit for the memory requirement for each process. Should be a string in the format integer-unit e.g. `--max_memory '8.GB'`</small></details>| `string` | 128.GB |  |  |
| `max_time` | Maximum amount of time that can be requested for any single job. <details><summary>Help</summary><small>Use to set an upper-limit for the time requirement for each process. Should be a string in the format integer-unit e.g. `--max_time '2.h'`</small></details>| `string` | 240.h |  | True |

## Generic options

Less common options for the pipeline, typically set in a config file.

| Parameter | Description | Type | Default | Required | Hidden |
|-----------|-----------|-----------|-----------|-----------|-----------|
| `help` | Display help text. | `boolean` |  |  | True |
| `version` | Display version and exit. | `boolean` |  |  | True |
| `publish_dir_mode` | Method used to save pipeline results to output directory. <details><summary>Help</summary><small>The Nextflow `publishDir` option specifies which intermediate files should be saved to the output directory. This option tells the pipeline what method should be used to move these files. See [Nextflow docs](https://www.nextflow.io/docs/latest/process.html#publishdir) for details.</small></details>| `string` | copy |  | True |
| `email_on_fail` | Email address for completion summary, only when pipeline fails. <details><summary>Help</summary><small>An email address to send a summary email to when the pipeline is completed - ONLY sent if the pipeline does not exit successfully.</small></details>| `string` |  |  | True |
| `plaintext_email` | Send plain-text email instead of HTML. | `boolean` |  |  | True |
| `max_multiqc_email_size` | File size limit when attaching MultiQC reports to summary emails. | `string` | 25.MB |  | True |
| `monochrome_logs` | Do not use coloured log outputs. | `boolean` |  |  | True |
| `hook_url` | Incoming hook URL for messaging service <details><summary>Help</summary><small>Incoming hook URL for messaging service. Currently, MS Teams and Slack are supported.</small></details>| `string` |  |  | True |
| `multiqc_config` | Custom config file to supply to MultiQC. | `string` |  |  | True |
| `multiqc_logo` | Custom logo file to supply to MultiQC. File name must also be set in the MultiQC config file | `string` |  |  | True |
| `multiqc_methods_description` | Custom MultiQC yaml file containing HTML including a methods description. | `string` |  |  |  |
| `multiqc_warnings_template` | Custom mutliQC template containing HTML coe to add warnings. | `string` |  |  |  |
| `tracedir` | Directory to keep pipeline Nextflow logs and reports. | `string` | ${params.outdir}/reports/pipeline_info |  | True |
| `validate_params` | Boolean whether to validate parameters against the schema at runtime | `boolean` | True |  | True |
| `schema_ignore_params` |  | `string` | genomes |  | True |
| `validationShowHiddenParams` | Show all params when using `--help` <details><summary>Help</summary><small>By default, parameters set as _hidden_ in the schema are not shown on the command line when a user runs with `--help`. Specifying this option will tell the pipeline to show all parameters.</small></details>| `boolean` |  |  | True |
| `validationFailUnrecognisedParams` | Validation of parameters fails when an unrecognised parameter is found. <details><summary>Help</summary><small>By default, when an unrecognised parameter is found, it returns a warinig.</small></details>| `boolean` |  |  | True |
| `validationLenientMode` | Validation of parameters in lenient more. <details><summary>Help</summary><small>Allows string values that are parseable as numbers or booleans. For further information see [JSONSchema docs](https://github.com/everit-org/json-schema#lenient-mode).</small></details>| `boolean` |  |  | True |
| `pipelines_testdata_base_path` | Base URL or local path to location of pipeline test dataset files | `string` | https://raw.githubusercontent.com/nf-core/test-datasets/ |  | True |
