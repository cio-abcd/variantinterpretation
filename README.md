<!-- [![Cite with Zenodo](http://img.shields.io/badge/DOI-10.5281/zenodo.XXXXXXX-1073c8?labelColor=000000)](https://doi.org/10.5281/zenodo.XXXXXXX)-->
# ![cio-abcd/variantinterpretation](docs/images/nf-core-variantinterpretation_logo_light.png#gh-light-mode-only) ![cio-abcd/variantinterpretation](docs/images/nf-core-variantinterpretation_logo_dark.png#gh-dark-mode-only)

[![GitHub Actions CI Status](https://github.com/cio-abcd/variantinterpretation/workflows/nf-core%20CI/badge.svg)](https://github.com/cio-abcd/variantinterpretation/actions?query=workflow%3A%22nf-core+CI%22)
[![GitHub Actions Linting Status](https://github.com/cio-abcd/variantinterpretation/workflows/nf-core%20linting/badge.svg)](https://github.com/cio-abcd/variantinterpretation/actions?query=workflow%3A%22nf-core+linting%22)[![AWS CI](https://img.shields.io/badge/CI%20tests-full%20size-FF9900?labelColor=000000&logo=Amazon%20AWS)](https://nf-co.re/variantinterpretation/results)[![Cite with Zenodo](http://img.shields.io/badge/DOI-10.5281/zenodo.XXXXXXX-1073c8?labelColor=000000)](https://doi.org/10.5281/zenodo.XXXXXXX)

[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A523.04.0-23aa62.svg)](https://www.nextflow.io/)
[![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/)
[![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/)
[![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)
[![Launch on Nextflow Tower](https://img.shields.io/badge/Launch%20%F0%9F%9A%80-Nextflow%20Tower-%234256e7)](https://tower.nf/launch?pipeline=https://github.com/cio-abcd/variantinterpretation)

## Introduction

The pipeline takes as input SNVs and short InDels in VCF file format and annotates them using Ensembl variant effect predictor (VEP). Several parameters in VEP annotation can be configured through this workflow.

**variantinterpretation** is a bioinformatics best-practice analysis pipeline for adding biological and clinical knowledge to genomic variants.

The pipeline is built using [Nextflow](https://www.nextflow.io), a workflow tool to run tasks across multiple compute infrastructures in a very portable manner. It uses Docker/Singularity containers making installation trivial and results highly reproducible. The [Nextflow DSL2](https://www.nextflow.io/docs/latest/dsl2.html) implementation of this pipeline uses one container per process which makes it much easier to maintain and update software dependencies. Where possible, these processes have been submitted to and installed from [nf-core/modules](https://github.com/nf-core/modules) in order to make them available to all nf-core pipelines, and to everyone within the Nextflow community!

<!-- TODO nf-core: Add full-sized test dataset and amend the paragraph below if applicable -->

<!-- On release, automated continuous integration tests run the pipeline on a full-sized dataset on the AWS cloud infrastructure. This ensures that the pipeline runs on AWS, has sensible resource allocation defaults set to run on real-world datasets, and permits the persistent storage of results to benchmark between pipeline releases and other analysis sources.-->

<!-- TODO nf-core: Include a figure that guides the user through the major workflow steps. Many nf-core
     workflows use the "tube map" design for that. See https://nf-co.re/docs/contributing/design_guidelines#examples for examples.   -->

1. Run Samplesheet check with modified [nf-core script](bin/check_samplesheet.py)
2. Run format check on optionally provided BED file using a [python script](bin/check_bedfiles.py)
3. Annotation using [Ensembl variant effect predictor (VEP)](https://www.ensembl.org/info/docs/tools/vep/index.html).
4. Filtering of transcripts using [filter_vep script](https://www.ensembl.org/info/docs/tools/vep/script/vep_filter.html).
5. Generate a TSV file based on VCF columns including FORMAT and INFO fields and the [VEP annotation fields](https://www.ensembl.org/info/docs/tools/vep/vep_formats.html#output) encoded as CSQ strings in the INFO field using [vembrane table](https://github.com/vembrane/vembrane).
6. Calculate TMB based on provided cutoffs and thresholds for each sample using a [python script](bin/calculate_TMB.py) from the Vembrane TSV output
7. Generate a HTML report using [datavzrd](https://github.com/datavzrd/datavzrd#readme).
8. Run MultiQC ([`MultiQC`](http://multiqc.info/))

## Quick Start

:::note
If you are new to Nextflow and nf-core, please refer to [this page](https://nf-co.re/docs/usage/installation) on how
to set-up Nextflow. Make sure to [test your setup](https://nf-co.re/docs/usage/introduction#how-to-run-a-pipeline)
with `-profile test` before running the workflow on actual data.
:::

A detailed step-by-step guide for using this workflow and also for beginners with nextflow and nf-core pipelines can be found in the [usage documentation](docs/usage.md).
Further you can find detailed descriptions of the output files in the [output documentation](docs/output.md).

2. Install any of [`Docker`](https://docs.docker.com/engine/installation/), [`Singularity`](https://www.sylabs.io/guides/3.0/user-guide/) (you can follow [this tutorial](https://singularity-tutorial.github.io/01-installation/)), [`Podman`](https://podman.io/), [`Shifter`](https://nersc.gitlab.io/development/shifter/how-to-use/) or [`Charliecloud`](https://hpc.github.io/charliecloud/) for full pipeline reproducibility _(you can use [`Conda`](https://conda.io/miniconda.html) both to install Nextflow itself and also to manage software within pipelines. Please only use it within pipelines as a last resort; see [docs](https://nf-co.re/usage/configuration#basic-configuration-profiles))_.

3. Download the pipeline and test it on a minimal dataset with a single command:

```bash
nextflow run variantinterpretation -profile test,YOURPROFILE --outdir <OUTDIR>
```

Note that some form of configuration will be needed so that Nextflow knows how to fetch the required software. This is usually done in the form of a config profile (`YOURPROFILE` in the example command above). You can chain multiple config profiles in a comma-separated string.

> - The pipeline comes with config profiles called `docker`, `singularity`, `podman`, `shifter`, `charliecloud` and `conda` which instruct the pipeline to use the named tool for software management. For example, `-profile test,docker`.
> - Please check [nf-core/configs](https://github.com/nf-core/configs#documentation) to see if a custom config file to run nf-core pipelines already exists for your Institute. If so, you can simply use `-profile <institute>` in your command. This will enable either `docker` or `singularity` and set the appropriate execution settings for your local compute environment.
> - If you are using `singularity`, please use the [`nf-core download`](https://nf-co.re/tools/#downloading-pipelines-for-offline-use) command to download images first, before running the pipeline. Setting the [`NXF_SINGULARITY_CACHEDIR` or `singularity.cacheDir`](https://www.nextflow.io/docs/latest/singularity.html?#singularity-docker-hub) Nextflow options enables you to store and re-use the images from a central location for future pipeline runs.
> - If you are using `conda`, it is highly recommended to use the [`NXF_CONDA_CACHEDIR` or `conda.cacheDir`](https://www.nextflow.io/docs/latest/conda.html) settings to store the environments in a central location for future pipeline runs.

4. Start running your own analysis!

Specify parameters best using `nf-core launch` and add to run command.

```bash
nextflow run variantinterpretation -params-file nf-params.json -profile <docker/singularity/podman/shifter/charliecloud/conda/institute>
```


:::warning
Please provide pipeline parameters via the CLI or Nextflow `-params-file` option. Custom config files including those
provided by the `-c` Nextflow option can be used to provide any configuration _**except for parameters**_;
see [docs](https://nf-co.re/usage/configuration#custom-configuration-files).
:::

For more details and further functionality, please refer to the [usage documentation](docs/usage.md).

## Pipeline output

To see the results of an example test run with a full size dataset refer to the [results](https://nf-co.re/variantinterpretation/results) tab on the nf-core website pipeline page.
For more details about the output files and reports, please refer to the
[output documentation](https://nf-co.re/variantinterpretation/output).

## Contributions and Support

This Pipeline development repository is a collaborative effort of the Center for Integrated Oncology of the Universities of Aachen, Bonn, Cologne and Düsseldorf to standardize and optimize data analysis in a clinical context.
TODO: Add Information on CIO and ZPM.
If you would like to contribute to this pipeline, please see the [contributing guidelines](.github/CONTRIBUTING.md).

**Contributing authors**

- RWTH University Hospital (UKA): Lancelot Seillier
- University Hospital Bonn (UKB): Patrick Basitta, Florian Hölscher
- University Hospital Köln (UKK): tba
- University Hospital Düsseldorf (UKD): Kai Horny

**Further contributors**

TBA

## Citations

<!-- TODO nf-core: Add citation for pipeline after first release. Uncomment lines below and update Zenodo doi and badge at the top of this file. -->
<!-- If you use  variantinterpretation for your analysis, please cite it using the following doi: [10.5281/zenodo.XXXXXX](https://doi.org/10.5281/zenodo.XXXXXX) -->

<!-- TODO nf-core: Add bibliography of tools and data used in your pipeline -->

An extensive list of references for the tools used by the pipeline can be found in the [`CITATIONS.md`](CITATIONS.md) file.

You can cite the `nf-core` publication as follows:

> **The nf-core framework for community-curated bioinformatics pipelines.**
>
> Philip Ewels, Alexander Peltzer, Sven Fillinger, Harshil Patel, Johannes Alneberg, Andreas Wilm, Maxime Ulysse Garcia, Paolo Di Tommaso & Sven Nahnsen.
>
> _Nat Biotechnol._ 2020 Feb 13. doi: [10.1038/s41587-020-0439-x](https://dx.doi.org/10.1038/s41587-020-0439-x).
