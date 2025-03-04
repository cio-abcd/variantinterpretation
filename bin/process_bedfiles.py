#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from pathlib import Path
import sys
import argparse
import logging

### Set the values which could occur in a well structured bed file
### FUTURE WARNING: Needs adaption depending on reference genome!

chroms = {
    "chr1",
    "chr2",
    "chr3",
    "chr4",
    "chr5",
    "chr6",
    "chr7",
    "chr8",
    "chr9",
    "chr10",
    "chr11",
    "chr12",
    "chr13",
    "chr14",
    "chr15",
    "chr16",
    "chr17",
    "chr18",
    "chr19",
    "chr20",
    "chr21",
    "chr22",
    "chrX",
    "chrY",
    "chrM",
}


def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="This python script accepts BED files based on the USCS file format standard and runs multiple checks \
        on the integrity and format adherence of the file. It checks if the BED file contains no header, if all columns containing \
        positions are only composed of integers and that all end positions occur after their respective start positions. Furthermore, it creates a \
        minimized version of a BED file required for bcftools and BED-based subworkflows in this pipeline.",
        epilog="Example: python3 process_bedfiles.py file.bed",
    )
    parser.add_argument(
        "file_in",
        metavar="FILE_IN",
        type=Path,
        help="File with .bed suffix.",
    )
    parser.add_argument(
        "file_out",
        metavar="FILE_OUT",
        type=Path,
        help="Filename after minimization"
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

### Define functions for integrity checks and BED-file minimalization.

def check_chromosome_col(input):
    column = input.isin(chroms)
    column_nonvalid_rows = column.index[column == False].tolist()
    validity = column.all()
    if validity == True:
        logger.info("The Chromosome column is valid.")
        return True
    else:
        logger.error(
            'The Chromosome column contains values not following the "chr1-chr22/X/Y" convention. Please check the rows ',
            column_nonvalid_rows,
            " for problems.",
        )
        return False

def check_integer_col(input):
    column = input.map(type).eq(int)
    validity = column.all()
    if validity == True:
        logger.info("The positional argument column only contains integers.")
        return True
    else:
        logger.error(
            "The positional argument column contains non-integer values. Please check your start/end column for problems."
        )
        return False

def check_startend_col(input):
    all_rows_valid = all(input.iloc[:, 1] < input.iloc[:, 2])
    if all_rows_valid == False:
        nonvalid_rows = input[input.iloc[:, 1] >= input.iloc[:, 2]].index.tolist()
        logger.error(
            "Not all start positions are smaller than their respective end positions. Please check the rows ",
            nonvalid_rows,
            " for problems.",
        )
        return False
    else:
        return True


def check_bed_structure(bed_input):
    colcheck = pd.read_csv(bed_input, sep="\t", header=None)
    header_test = any(
        isinstance(value, str) for value in colcheck.iloc[0, 1:2]
    )  ## checks for no full strings in positional argument columns, as chr is interpreted as str
    if len(colcheck.columns) >= 3 and header_test == False:
        ### Should contain at least three columns CHROM, POS, END without header
        chrom_valid = check_chromosome_col(colcheck.iloc[:, 0])
        start_valid = check_integer_col(colcheck.iloc[:, 1])
        end_valid = check_integer_col(colcheck.iloc[:, 2])
        order_check = check_startend_col(colcheck)
        return all([chrom_valid, start_valid, end_valid, order_check])
    else:
        raise ValueError(
            f"The provided BED file doesn't follow the required format. Please provide a BED file containing the minimal information (Chromosome, Start, End) without an header. TMB will not be calculated."
        )

def select_minimal(bed_input):
    full_bed = pd.read_csv(bed_input, sep="\t", header=None)
    minimal_bed = full_bed.iloc[:,0:3]
    return(minimal_bed)


def main(argv=None):
    """Coordinate argument parsing and program execution."""
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level, format="[%(levelname)s] %(message)s")
    if not args.file_in.is_file():
        logger.error(f"The given input file {args.file_in} was not found!")
        raise ValueError(f"The given input file {args.file_in} was not found!")
    else:
        bed_well_structured = check_bed_structure(args.file_in)
        if bed_well_structured == True:
            structured_out = pd.DataFrame(
                {"bed_well_structured": [bed_well_structured]}
            )
            minimal_bed = select_minimal(args.file_in)
            structured_out.to_csv("bed_stats_structure.txt", header=False, index=False)
            minimal_bed.to_csv(args.file_out, header=False, index=False, sep='\t')
        else:
            raise ValueError(
                f"The given BED file is not well structured! Please check for floats, strings or thereof in your file!"
            )

if __name__ == "__main__":
    sys.exit(main())
