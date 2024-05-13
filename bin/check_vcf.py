#!/usr/bin/env python

import pandas as pd
import re
import argparse
import gzip
from itertools import chain


def parse_arguments():
    parser = argparse.ArgumentParser(description="This script checks vcf files.")
    parser.add_argument(
        "--meta_id",
        help="Meta ID representing the sample name used in warning messages.",
        type=str,
    )
    parser.add_argument(
        "--vcf_in",
        help="VCF file path.",
        type=str,
    )
    parser.add_argument(
        "--bcftools_stats_in",
        help="bcftools stats file.",
        type=str,
    )
    parser.add_argument(
        "--warnings_out",
        help="name of .txt file to save warnings.",
        type=str,
    )
    parser.add_argument(
        "--check_chr_prefix",
        help='Check if CHROM column always has "chr" prefix.',
        action="store_true",
    )
    parser.add_argument(
        "--check_MNPs",
        help="Check if provided VCF contains multinucleotide variants.",
        action="store_true",
    )
    parser.add_argument(
        "--check_vep_annotation",
        help="Check if provided VCF is already annotated with VEP.",
        action="store_true",
    )
    parser.add_argument(
        "--check_FILTERs",
        help='Check if provided VCF has FILTER entries other than "PASS" or "."',
        action="store_true",
    )
    parser.add_argument(
        "--check_gVCF",
        help="Check if provided VCF contains genomic, nonvariant positions.",
        action="store_true",
    )
    parser.add_argument(
        "--check_other_variants",
        help="Check if provided VCF has other variants than SNVs and indels.",
        action="store_true",
    )
    parser.add_argument(
        "--check_multiallelic_sites",
        help="Check if provided VCF file has multiallelic sites.",
        action="store_true",
    )

    return parser.parse_args()


def read_vcf(vcf_in):
    vcffile = pd.read_csv(vcf_in, sep="\t", comment="#", header=None)
    if len(vcffile.columns) < 10:
        raise ValueError(
            "ERROR: Your VCF file has less than 10 columns and may miss columns."
        )
    else:
        vcffile.columns = [
            "CHROM",
            "POS",
            "ID",
            "REF",
            "ALT",
            "QUAL",
            "FILTER",
            "INFO",
            "FORMAT",
        ] + ['SAMPLE{}'.format(i) for i in range(1, len(vcffile.columns) - 8)]
    return vcffile


def read_vcf_header(vcf_in):
    header = []
    if vcf_in.endswith(".gz"):
        with gzip.open(vcf_in, "rt") as f:
            for l in f:
                if l.startswith("##"):
                    header.append(l.strip("\n"))
    else:
        with open(vcf_in, "rt") as f:
            for l in f:
                if l.startswith("##"):
                    header.append(l.strip("\n"))
    return header


def check_chrom_def(vcffile, meta_id, log_level):
    """
    Check if the chromosome column always has the "chr" prefix.
    """
    # extract chromosomes
    chromosomes = vcffile["CHROM"]

    if chromosomes.dtype == "int":
        report_message = f'{log_level}: {meta_id} "CHROM" column only contains integers. Chromosome names need the "chr" prefix in the "CHROM" column.'
    else:
        # check for pattern
        pattern = re.compile(r"^chr.*")
        chrmatch = [bool(pattern.match(c)) for c in chromosomes]
        if all(chrmatch):
            report_message = f'CHECK: {meta_id} always contains "chr" prefix in the CHROM column.'
        else:
            error_indices = [idx for idx, result in enumerate(chrmatch) if not result]
            report_message = (
                f'{log_level}: {meta_id} contains records without "chr" prefix in the CHROM column. '
                f"{len(error_indices)} out of {len(chromosomes)} records do not have this prefix, e.g. have chromosome defined like this entry: {chromosomes[error_indices[0]]}. "
                'Please use the "chr" prefix consistently for all entries.'
            )
    return report_message


def check_VEP(vcffile, vcfheader, meta_id, log_level):
    """
    Check for already present VEP annotations in the VCF file.
    First, it checks the presence of a VEP flag in the header.
    Then, it checks if a CSQ string is present in the INFO column.
    """

    if "VEP" in vcfheader:
        report_message = f"{log_level}: {meta_id} contains a VEP key in VCF header. If the VCF file contains previous annotations, these will be overwritten."
    elif [any("CSQ" in e for e in vcffile["INFO"])][0]:
        report_message = f"{log_level}: {meta_id} contains a CSQ key in the INFO column entries. If the VCF file contains previous annotations, these will be overwritten."
    else:
        report_message = f"CHECK: {meta_id} is not annotated by VEP yet."
    return report_message


def check_FILTERs(vcffile, meta_id, log_level, passfilters={"PASS", "."}):
    """
    Checks if FILTER column has anything else than "." or "PASS".
    If VCF FILTER columns has ".", i.e. no filter was applied, PyVCF convert it to "None" and "PASS" is converted to an empty list "[]".
    Hence to check for both, we need to check for non-empty strings
    """

    # get unique FILTER col entries from all vcf records
    def get_entries_FILTER_col(vcffile):
        # get filtervalues and split multiple values
        filters = vcffile["FILTER"].str.split(";")
        # remove nested list and get unique entries
        allfilters = set(chain.from_iterable(filters))
        # get unique entries
        return allfilters

    # check if any other filtervalues are present.
    def check_pass(filters):
        otherfilters = filters.difference(passfilters)
        if not otherfilters:
            report_message = f'CHECK: {meta_id} contains only "." or "PASS" values in FILTER column.'
        else:
            # if anything else than "PASS" or "." is present, report.
            report_message = f"{log_level}: {meta_id} contains other FILTER values than \"PASS\" or \".\": {','.join(otherfilters)}. If pass_filter = true, these will be filtered."
        return report_message

    # Check in records
    filters = get_entries_FILTER_col(vcffile)
    report_message = check_pass(filters)

    return report_message


def check_stats_value(
    statsfile,
    pattern,
    textsnippet,
    meta_id,
    tabposition=4,
    intcheck=0,
    log_level="WARNING",
):
    """
    This function generally opens the stats file, searches for a string to match and extracts a tab-delimited position.
    This position is assumed to be integer and checked against a specific intcheck number.
    Hence, you can extract specific values in the bcftools stats file and check them directly.
    The textsnippet argument adds specific error messages for better readability.
    """

    def process_lines(line):
        # strip newline
        foundline = line.strip("\n")
        # split tabs
        tabs = re.split("\t", foundline)
        # extract tabposition and return
        return tabs[tabposition - 1]

    # open file
    with open(statsfile, "r") as file:
        matches = []
        for line in file:
            # important: the line is no comment line.
            if pattern in line and not line.startswith("#"):
                matches.append(process_lines(line))
    if len(matches) != 1:
        print(f"ERROR: {pattern} matches more than one line on stats file.")

    if int(matches[0]) > intcheck:
        report_message = f"{log_level}: {meta_id} contains {matches[0]} {textsnippet}."
    else:
        report_message = f"CHECK: {meta_id} contains equal or less than {intcheck} {textsnippet}."
    return report_message


if __name__ == "__main__":
    args = parse_arguments()

    """
    meta_id is always needed to reassign the sample name when warnings are collated in the workflow.
    The log_level determines a string that will be handled as following:
        "ERROR": raise ValueError, workflow will stop.
        "WARNING": The whole warning message will be collected in warnings_out and reported in multiQC file.
    """

    # load VCF as pyVCF object. This checks VCF format as well.
    vcffile = read_vcf(args.vcf_in)
    vcfheader = read_vcf_header(args.vcf_in)

    # Run all checks and collect feedback in report_message list
    report_message = []

    # Checks through VCF file:
    # The input for all functions needs to be a PyVCF reader class object.
    if args.check_chr_prefix:
        report_message = report_message + [check_chrom_def(vcffile, meta_id=args.meta_id, log_level="ERROR")]

    if args.check_vep_annotation:
        report_message = report_message + [check_VEP(vcffile, vcfheader, meta_id=args.meta_id, log_level="WARNING")]

    if args.check_FILTERs:
        report_message = report_message + [check_FILTERs(vcffile, meta_id=args.meta_id, log_level="WARNING")]

    # Input checks based on bcftools stats output.
    if args.check_MNPs:
        report_message = report_message + [
            check_stats_value(
                args.bcftools_stats_in,
                pattern="number of MNPs",
                textsnippet="MNPs (multinucleotide variants)",
                meta_id=args.meta_id,
            )
        ]

    if args.check_gVCF:
        report_message = report_message + [
            check_stats_value(
                args.bcftools_stats_in,
                pattern="number of no-ALTs",
                textsnippet="nonvariant genomic postions (no-ALTs)",
                meta_id=args.meta_id,
            )
        ]

    if args.check_other_variants:
        report_message = report_message + [
            check_stats_value(
                args.bcftools_stats_in,
                pattern="number of others",
                textsnippet='"other" variants that are neither SNPs nor indels',
                meta_id=args.meta_id,
            )
        ]

    if args.check_multiallelic_sites:
        report_message = report_message + [
            check_stats_value(
                args.bcftools_stats_in,
                pattern="number of multiallelic sites",
                textsnippet="variants with multiallelic sites. These will be splitted by `bcftools norm` into biallelic sites",
                meta_id=args.meta_id,
            )
        ]

    # If log_level is set to "ERROR": crash and report ALL check messages
    if any(["ERROR" in m for m in report_message]):
        raise ValueError("\n".join(report_message))

    # If log_level is set to "WARNING". collect only those in warnings_out for including in multiQC report.
    warnings = []
    for m in report_message:
        if "WARNING" in m:
            warnings.append(m)

    with open(args.warnings_out, "xt") as warning_out:
        warning_out.write("\n".join(warnings))

    # Report messages also to stdin
    print(f"{args.meta_id} VCF check was successful:\n" + "\n".join(report_message))
