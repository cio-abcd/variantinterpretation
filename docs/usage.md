# cio-abcd/variantinterpretation: Usage

:::note
If you are new to Nextflow and nf-core, please refer to [this page](https://nf-co.re/docs/usage/installation) on how
to set-up Nextflow.

<!-- Make sure to [test your setup](https://nf-co.re/docs/usage/introduction#how-to-run-a-pipeline)
with `-profile test` before running the workflow on actual data. -->

:::

## Introduction

This guide gives you a detailed step-by-step guide for running the variantinterpretation pipeline for the first time.
We are planning on adding a good example VCF file for testing the functionality of the pipeline after installation.
If you find any mistake or encounter errors please let us know, so we can improve this documentation.

Table of Contents:

1. [Installation](#installation): Nextflow and nf-core tools installation.
2. [Downloads](#downloads): Downloading workflow code and reference files.
3. [Configuration](#configuration): Samplesheet creation, preconfigured profiles and parameter setting.
4. [Running](#running): How to run the configure pipeline.
5. [Other core Nextflow functionalities](#other-core-nextflow-functionalities)
6. [Custom configuration](#custom-configuration)

## Installation

It is recommended, but not necessary, to use conda environments for installing nextflow and other software to ensure reproducibility.

1. Install [`Nextflow`](https://www.nextflow.io/docs/latest/getstarted.html#installation) (`>=22.10.1`)

2. Install any of [`Docker`](https://docs.docker.com/engine/installation/), [`Singularity`](https://www.sylabs.io/guides/3.0/user-guide/) (you can follow [this tutorial](https://singularity-tutorial.github.io/01-installation/)), [`Podman`](https://podman.io/), [`Shifter`](https://nersc.gitlab.io/development/shifter/how-to-use/) or [`Charliecloud`](https://hpc.github.io/charliecloud/) for full pipeline reproducibility _(you can use [`Conda`](https://conda.io/miniconda.html) both to install Nextflow itself and also to manage software within pipelines. Please only use it within pipelines as a last resort; see [docs](https://nf-co.re/usage/configuration#basic-configuration-profiles))_.

3. Optional: Install the ["nf-core tools"](https://nf-co.re/tools) providing command-line tools for download, configuration and development. Highly recommended.

## Downloads

### Download the pipeline code

You can either clone this github repository or use `nf-core download` from the nf-core tools software package.
It helps downloading specific workflow releases or branches, institutional config files and singularity software images.

```bash
nf-core download cio-abcd/variantinterpretation
```

#### Updating the pipeline

Note that when running the pipeline directly without previous download of the pipeline code, Nextflow automatically pulls the pipeline code from GitHub and stores it as a cached version. When running the pipeline after this, it will always use the cached version if available - even if the pipeline has been updated since. To make sure that you're running the latest version of the pipeline, make sure that you regularly update the cached version of the pipeline:

```bash
nextflow pull cio-abcd/variantinterpretation
```

#### Reproducibility

It is a good idea to specify a pipeline version when running the pipeline on your data. This ensures that a specific version of the pipeline code and software are used when you run your pipeline. If you keep using the same tag, you'll be running the same version of the pipeline, even if there have been changes to the code since.

First, go to the [cio-abcd/variantinterpretation releases page](https://github.com/cio-abcd/variantinterpretation/releases) and find the latest pipeline version - numeric only (eg. `1.3.1`). Then specify this when running the pipeline with `-r` (one hyphen) - eg. `-r 1.3.1`. Of course, you can switch to another version by changing the number after the `-r` flag.

This version number will be logged in reports when you run the pipeline, so that you'll know what you used when you look back in the future. For example, at the bottom of the MultiQC reports.

To further assist in reproducbility, you can use share and re-use [parameter files](#running-the-pipeline) to repeat pipeline runs with the same settings without having to write out a command with every single parameter.

:::tip
If you wish to share such profile (such as upload as supplementary material for academic publications), make sure to NOT include cluster specific paths to files, nor institutional specific profiles.
:::

### Download reference files

The workflow requires a reference genome and annotation sources.

- The **reference genome** is provided in FASTA format using the parameter `--fasta`. It is also possible to use the nf-core `igenomes` resource specified with `--igenomes_base` option (more information [here](https://nf-co.re/docs/usage/reference_genomes)).
- **Annotation resources** are provided through VEP cache with the `---vep_cache` parameter.
  The version of the VEP cache needs to match the used VEP version (v110). More information can be found on the [ensembl website](http://www.ensembl.org/info/docs/tools/vep/script/vep_cache.html) and is shortly summarized here:
  The VEP cache can be downloaded from the ensembl FTP server (https://ftp.ensembl.org/pub/release-110/variation/) using `curl` in different flavors: - either indexed or non-indexed cache (folder `indexed_vep_cache/` or `vep/`) - with different species (e.g., homo_sapiens). - for human genome: GRCh37 or GRCh38 reference genome (defined with `--vep_genome` parameter). - either with the standard cache using ensembl transcripts, the refseq cache with NCBI transcript definitions (NM-numbers) or merged cache with both. This type has to be specified with the `--vep_cache_source` parameter.

For example for non-indexed, homo_sapiens, GRCh38 refseq cache download and untar:

```
cd $HOME/.vep
curl -O https://ftp.ensembl.org/pub/release-110/variation/vep/homo_sapiens_refseq_vep_110_GRCh38.tar.gz
tar xzf homo_sapiens_vep_110_GRCh38.tar.gz
```

## Configuration

### Create samplesheet with input VCF files.

You will need to create a samplesheet with information about the samples you would like to analyze before running the pipeline. Use the `--input` parameter to specify its location. It has to be a comma-separated file with 2 columns and a header row as shown in the example below.

The samplesheet can have as many columns as you desire, however, there is a strict requirement for the first 2 columns to match those defined in the table below.
A final samplesheet file consisting of vcf files may look something like the one below for 6 samples.

```console
sample,vcf
CONTROL_REP1,AEG588A1.vcf.gz
CONTROL_REP2,AEG588A2.vcf.gz
CONTROL_REP3,AEG588A3.vcf.gz
TREATMENT_REP1,AEG588A4.vcf.gz,
TREATMENT_REP2,AEG588A5.vcf.gz,
TREATMENT_REP3,AEG588A6.vcf.gz
```

| Column   | Description                                                                                                                                                                            |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sample` | Custom sample name. This entry will be identical for multiple sequencing libraries/runs from the same sample. Spaces in sample names are automatically converted to underscores (`_`). |
| `vcf`    | Full path to vcf file. File has to be either uncompressed with ".vcf" extension or bgzipped and with ".vcf. gz" extension.                                                             |

An [example samplesheet](../assets/samplesheet.csv) has been provided with the pipeline.

### **Configuration profiles** for software containers and institutional configs.

Note that some form of configuration will be needed so that Nextflow knows how to fetch the required software. This is usually done in the form of a config profile that is defined with the `-profile` nextflow parameter. Profiles can give configuration presets for different compute environments.

> - The pipeline comes with config profiles called `docker`, `singularity`, `podman`, `shifter`, `charliecloud` and `conda` which instruct the pipeline to use the named container tool for software management. For example, `-profile test,docker`. More detailed information can be found below.
>   We highly recommend the use of Docker or Singularity containers for full pipeline reproducibility, however when this is not possible, Conda is also supported.
> - If you are using `singularity`, please use the [`nf-core download`](https://nf-co.re/tools/#downloading-pipelines-for-offline-use) command to download images first, before running the pipeline. Setting the [`NXF_SINGULARITY_CACHEDIR` or `singularity.cacheDir`](https://www.nextflow.io/docs/latest/singularity.html?#singularity-docker-hub) Nextflow options enables you to store and re-use the images from a central location for future pipeline runs.
> - If you are using `conda`, it is highly recommended to use the [`NXF_CONDA_CACHEDIR` or `conda.cacheDir`](https://www.nextflow.io/docs/latest/conda.html) settings to store the environments in a central location for future pipeline runs.

The pipeline also dynamically loads configurations from [https://github.com/nf-core/configs](https://github.com/nf-core/configs) when it runs, making multiple config profiles for various institutional clusters available at run time. For more information and to see if your system is available in these configs please see the [nf-core/configs documentation](https://github.com/nf-core/configs#documentation). If available, you can simply use `-profile <institute>` in your command.

Note that multiple profiles can be loaded, for example: `-profile test,docker` - the order of arguments is important!
They are loaded in sequence, so later profiles can overwrite earlier profiles.

If `-profile` is not specified, the pipeline will run locally and expect all software to be installed and available on the `PATH`. This is _not_ recommended, since it can lead to different results on different machines dependent on the computer enviroment.

- `test`
  - A profile with a complete configuration for automated testing
  - Includes links to test data so needs no other parameters
- `docker`
  - A generic configuration profile to be used with [Docker](https://docker.com/)
- `singularity`
  - A generic configuration profile to be used with [Singularity](https://sylabs.io/docs/)
- `podman`
  - A generic configuration profile to be used with [Podman](https://podman.io/)
- `shifter`
  - A generic configuration profile to be used with [Shifter](https://nersc.gitlab.io/development/shifter/how-to-use/)
- `charliecloud`
  - A generic configuration profile to be used with [Charliecloud](https://hpc.github.io/charliecloud/)
- `apptainer`
  - A generic configuration profile to be used with [Apptainer](https://apptainer.org/)
- `conda`
  - A generic configuration profile to be used with [Conda](https://conda.io/docs/). Please only use Conda as a last resort i.e. when it's not possible to run the pipeline with Docker, Singularity, Podman, Shifter, Charliecloud, or Apptainer.

### **Configure parameters** to launch variantinterpretation workflow.

The best way to configure the pipeline is by creating a separate parameter file `nf-params.json` and supplying it using the `-params-file` nextflow parameter.
It is highly recommended to define these parameters with

```
nf-core launch -ax vio-abcd/variantinterpretation
```

:::note
The flags `-a` saves all parameters, even defaults, for better reproducibility and `-x` also shows hidden parameters.
:::

It opens a web-based interface to define the parameters showing helpful descriptions, default values and constraints for each parameter. You can also find the description of parameters in [docs/params.md](../docs/params.md) and lots of additional information in the [README.md](../README.md).

## Running

Now that you downloaded and configured the pipeline you can finally start running your own analysis!
The typical command for running the pipeline is as follows:

```bash
nextflow run cio-abcd/variantinterpretation \
    -params-file nf-params.json \
    -profile docker/singularity/podman/shifter/charliecloud/conda/institute> \
    --vep_cache $HOME/.vep
```

:::note
The `--vep_cache` parameter needs to be defined in the `nextflow run` command and _not_ within the nf-params.json file.
If using the igenomes resource, the `--igenomes_base` parameter also needs to be specified in the `nextflow run` command and not in the `nf-params.json` file.
:::

:::warning
Please provide pipeline parameters via the CLI or Nextflow `-params-file` option. Custom config files including those
provided by the `-c` Nextflow option can be used to provide any configuration _**except for parameters**_;
see [docs](https://nf-co.re/usage/configuration#custom-configuration-files).
:::

The pipeline will create the following files in your working directory:

```bash
work                # Directory containing the nextflow working files
<OUTDIR>            # Finished results in specified location (defined with --outdir)
.nextflow_log       # Log file from Nextflow
# Other nextflow hidden files, eg. history of pipeline runs and old logs.
```

## Other core Nextflow functionalities

### **Configure parameters** to launch variantinterpretation workflow.

The best way to configure the pipeline is by creating a separate parameter file `nf-params.json` and supplying it using the `-params-file` nextflow parameter.
It is highly recommended to define these parameters with

```
nf-core launch -a vio-abcd/variantinterpretation
```

It opens a web-based interface to define the parameters showing helpful descriptions, default values and constraints for each parameter.

## Running

Now that you downloaded and configured the pipeline you can finally start running your own analysis!
The typical command for running the pipeline is as follows:

```bash
nextflow run cio-abcd/variantinterpretation -params-file nf-params.json -profile docker/singularity/podman/shifter/charliecloud/conda/institute> --vep_cache $HOME/.vep
```

> NOTE: The `--vep_cache` parameter needs to be defined in the `nextflow run` command and not within the nf-params.json file.
> NOTE: If using the igenomes resource, the `--igenomes_base` parameter also needs to be specified in the `nextflow run` command and not in the `nf-params.json` file.

The pipeline will create the following files in your working directory:

```bash
work                # Directory containing the nextflow working files
<OUTDIR>            # Finished results in specified location (defined with --outdir)
.nextflow_log       # Log file from Nextflow
# Other nextflow hidden files, eg. history of pipeline runs and old logs.
```

## Other core Nextflow functionalities

### `-resume`

Specify this when restarting a pipeline. Nextflow will use cached results from any pipeline steps where the inputs are the same, continuing from where it got to previously. For input to be considered the same, not only the names must be identical but the files' contents as well. For more info about this parameter, see [this blog post](https://www.nextflow.io/blog/2019/demystifying-nextflow-resume.html).

You can also supply a run name to resume a specific run: `-resume [run-name]`. Use the `nextflow log` command to show previous run names.

### `-c`

Specify the path to a specific config file (this is a core Nextflow command). See the [nf-core website documentation](https://nf-co.re/usage/configuration) for more information.

### Running in the background

Nextflow handles job submissions and supervises the running jobs. The Nextflow process must run until the pipeline is finished.

The Nextflow `-bg` flag launches Nextflow in the background, detached from your terminal so that the workflow does not stop if you log out of your session. The logs are saved to a file.

Alternatively, you can use `screen` / `tmux` or similar tool to create a detached session which you can log back into at a later time.
Some HPC setups also allow you to run nextflow within a cluster job submitted your job scheduler (from where it submits more jobs).

## Custom configuration

### Resource requests

Whilst the default requirements set within the pipeline will hopefully work for most people and with most input data, you may find that you want to customise the compute resources that the pipeline requests. Each step in the pipeline has a default set of requirements for number of CPUs, memory and time. For most of the steps in the pipeline, if the job exits with any of the error codes specified [here](https://github.com/nf-core/rnaseq/blob/4c27ef5610c87db00c3c5a3eed10b1d161abf575/conf/base.config#L18) it will automatically be resubmitted with higher requests (2 x original, then 3 x original). If it still fails after the third attempt then the pipeline execution is stopped.

To change the resource requests, please see the [max resources](https://nf-co.re/docs/usage/configuration#max-resources) and [tuning workflow resources](https://nf-co.re/docs/usage/configuration#tuning-workflow-resources) section of the nf-core website.

### Custom Containers

In some cases you may wish to change which container or conda environment a step of the pipeline uses for a particular tool. By default nf-core pipelines use containers and software from the [biocontainers](https://biocontainers.pro/) or [bioconda](https://bioconda.github.io/) projects. However in some cases the pipeline specified version maybe out of date.

To use a different container from the default container or conda environment specified in a pipeline, please see the [updating tool versions](https://nf-co.re/docs/usage/configuration#updating-tool-versions) section of the nf-core website.

### Custom Tool Arguments

A pipeline might not always support every possible argument or option of a particular tool used in pipeline. Fortunately, nf-core pipelines provide some freedom to users to insert additional parameters that the pipeline does not include by default.

To learn how to provide additional arguments to a particular tool of the pipeline, please see the [customising tool arguments](https://nf-co.re/docs/usage/configuration#customising-tool-arguments) section of the nf-core website.

### Azure Resource Requests

To be used with the `azurebatch` profile by specifying the `-profile azurebatch`.
We recommend providing a compute `params.vm_type` of `Standard_D16_v3` VMs by default but these options can be changed if required.

Note that the choice of VM size depends on your quota and the overall workload during the analysis.
For a thorough list, please refer the [Azure Sizes for virtual machines in Azure](https://docs.microsoft.com/en-us/azure/virtual-machines/sizes).

### Nextflow memory requirements

In some cases, the Nextflow Java virtual machines can start to request a large amount of memory.
We recommend adding the following line to your environment to limit this (typically in `~/.bashrc` or `~./bash_profile`):

```bash
NXF_OPTS='-Xms1g -Xmx4g'
```
