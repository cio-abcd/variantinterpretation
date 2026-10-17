# variantinterpretation: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.2.0 - [unreleased<!-- TODO nf-core: replace with date on release -->]

### `Changed`

- updated pipeline to Nextflow strict syntax to be executable with nextflow v26: `nextflow lint` (Nextflow 26.04) reports no errors (AI-assisted, Claude Code)
  - `check_max()` replaced by the Nextflow `process.resourceLimits` directive (requires Nextflow >= 24.04); the params `max_cpus`, `max_memory` and `max_time` are removed. **Breaking:** set `process { resourceLimits = [cpus: ..., memory: ..., time: ...] }` in your own config instead. `resourceLimits` also caps plain `withName` overrides, unlike `check_max()`
  - config `try`/`catch`, `if` and `def` replaced by conditional `includeConfig` and the new hidden param `trace_report_suffix`; removed the include of `pipeline/variantinterpretation.config`, which does not exist in nf-core/configs
  - input channels are created inside `CIOABCD_VARIANTINTERPRETATION` instead of at the top level of `main.nf`
  - updated nf-core subworkflows `utils_nextflow_pipeline` and `utils_nfcore_pipeline` (the latter patched to keep `workflowCitation`, `nfCoreLogo`, `dashedLine` and `imNotification`)
  - patched nf-core modules `bcftools/annotate` (stub only), `bcftools/index`, `bcftools/merge` and `bcftools/norm` without changing their versions or containers
  - quoted `env` outputs, renamed shadowing variables, explicit closure parameters, `channel` instead of `Channel`, removed unused variables
  - no change in results: stub runs with Nextflow 25.10.4 and 26.04.4 give the same tasks, resources and published files as v1.2.0
- updated nf-core template to v4.1.
  - updated multiQC module to v1.35
  - require now at least nextflow >=25.10.4
  - also chnaged from nf-validation to nf-schema plugin

## v1.2.0

### `Fixed`

- fixed comma-separated input from parameters `used_filter`, `annotation_fields`, `info_fields` and `format_fields` (Issue #39)
- Updated nf-core modules, including ensemblvep from v113 to v115

## v1.1.0 - [1st September 2025]

### `Added`

- support multi-sample VCF files (PR #44, Issue #35)
- updated nf-core template and restructured workflow (PR #47)
- support merging of vcf files (PR #49, Issue #36)
- updated nf-core modules (PR #50)
- support for "region-of-interest" tagging of variant calls outside of provided BED file (PR #51)
- added bcftools annotate/tabix/bgzip as nf-core modules (PR #51)
- added multi-sample support for TMB_CALCULATE (PR #56)
- added separate region-of-interest filter independent of `--tag_roi` + `--filter_vcf` for TMB_CALCULATE (PR #56)
- added VEP consequence filter for TMB_CALCULATE (PR #56)

### `Changed`

- increase compatibility with calling workflow from another pipeline (PR #52)
  - moved scripts from bin/ to their respective module/resources/usr/bin
  - factored out MULTIQC from VARIANTINTERPRETATION workflow and called separately in main.nf
- moved prefix adaptions for better control of output names from bcftools_norm and ensembl_vep into corresponding config files
- changed BEDCHECK module to check BED file format and automatically generate a compatible minimized BED file for downstream processes (PR #51 discussion)
- changed BEDCHECK to allow eligible BED files to be further used for annotation purposes

### `Fixed`

- fixed vembrane error by updating vembrane to 1.0.6 (PR #48, Issue #46)
- fixed samtools dict from getSimpleName to getBaseName (PR #43, Issue #42)
- fixed --vep_cache_version parameter to be interpreted as integer instead of string (Issue #45)
- fixed missing bgzip-compression step in VCFPROC subworkflow
- fixed TMB_CALCULATE and refactored code for better readability

### `Dependencies`

### `Deprecated`

## v1.0.0 - [24th October 2023]

Initial release of cio-abcd/variantinterpretation, created with the [nf-core](https://nf-co.re/) template.
