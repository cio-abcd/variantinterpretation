#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import pyranges as pr
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse
import logging
import sys

logger = logging.getLogger()


def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate TMB and plot AF distribution",
        epilog="Example: python3 calculate_TMB.py --file_in input.tsv --sampleindex SAMPLE01",
    )
    parser.add_argument(
        "--file_in",
        metavar="file_in",
        type=Path,
        help="Input TSV file of the vembrane TSV converter module",
    )
    parser.add_argument(
        "--sampleindex",
        metavar="sampleindex",
        type=str,
        help="Sample index based on meta.id of the input file",
    )
    parser.add_argument(
        "--bedfile",
        metavar="bedfile",
        type=Path,
        help="Path to the provided BED file with .bed suffix.",
    )
    parser.add_argument(
        "--prefilter_region",
        action="store_true",
        help="Filter the TMB calculation to only the defined bedfile range.",
    )
    parser.add_argument(
        "--panelsize_threshold",
        metavar="panelsize_threshold",
        type=int,
        help="Expected minimal size of the BED-file before giving an error.",
    )
    parser.add_argument(
        "--min_AF",
        metavar="min_AF",
        type=float,
        help="Minimal AF threshold for the filtering procedure of the TMB module",
    )
    parser.add_argument(
        "--max_AF",
        metavar="max_AF",
        type=float,
        help="Maximal AF threshold for the filtering procedure of the TMB module",
    )
    parser.add_argument(
        "--min_cov",
        metavar="min_cov",
        type=int,
        help="Minimal coverage threshold for the filtering procedure of the TMB module",
    )
    parser.add_argument(
        "--popfreq_max",
        metavar="popfreq_max",
        type=float,
        help="Maximal prevalence AF in the --population_db database",
    )
    parser.add_argument(
        "--filter_muttype",
        metavar="filter_muttype",
        type=str,
        choices=["snv", "snvs", "mnv", "mnvs"],
        help="Set the conditions for filtering, either selecting only SNVs, SNVs and MNVs or the whole dataset including InDels",
    )
    parser.add_argument(
        "--filter_consequence",
        metavar="filter_consequence",
        type=str,
        help="Path to csv-file containing the VEP consequences to retain for TMB calculation",
    )
    parser.add_argument(
        "--population_db",
        metavar="population_db",
        type=str,
        help="String corresponding to the column name of the desired population database to filter on.",
    )
    parser.add_argument(
        "--file_out",
        metavar="FILE_OUT",
        type=Path,
        help="Per Sample TMB value",
    )
    parser.add_argument(
        "--plot_out",
        metavar="PLOT_OUT",
        type=Path,
        help="Stacked histogramm of the AFs in the sample",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="The desired log level (default WARNING).",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        default="WARNING",
    )
    return parser.parse_args(argv)


logger = logging.getLogger()

def multisample_check(file_in):
    ### Read in sample
    TMB_multicontrol = pd.read_csv(file_in, sep="\t")
    ### Generate boolean based on AF column if single- or multisample
    multi_control = len(TMB_multicontrol.filter(regex='allele_fraction*').columns) > 1 ### check based on AF
    ### Isolate sample suffix(es)
    matching_columns = [col for col in TMB_multicontrol.columns if col.startswith('allele_fraction')]
    suffix_list = list(map( lambda x: x.replace('allele_fraction', ''), matching_columns))
    ### Return all relevant variables
    return (multi_control, suffix_list)

def preprocess_vembraneout(file_in, allele_fraction, read_depth, filter_muttype, population_db, filter_consequence):
    TMB_inputfile = pd.read_csv(file_in, sep="\t")
    filtering_rates = []
    TMB_inputfile["Mut_ID"] = TMB_inputfile[["CHROM", "POS", "REF", "ALT"]].apply(
        lambda row: ":".join(row.values.astype(str)), axis=1
    )
    ### move consequence filter into preprocessing to circumvent deduplication pitfall
    TMB_consequence, filtering_csq = consequence_filter(TMB_inputfile, filter_consequence)
    filtering_rates.append(filtering_csq)
    TMB_deduplicated = TMB_consequence.drop_duplicates("Mut_ID", keep="first")
    filtering_rates.append(len(TMB_deduplicated["Mut_ID"]))
    ### reduce dataset on relevant columns for TMB calculation
    TMB_minimal = TMB_deduplicated.filter(
        items=[
            "Mut_ID",
            "CHROM",
            "POS",
            "REF",
            "ALT",
            "FILTER",
            allele_fraction,
            read_depth,
            "CSQ_VARIANT_CLASS",
            "CSQ_Consequence",
            population_db,
        ],
        axis=1,
    )
    if filter_muttype in ["snv", "snvs"]:
        TMB_filtered = filter_onlySNV(TMB_minimal)
    elif filter_muttype in ["mnv", "mnvs"]:
        TMB_filtered = filter_retainMNV(TMB_minimal)
    else:
        TMB_filtered = TMB_minimal
    filtering_rates.append(len(TMB_filtered["Mut_ID"]))
    ### Generate position specific identifier for deduplication / counting
    return (TMB_filtered, filtering_rates)

def filter_onlySNV(TMB_inputfile):
    TMB_onlySNV = TMB_inputfile[
        (TMB_inputfile["REF"].isin(["A", "G", "T", "C"]))
        & (TMB_inputfile["ALT"].isin(["A", "G", "T", "C"]))
    ].reset_index(drop=True)
    if TMB_onlySNV["CSQ_VARIANT_CLASS"].eq("SNV").all():
        return TMB_onlySNV
    else:
        TMB_onlySNV = TMB_onlySNV[(TMB_onlySNV["CSQ_VARIANT_CLASS"] == "SNV")]
        return TMB_onlySNV

def filter_retainMNV(TMB_inputfile):
    TMB_SNVs = TMB_inputfile[
        (TMB_inputfile["REF"].isin(["A", "G", "T", "C"]))
        & (TMB_inputfile["ALT"].isin(["A", "G", "T", "C"]))
    ].reset_index(drop=True)
    TMB_MNVs = TMB_inputfile[
        (TMB_inputfile["CSQ_VARIANT_CLASS"] == "substitution")
    ].reset_index(
        drop=True
    )  ### contains DBS, SNVs close to repeats and non-normalized SNVs close to InDels
    TMB_return = pd.concat([TMB_SNVs, TMB_MNVs])
    return TMB_return

def csq_match(row, values):
    row_values = row.split('&')
    return any(value in row_values for value in values)

def consequence_filter(TMB_inputfile, filter_consequence):
    TMB_prefilt = TMB_inputfile.copy()
    with open(filter_consequence, 'r') as file:
            csq_raw = file.read().strip()
            if not csq_raw:
                raise ValueError("The filter file is empty. Please provide valid filter values.")
            csq_values = csq_raw.split(',')
    TMB_filt = TMB_prefilt[TMB_prefilt["CSQ_Consequence"].apply(lambda x: csq_match(x, csq_values))]
    filtering_rates = len(TMB_filt.index)
    return (TMB_filt, filtering_rates)


def filter_bedrange(TMB_inputfile, bedfile):
    ### Separate filter for ROI independant of tag_roi
    ### Read bedfile and convert to range
    panel_data = pd.read_csv(bedfile, sep="\t", header=None)
    panel_data = panel_data.iloc[:, 0:3]
    panel_data.columns = ["Chromosome", "Start", "End"]
    panel_range = pr.PyRanges(panel_data)
    ### Read in data
    TMB_prefilt = TMB_inputfile.copy()
    TMB_prefilt = TMB_prefilt[["CHROM", "POS"]].rename(columns={"CHROM": "Chromosome", "POS": "Start"})
    TMB_prefilt['End'] = TMB_prefilt['Start']
    TMB_range = pr.PyRanges(TMB_prefilt)
    ### Create intersection and return ROI-filtered dataframe
    TMB_intersect = panel_range.intersect(TMB_range)
    TMB_intersect_df = TMB_intersect.df.rename(columns={"Chromosome": "CHROM", "Start": "POS"}).iloc[:,0:2]
    ### Check if the intersection df is not empty and pass a warning parameter to output writer
    if len(TMB_intersect_df.index) > 0:
        TMB_filt = pd.merge(TMB_inputfile, TMB_intersect_df[["CHROM", "POS"]], on=["CHROM", "POS"])
        is_notempty = True
        return (TMB_filt, is_notempty)
    else:
        TMB_filt = TMB_inputfile
        is_notempty = False
        return (TMB_filt, is_notempty)

def check_bed_size(bedfile, breaking_thresh):
    panel_data = pd.read_csv(bedfile, sep="\t", header=None)
    panel_data = panel_data.iloc[:, 0:3]
    panel_data.columns = ["Chromosome", "Start", "End"]
    panel_range = pr.PyRanges(panel_data)
    panel_size = panel_range.length
    if panel_size >= breaking_thresh:
        if panel_size >= 1000000:
            logger.info(
                "The provided BED file covers "
                + str(panel_size)
                + " basepairs. It covers more than 1 Mbp. TMB calculation can be performed"
            )
            return True, panel_size
        else:
            logger.warning(
                "The provided BED file covers "
                + str(panel_size)
                + " basepairs. It covers less than 1 Mbp, but is above the breaking threshold. TMB calculation can be performed, but could be biased."
            )
            return True, panel_size
    elif panel_size < breaking_thresh:
        logger.warning(
            "The provided BED file covers "
            + str(panel_size)
            + " basepairs, but does not surpass the threshold for TMB calculation. Reconsider the threshold or provide an actualized BED-file."
        )
        return False, panel_size
    else:
        logger.warning(
            "An unexpected error occured while parsing the BED-file size. TMB calculation will not be performed."
        )
        return False, False


def coverage_filter(input, read_depth, threshold):
    TMB_covfilt = input[(input[read_depth] >= threshold)].reset_index(drop=True)
    filtering_rates = len(TMB_covfilt["Mut_ID"])
    return (TMB_covfilt, filtering_rates)


def allelefrequency_filter(input, allele_fraction, lower_threshold, higher_threshold):
    TMB_AFboundariesfilt = input[
        (input[allele_fraction] >= lower_threshold)
        & (input[allele_fraction] <= higher_threshold)
    ].reset_index(drop=True)
    filtering_rates = len(TMB_AFboundariesfilt["Mut_ID"])
    return (TMB_AFboundariesfilt, filtering_rates)


def popfrequency_filter(input, database, threshold):
    TMB_popfreqfilt = input[input[database] <= threshold].reset_index(drop=True)
    filtering_rates = len(TMB_popfreqfilt["Mut_ID"])
    return (TMB_popfreqfilt, filtering_rates)


def calculate_TMB(input, panel_size):
    TMB = round((len(input.index) / panel_size) * 1000000, 2)
    return TMB

def process_single_sample(args, suffix):
    ### Wrapper for single-sample TSV
    allele_fraction = f'allele_fraction{suffix}'
    read_depth = f'read_depth{suffix}'
    TMB_df, filtering_rates_total = preprocess_vembraneout(
        args.file_in, allele_fraction, read_depth, args.filter_muttype, args.population_db, args.filter_consequence
    )
    process_data(args, TMB_df, filtering_rates_total, args.prefilter_region, args.bedfile, allele_fraction, read_depth, args.file_out, args.plot_out)


def process_multi_sample(args, suffix_list):
    ### Wrapper for multi-sample TSV
    ### Outputs each sample in the VCF/TSV as seperate file
    for suffix in suffix_list:
        allele_fraction = f'allele_fraction{suffix}'
        read_depth = f'read_depth{suffix}'
        output_filename = f"{str(args.file_out).strip('.txt')}_{suffix}.txt"
        output_plotname = f"{str(args.plot_out).strip('.png')}_{suffix}.png"
        TMB_df, filtering_rates_total = preprocess_vembraneout(
            args.file_in, allele_fraction, read_depth, args.filter_muttype, args.population_db, args.filter_consequence
        )
        process_data(args, TMB_df, filtering_rates_total, args.prefilter_region, args.bedfile, allele_fraction, read_depth, output_filename, output_plotname)


def process_data(args, TMB_df, filtering_rates_total, prefilter_region, bedfile, allele_fraction, read_depth, output_file, output_plot):
    ### Basically what main did before
    ### Processes data based on thresholds and filter conditions to generate the output txt files
    is_eligible, panel_size = check_bed_size(args.bedfile, args.panelsize_threshold)

    if not is_eligible:
        logger.info(
            "The calculation was not performed as the panel_size is below the allowed threshold."
        )
        return

    if prefilter_region == True:
        TMB_df, is_notempty = filter_bedrange(TMB_df, bedfile)
    else:
        is_notempty = True ## ensure script is running as intended when prefilter_region is not passed

    TMB_covfilt, filtering_rates_cov = coverage_filter(TMB_df, read_depth, args.min_cov)
    TMB_affilt, filtering_rates_af = allelefrequency_filter(
        TMB_covfilt, allele_fraction, args.min_AF, args.max_AF
    )
    TMB_popfilt, filtering_rates_popfreq = popfrequency_filter(
        TMB_affilt, args.population_db, args.popfreq_max
    )
    TMB_value = calculate_TMB(
        TMB_popfilt, panel_size
    )
    plot_TMB(
        TMB_covfilt, output_plot, allele_fraction, args.min_AF, args.max_AF
    )

    filtering_rates_total += [
        filtering_rates_cov,
        filtering_rates_af,
        filtering_rates_popfreq,
    ]

    write_output(
        output_file,
        filtering_rates_total,
        args.prefilter_region,
        args.filter_muttype,
        args.min_cov,
        args.min_AF,
        args.max_AF,
        args.population_db,
        args.popfreq_max,
        TMB_value,
        panel_size,
        is_notempty,
    )

def write_output(
    output_file, filtering_rates, prefilter_region, filter_muttype, min_cov, min_AF, max_AF, population_db, popfreq_max, TMB_value, panel_size, is_notempty
):
    with open(output_file, "w") as file:
        file.write(f"Initial amount of mutations after selecting for considered consequences: {filtering_rates[0]} mutations\n")
        file.write(f"Initial amount of unique mutations after consequence selection: {filtering_rates[1]} mutations\n")
        if prefilter_region == True:
            if is_notempty == True:
                file.write(
                    f"### All following TMB Calculations have been performed only based on the provided BED file regions! ###\n"
                )
            else:
                file.write(
                    f"### WARNING: TMB Calculations could not be performed on BED file regions, as no mutations are present in the regions-of-interest! --prefilter_tmb was ignored. ###\n"
                )
        if filter_muttype in ["snv", "snvs", "mnv", "mnvs"]:
            file.write(
                f"Retained mutations after filtering for mutation type {filter_muttype}: {filtering_rates[2]} mutations\n"
            )
        file.write(
            f"Retained mutations after applying coverage filter for a threshold below {min_cov}: {filtering_rates[3]} mutations\n"
        )
        file.write(
            f"Retained mutations after filtering for AF between {min_AF} and {max_AF}: {filtering_rates[4]} mutations\n"
        )
        file.write(
            f"Retained mutations after filtering for the population AF from {population_db} below {popfreq_max}: {filtering_rates[5]} mutations\n"
        )
        file.write(
            f"The final TMB based on these filtering conditions and a panel size of {panel_size}: {TMB_value} mutations/Mbp"
        )

def plot_TMB(input, output_plotname, allele_fraction, lower_af, higher_af):
    ### Preprocess for plotting
    counts_consequence = input.groupby(
        input.columns.tolist(), as_index=False, dropna=False
    ).size()
    index_filter = (
        counts_consequence.groupby("Mut_ID")["size"]
        .transform("max")
        .ne(counts_consequence["size"])
    )
    most_prevalent_con = counts_consequence[~index_filter.values]
    TMB_forplot = (
        pd.DataFrame(
            {
                "Mut_ID": most_prevalent_con["Mut_ID"],
                "CSQ_Consequence": most_prevalent_con["CSQ_Consequence"],
            }
        )
        .merge(input)
        .drop_duplicates()
    )
    TMB_forplot["CSQ_Consequence"] = (
        TMB_forplot["CSQ_Consequence"].str.split("&").str[0]
    )  ## beautification
    TMB_forplot = TMB_forplot.drop_duplicates("Mut_ID", keep="first")

    ### Draw the plot
    fig, ax = plt.subplots(figsize=(14, 8))

    p = sns.histplot(
        data=TMB_forplot,
        ax=ax,
        stat="count",
        multiple="stack",
        binwidth=0.01,
        x=allele_fraction,
        kde=False,
        palette="colorblind",
        hue="CSQ_Consequence",
        element="bars",
    )

    ### Show filtering parameters
    plt.axvline(x=lower_af, color="grey", linestyle="dotted")
    plt.axvline(x=higher_af, color="grey", linestyle="dotted")

    # Set the title and labels
    ax.set_title("Allele frequency (AF) distribution for TMB-filtered variants")
    ax.set_xlabel("AF in %")
    ax.set_ylabel("# of mutations")
    plt.xticks(np.arange(0, 1.1, 0.1))
    ax.yaxis.get_major_locator().set_params(integer=True)  ## force integers on y-axis
    plt.savefig(output_plotname, bbox_inches="tight")

##########
#### MAIN
##########

def main(argv=None):
    ### Parse arguments
    args = parse_args(argv)

    if not args.file_in.is_file():
        logger.error(f"The given input file {args.file_in} was not found!")
        return

    # Set default parameters if they are None
    args.min_cov = args.min_cov or 0.00
    args.min_AF = args.min_AF or 0.00
    args.panelsize_threshold = args.panelsize_threshold or 0

    # Check if the input is a single-sample or multi-sample TSV report
    is_multi, suffix_list = multisample_check(args.file_in)

    # Split workflow based on single or multi-sample TSV
    if not is_multi:
        process_single_sample(args, suffix_list[0])
    else:
        process_multi_sample(args, suffix_list)

if __name__ == "__main__":
    sys.exit(main())
