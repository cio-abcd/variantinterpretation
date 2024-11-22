# variantinterpretation: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## dev

### `Added`

- support multi-sample VCF files (PR #44, Issue #35)
- updated nf-core template and restructured workflow (PR #47)
- support merging of vcf files (PR #49, Issue #36)
- updated nf-core modules (PR #50)
- support for "region-of-interest" tagging of variant calls outside of provided BED file (PR #51)
- added bcftools annotate/tabix/bgzip as nf-core modules (PR #51)

### Changed

- increase compatibility with calling workflow from another pipeline (PR #52)
    - moved scripts from bin/ to their respective module/resources/usr/bin
    - factored out MULTIQC from VARIANTINTERPRETATION workflow and called separately in main.nf
- moved prefix adaptions for better control of output names from bcftools_norm and ensembl_vep into corresponding config files

### `Fixed`

- fixed vembrane error by updating vembrane to 1.0.6 (PR #48, Issue #46)
- fixed samtools dict from getSimpleName to getBaseName (PR #43, Issue #42)
- fixed --vep_cache_version parameter to be interpreted as integer instead of string (Issue #45)

### `Dependencies`

### `Deprecated`

## v1.0.0 - [24th October 2023]

Initial release of cio-abcd/variantinterpretation, created with the [nf-core](https://nf-co.re/) template.
