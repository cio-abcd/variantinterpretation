# variantinterpretation: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## dev

### `Added`

- support multi-sample VCF files according to issue #35
- updated nf-core template and restructured workflow
- support merging of vcf files according to issue #36
- updated nf-core modules

### Changed

- moved scripts from bin/ to their respective module/resources/usr/bin
- factored out VARIANTINTERPRETATION_CORE without MULTIQC from VARIANTINTERPRETATION workflow

### `Fixed`

- fixed vembrane error by updating vembrane to 1.0.6 (Issue #46)

### `Dependencies`

### `Deprecated`

## v1.0.0 - [24th October 2023]

Initial release of cio-abcd/variantinterpretation, created with the [nf-core](https://nf-co.re/) template.
