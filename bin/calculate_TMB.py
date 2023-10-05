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
        epilog="Example: python3 calculate_TMB.py input.tsv",
    )
    parser.add_argument(
        "--file_in",
        metavar="file_in",
        type=Path,
        help="Input tsv file of the vembrane TSV converter module",
    )
    parser.add_argument(
        "--bedfile",
        metavar="bedfile",
        type=Path,
        help="Path to the provided BED-file with .bed suffix.",
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


def preprocess_vembraneout(file_in, filter_muttype, population_db):
    TMB_inputfile = pd.read_csv(file_in, sep="\t")
    TMB_inputfile["Mut_ID"] = TMB_inputfile[["CHROM", "POS", "REF", "ALT"]].apply(
        lambda row: ":".join(row.values.astype(str)), axis=1
    )
    TMB_deduplicated = TMB_inputfile.drop_duplicates("Mut_ID", keep="first")
    filtering_rates = []
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
            "allele_fraction",
            "read_depth",
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
        (TMB_inputfile["REF"].isin(["A", "G", "T", "C"])) & (TMB_inputfile["ALT"].isin(["A", "G", "T", "C"]))
    ].reset_index(drop=True)
    if TMB_onlySNV["CSQ_VARIANT_CLASS"].eq("SNV").all():
        return TMB_onlySNV
    else:
        TMB_onlySNV = TMB_onlySNV[(TMB_onlySNV["CSQ_VARIANT_CLASS"] == "SNV")]
        return TMB_onlySNV


def filter_retainMNV(TMB_inputfile):
    TMB_SNVs = TMB_inputfile[
        (TMB_inputfile["REF"].isin(["A", "G", "T", "C"])) & (TMB_inputfile["ALT"].isin(["A", "G", "T", "C"]))
    ].reset_index(drop=True)
    TMB_MNVs = TMB_inputfile[(TMB_inputfile["CSQ_VARIANT_CLASS"] == "substitution")].reset_index(
        drop=True
    )  ### contains DBS, SNVs close to repeats and non-normalized SNVs close to InDels
    TMB_return = pd.concat([TMB_SNVs, TMB_MNVs])
    return TMB_return


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


def coverage_filter(input, threshold):
    TMB_covfilt = input[(input["read_depth"] >= threshold)].reset_index(drop=True)
    filtering_rates = len(TMB_covfilt["Mut_ID"])
    return (TMB_covfilt, filtering_rates)


def allelefrequency_filter(input, lower_threshold, higher_threshold):
    TMB_AFboundariesfilt = input[
        (input["allele_fraction"] >= lower_threshold) & (input["allele_fraction"] <= higher_threshold)
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


def plot_TMB(input, name_convention, lower_af, higher_af):
    ### Preprocess for plotting
    counts_consequence = input.groupby(input.columns.tolist(), as_index=False, dropna=False).size()
    index_filter = counts_consequence.groupby("Mut_ID")["size"].transform("max").ne(counts_consequence["size"])
    most_prevalent_con = counts_consequence[~index_filter.values]
    TMB_forplot = (
        pd.DataFrame({"Mut_ID": most_prevalent_con["Mut_ID"], "CSQ_Consequence": most_prevalent_con["CSQ_Consequence"]})
        .merge(input)
        .drop_duplicates()
    )
    TMB_forplot["CSQ_Consequence"] = TMB_forplot["CSQ_Consequence"].str.split("&").str[0]  ## beautification
    TMB_forplot = TMB_forplot.drop_duplicates("Mut_ID", keep="first")

    ### Draw the plot
    fig, ax = plt.subplots(figsize=(14, 8))

    p = sns.histplot(
        data=TMB_forplot,
        ax=ax,
        stat="count",
        multiple="stack",
        binwidth=0.01,
        x="allele_fraction",
        kde=False,
        palette="colorblind",
        hue="CSQ_Consequence",
        element="bars",
    )

    ### Control the legend
    sns.move_legend(p, loc="center right", bbox_to_anchor=(1.35, 0.5), ncol=1, fontsize=6)

    ### Show filtering parameters
    plt.axvline(x=lower_af, color="grey", linestyle="dotted")
    plt.axvline(x=higher_af, color="grey", linestyle="dotted")

    # Set the title and labels
    ax.set_title("Allele frequency (AF) distribution for TMB-filtered variants")
    ax.set_xlabel("AF in %")
    ax.set_ylabel("# of mutations")
    plt.xticks(np.arange(0, 1.1, 0.1))
    ax.yaxis.get_major_locator().set_params(integer=True)  ## force integers on y-axis
    plt.savefig(name_convention, bbox_inches="tight")


def main(argv=None):
    """Coordinate argument parsing and program execution."""
    args = parse_args(argv)
    if not args.file_in.is_file():
        logger.error(f"The given input file {args.file_in} was not found!")

    # Need to adjust parameters of zero is passed to avoid None input
    if args.min_cov is None:
        args.min_cov = 0.00
    if args.min_AF is None:
        args.min_AF = 0.00
    if args.panelsize_threshold is None:
        args.panelsize_threshold = 0

    TMB_df, filtering_rates_total = preprocess_vembraneout(args.file_in, args.filter_muttype, args.population_db)
    eligibility, panel_size = check_bed_size(args.bedfile, args.panelsize_threshold)
    if eligibility == True:
        TMB_covfilt, filtering_rates_cov = coverage_filter(TMB_df, args.min_cov)
        TMB_affilt, filtering_rates_af = allelefrequency_filter(TMB_covfilt, args.min_AF, args.max_AF)
        TMB_popfilt, filtering_rates_popfreq = popfrequency_filter(TMB_affilt, args.population_db, args.popfreq_max)
        TMB_value = calculate_TMB(TMB_popfilt, panel_size)
        filtering_rates_total = filtering_rates_total + [
            filtering_rates_cov,
            filtering_rates_af,
            filtering_rates_popfreq,
        ]
        plot_TMB(
            TMB_covfilt, args.plot_out, args.min_AF, args.max_AF
        )  ### Use coverage filtered data as non-filtered data compresses plot to uselessness...
        with open(args.file_out, "w") as file:
            file.write(f"Inital amount of unique mutations: {filtering_rates_total[0]} mutations\n")
            if args.filter_muttype in ["snv", "snvs", "mnv", "mnvs"]:
                file.write(
                    f"Retained mutations after filtering for mutation type {args.filter_muttype}: {filtering_rates_total[1]} mutations\n"
                )
            file.write(
                f"Retained mutations after applying coverage filter for a threshold below {args.min_cov}: {filtering_rates_total[2]} mutations\n"
            )
            file.write(
                f"Retained mutations after filtering for AF between {args.min_AF} and {args.max_AF}: {filtering_rates_total[3]} mutations\n"
            )
            file.write(
                f"Retained mutations after filtering for the population AF from {args.population_db} below {args.popfreq_max}: {filtering_rates_total[4]} mutations\n"
            )
            file.write(
                f"The final TMB based on these filtering conditions and a panel size of {panel_size}: {TMB_value} mutations/Mbp"
            )
    else:
        logger.info("The calculation was not performed as the panel_size is below the allowed threshold.")


if __name__ == "__main__":
    sys.exit(main())
