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
        choices=["snv", "snvs", "mnv", "mnvs", "all"],
        help="Set the conditions for filtering, either selecting only SNVs, SNVs and MNVs or the whole dataset including InDels",
    )
    parser.add_argument(
        "--filter_consequence",
        metavar="filter_consequence",
        type=bool,
        help="Should variant consequence filtering be performed?",
    )
    parser.add_argument(
        "--csq_values",
        metavar="csq_values",
        type=str,
        help="String containing the VEP consequences for which should be filtered.",
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


def preprocess_vembraneout(file_in, allele_fraction, read_depth, filter_muttype, population_db, filter_consequence, csq_values):
    TMB_inputfile = pd.read_csv(file_in, sep="\t")
    filtering_rates = []
    TMB_inputfile["Mut_ID"] = TMB_inputfile[["CHROM", "POS", "REF", "ALT"]].apply(
        lambda row: ":".join(row.values.astype(str)), axis=1
    )
    ### Count initial unique mutations based on Mut_ID
    initial_unique = TMB_inputfile["Mut_ID"].nunique()
    filtering_rates.append(initial_unique)
    ### move consequence filter into preprocessing to circumvent deduplication pitfall
    if filter_consequence is True:
        TMB_consequence, filtering_csq = consequence_filter(TMB_inputfile, csq_values)
        filtering_rates.append(filtering_csq)
    else:
        TMB_consequence = TMB_inputfile
        filtering_rates.append(initial_unique)
    TMB_deduplicated = TMB_consequence.drop_duplicates("Mut_ID", keep="first")
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
    filtering_rates.append(TMB_filtered["Mut_ID"].nunique())
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


def consequence_filter(TMB_inputfile, csq_values):
    csq_list = csq_values.split(",")
    TMB_prefilt = TMB_inputfile.copy()
    TMB_filt = TMB_prefilt[TMB_prefilt["CSQ_Consequence"].apply(lambda x: csq_match(x, csq_list))]
    filtering_rates = TMB_filt["Mut_ID"].nunique()
    return (TMB_filt, filtering_rates)


def filter_bedrange(TMB_inputfile, panel_data_in):
    ### Separate filter for ROI independant of tag_roi
    ### Read bedfile and convert to range
    panel_data = panel_data_in.iloc[:, 0:3]
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
        filtering_rates = TMB_filt.index.nunique()
        return (TMB_filt, is_notempty, filtering_rates)
    else:
        TMB_filt = TMB_inputfile
        is_notempty = False
        filtering_rates = TMB_filt.index.nunique()
        return (TMB_filt, is_notempty, filtering_rates)


def check_bed_size(panel_data_in, breaking_thresh):
    panel_data = panel_data_in.iloc[:, 0:3]
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
    filtering_rates = TMB_covfilt["Mut_ID"].nunique()
    return (TMB_covfilt, filtering_rates)


def allelefrequency_filter(input, allele_fraction, lower_threshold, higher_threshold):
    TMB_AFboundariesfilt = input[
        (input[allele_fraction] >= lower_threshold)
        & (input[allele_fraction] <= higher_threshold)
    ].reset_index(drop=True)
    filtering_rates = TMB_AFboundariesfilt["Mut_ID"].nunique()
    return (TMB_AFboundariesfilt, filtering_rates)


def popfrequency_filter(input, database, threshold):
    ### NaN should be retained
    TMB_popfreqfilt = input[(input[database] <= threshold) | input[database].isna()].reset_index(drop=True)
    filtering_rates = TMB_popfreqfilt["Mut_ID"].nunique()
    return (TMB_popfreqfilt, filtering_rates)


def calculate_TMB(input, panel_size):
    TMB = round((input["Mut_ID"].nunique() / panel_size) * 1000000, 2)
    return TMB


def process_single_sample(args, suffix):
    ### Wrapper for single-sample TSV
    allele_fraction = f'allele_fraction{suffix}'
    read_depth = f'read_depth{suffix}'
    TMB_df, filtering_rates_total = preprocess_vembraneout(
        args.file_in, allele_fraction, read_depth, args.filter_muttype, args.population_db, args.filter_consequence, args.csq_values
    )
    process_data(args, TMB_df, filtering_rates_total, args.prefilter_region, allele_fraction, read_depth, args.file_out, args.plot_out)


def process_multi_sample(args, suffix_list):
    ### Wrapper for multi-sample TSV
    ### Outputs each sample in the VCF/TSV as seperate file
    for suffix in suffix_list:
        allele_fraction = f'allele_fraction{suffix}'
        read_depth = f'read_depth{suffix}'
        output_filename = f"{str(args.file_out).strip('.txt')}_{suffix}.txt"
        output_plotname = f"{str(args.plot_out).strip('.png')}_{suffix}.png"
        TMB_df, filtering_rates_total = preprocess_vembraneout(
            args.file_in, allele_fraction, read_depth, args.filter_muttype, args.population_db, args.filter_consequence, args.csq_values
        )
        process_data(args, TMB_df, filtering_rates_total, args.prefilter_region, allele_fraction, read_depth, output_filename, output_plotname)


def process_data(args, TMB_df, filtering_rates_total, prefilter_region, allele_fraction, read_depth, output_file, output_plot):
    ### Processes data based on thresholds and filter conditions to generate the output txt files
    panel_bedfile = pd.read_csv(args.bedfile, sep="\t", header=None)
    is_eligible, panel_size = check_bed_size(panel_bedfile, args.panelsize_threshold)

    if not is_eligible:
        logger.info(
            "The calculation was not performed as the panel_size is below the allowed threshold."
        )
        return

    if prefilter_region == True:
        TMB_df, is_notempty, filtering_rates_roi = filter_bedrange(TMB_df, panel_bedfile)
    else:
        is_notempty = True
        filtering_rates_roi = 0 ## ensure script is running as intended when prefilter_region is not passed

    TMB_covfilt, filtering_rates_cov = coverage_filter(
        TMB_df, read_depth, args.min_cov
    )
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
        filtering_rates_roi,
        filtering_rates_cov,
        filtering_rates_af,
        filtering_rates_popfreq,
    ]

    write_output(
        output_file,
        filtering_rates_total,
        args.prefilter_region,
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
    output_file, filtering_rates, prefilter_region, min_cov, min_AF, max_AF, population_db, popfreq_max, TMB_value, panel_size, is_notempty
):
    with open(output_file, "w") as file:
        file.write(f"STEP,#_MUTATIONS,INFO\n")
        file.write(f"Initial mutations prior filtering,{filtering_rates[0]},\n")
        if filtering_rates[0] == filtering_rates[1]:
            file.write(f"Unique mutations after consequence filter,{filtering_rates[1]},NOT_APPLIED\n")
        else:
            file.write(f"Unique mutations after consequence filter,{filtering_rates[1]},\n")
        if filtering_rates[1] == filtering_rates[2]:
            file.write(f"Unique mutations after SNV/MNV filter,{filtering_rates[2]},NOT_APPLIED\n")
        else:
            file.write(f"Unique mutations after SNV/MNV filter,{filtering_rates[2]},\n")
        if prefilter_region == True:
            if is_notempty == True:
                file.write(f"Unique mutations after ROI-intersection,{filtering_rates[3]},\n")
            else:
                file.write(f"Unique mutations after ROI-intersection,{filtering_rates[3]},WARN_NO_MUTATIONS_IN_ROI\n")
        file.write(
            f"Unique mutations after coverage filter,{filtering_rates[4]},COV_VAL_{min_cov}\n"
        )
        file.write(
            f"Unique mutations after AF range filter,{filtering_rates[5]},AF_RANGE_{min_AF}_{max_AF}\n"
        )
        file.write(
            f"Unique mutations after population database filter,{filtering_rates[6]},{population_db}_THRESH_{popfreq_max}\n"
        )
        file.write(
            f"TMB value,{TMB_value}/Mbp,PANELSIZE_{panel_size}"
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
    )
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
