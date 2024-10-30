#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from pathlib import Path
import sys
import argparse
import logging

logger = logging.getLogger()

### Set the values which could occur in a well structured bed file

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

### Function to read in the input bed file


def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate the structure of the provided BED-sheet.",
        epilog="Example: python3 check_bedfiles.py file.bed",
    )
    parser.add_argument(
        "file_in",
        metavar="FILE_IN",
        type=Path,
        help="File with .bed suffix.",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="The desired log level (default WARNING).",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        default="WARNING",
    )
    return parser.parse_args(argv)


### Function to check if the BED file provided can be used for bcftools and PyRanges


def check_bed_structure(bed_input):
    colcheck = pd.read_csv(bed_input, sep="\t", header=None)
    header_test = any(
        isinstance(value, str) for value in colcheck.iloc[0, 1:2]
    )  ## checks for no full strings in positional argument columns, as chr is interpreted as str
    if (
        len(colcheck.columns) >= 3 and header_test == False
    ):  ### Should contain at least three columns CHROM, POS, END without header
        chrom_valid = check_chromosome_col(colcheck.iloc[:, 0])
        start_valid = check_integer_col(colcheck.iloc[:, 1])
        end_valid = check_integer_col(colcheck.iloc[:, 2])
        order_check = check_startend_col(colcheck)
        if chrom_valid == True:
            if start_valid == True and end_valid == True and order_check == True:
                return True
            else:
                return False
        else:
            return False
    else:
        logger.error(
            "The provided BED file doesn't follow the required format. Please provide a BED file containing the minimal information (Chromosome, Start, End) without an header. TMB will not be calculated."
        )
        raise ValueError(
            f"The provided BED file doesn't follow the required format. Please provide a BED file containing the minimal information (Chromosome, Start, End) without an header. TMB will not be calculated."
        )


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
            structured_out.to_csv("bed_stats_structure.txt", header=False, index=False)
        else:
            raise ValueError(
                f"The given BED file is not well structured! Please check for floats, strings or thereof in your file!"
            )


if __name__ == "__main__":
    sys.exit(main())
