#!/usr/bin/env python

import pandas as pd
import argparse
import re


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Reads in TSV file with filter definitions and formats into vembrane tag input. \
        The general filter expression follow a python syntax with the guidelines at https://github.com/vembrane/vembrane#vembrane-filter"
    )
    parser.add_argument(
        "--filterdefinitions",
        help="tab-separated file with filter name in first column and filter expression in second column.",
        type=str,
    )

    return parser.parse_args()


def input_check(input_strings):
    for input_string in input_strings:
        if re.fullmatch(r"^[A-Za-z0-9_]+$", input_string) is None:
            raise ValueError(
                f'Error: The input_field "{input_string}" should only contain letters, numbers and underscores.'
            )


if __name__ == "__main__":
    args = parse_arguments()

    # import predefined filters from TSV
    filterdef_df = pd.read_csv(
        args.filterdefinitions,
        sep="\t",
    )

    # check TSV file structure
    if not ["name", "filter"] == list(filterdef_df.columns):
        raise ValueError(
            f'Error: The specified filter TSV file does not have two columns named "name" and "filter": "{args.filterdefinitions}".'
        )
    # only allow numbers, letters and underscore for filter names
    input_check(filterdef_df["name"])

    # format for tagging
    filter_argument = "--tag=" + filterdef_df["name"] + "='" + filterdef_df["filter"] + "'"

    # concatenate
    filters = " ".join(filter_argument)

    print(filters)
