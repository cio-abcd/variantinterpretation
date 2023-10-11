#!/usr/bin/env python

import argparse
import pandas as pd
import numpy as np
import yte
import re


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Split variant TSV file by groups and create datavzrd config file.")
    parser.add_argument(
        "--variant_tsv",
        type=str,
        help="File path to TSV file with variant information.",
    )
    parser.add_argument(
        "--colinfo_tsv",
        type=str,
        help="File path to TSV file with information about annotation columns in variant_tsv.",
    )
    parser.add_argument(
        "--ann_name_column",
        type=str,
        help="Column name in colinfo_tsv containing the column names of variant_tsv.",
        default="identifier",
    )
    parser.add_argument(
        "--ann_group_column",
        type=str,
        help="Column name in colinfo_tsv containing the group information of column names of variant_tsv, in which TSVs should be split.",
        default="group",
    )
    parser.add_argument(
        "--identifiers",
        type=str.lower,
        nargs="+",
        help="Column names used for creating an identifier for each split TSV file, used for referencing links between them. Space-separated",
        default=["chrom", "pos", "ref", "alt", "id", "feature"],
    )
    parser.add_argument("--prefix", type=str, help="prefix for sample to distinguish them.")
    parser.add_argument("--datavzrd_template", type=str, help="Path to datavzrd config template that will be rendered.")

    # Parse command-line arguments
    return parser.parse_args()


def process_ann_cols(variant_df, colinfo_df, ann_name_column, ann_group_column, identifiers, id_name):
    ### Processing of column names for matching colinfo table ###
    # removing CSQ prefixes from column names
    variant_df.columns = variant_df.columns.str.replace("CSQ_", "")

    # for case-insensitive matching of variant TSV columns and colinfo: convert both to lower strings
    variant_df.columns = variant_df.columns.str.lower()
    colinfo_df[ann_name_column] = colinfo_df[ann_name_column].str.lower()

    # replace mathematical operands and brackets with their literal names in variant TSV column names (compatibility with datavzrd)
    variant_df.columns = replace_operands(variant_df.columns)

    # check for characters beyond letters, numbers and underscores in column names
    input_check(variant_df.columns, r"^[A-Za-z0-9_\-]+$")
    input_check(colinfo_df[ann_name_column], r"^[A-Za-z0-9_\-]+$")

    # check for duplicated variant TSV columns or column info.
    check_for_duplicates(variant_df.columns, "variant TSV file column names")
    check_for_duplicates(colinfo_df[ann_name_column], "colinfo TSV file annotation name column")
    # Compare TSV files and add columns that are missing
    variant_df, colinfo_df = add_missing_columns(variant_df, colinfo_df, ann_name_column, ann_group_column)

    # Create a column with pasted identifiers as an ID column that will be used to reference variants between tables.
    variant_df = generate_variant_ids(variant_df, id_name, identifiers)

    return variant_df, colinfo_df


# replace operands with literal names
def replace_operands(df_index):
    operator_replacements = {
        "+": "-plus-",
        "-": "-minus-",
        "*": "-times-",
        "/": "-divided-by-",
        "%": "-modulus-",
        "[": "-",
        "]": "-",
    }
    replace_pattern = r"[-+*/%\[\]]"
    return df_index.str.replace(replace_pattern, lambda m: operator_replacements[m.group()], regex=True)


# check if string matches regular expression
def input_check(input_strings, regex):
    for input_string in input_strings:
        if re.fullmatch(regex, input_string) is None:
            raise ValueError(f'Error: The annotation name "{input_string}" should match regex "{regex}".')


# check list of strings for duplicates and give error message with all duplicated entries.
def check_for_duplicates(strings_list, listname):
    seen = set()
    duplicates = set()

    for string in strings_list:
        if string in seen:
            duplicates.add(string)
        else:
            seen.add(string)

    if duplicates:
        duplicate_entries = ", ".join(duplicates)
        raise ValueError(f"Found duplicate entries in the {listname}: {duplicate_entries}")


def add_missing_columns(variant_df, colinfo_df, ann_name_column, ann_group_column):
    # Get column names from variant_tsv and colinfo_tsv
    variant_cols = set(variant_df.columns)
    colinfo_cols = set(colinfo_df[ann_name_column])

    # Find columns in colinfo_df that are missing in variant_df
    missing_columns = colinfo_cols - variant_cols

    if missing_columns:
        print(
            "Warning: The following columns are missing in variant tsv file but are present in colinfo tsv file and will be added with empty values:"
        )
        for column in missing_columns:
            print(f"- {column}")
            # Add missing columns to variant_tsv with nan values
            variant_df[column] = np.nan

    # Find columns in variant_tsv that are not defined in colinfo_tsv
    undefined_columns = variant_cols - colinfo_cols

    if undefined_columns:
        print(f"Warning: Columns present in variant tsv file but not defined in colinfo tsv file.")
        print("These columns will be included in the 'others' group.")
        for column in undefined_columns:
            print(f"  - {column}")
            # Add new row to colinfo_tsv with "nan" values, 'others' group, same label and normal display mode.
            new_rows = pd.DataFrame(
                [[column, "others", column, "normal"]],
                columns=[ann_name_column, ann_group_column, "label", "display"],
            )
            colinfo_df = pd.concat([colinfo_df, new_rows])

    return variant_df, colinfo_df


# generate a minus-linked string from multiple columns
def generate_variant_ids(variant_df, id_name, identifiers):
    variant_df[id_name] = variant_df[identifiers].apply(lambda x: "-".join(x.astype(str)), axis=1)
    return variant_df


# split the variant dataframe by groups
def split_df_by_group(colinfo_df, variant_df, group, ann_name_column, ann_group_column, identifiers, id_name, prefix):
    # Extract which columns are in a group
    group_cols = colinfo_df.query(ann_group_column + "=='" + group + "'")[ann_name_column]
    # also add identifiers
    group_cols = [id_name] + identifiers + list(group_cols)
    # avoid having identifiers duplicated, so remove duplicates
    group_cols = list(dict.fromkeys(group_cols))
    # subset the variant_df based on this list, with identifier columns always in front.
    group_df = variant_df[group_cols]
    # save as tsv file
    group_df.to_csv(prefix + "-" + group + ".tsv", sep="\t", index=False)


# convert a string with comma-separated key-value pairs to a dictionary
def convert_to_dict(string, delimiter):
    # split multiple comma-separated key:value pairs
    pairs = re.split(",", string)
    # split keys and values by equal sign and format to dictionary
    return {key: value for key, value in (re.split(delimiter, pair) for pair in pairs)}


# process colinfo columns and provide them in datavzrd rendering
def render_datavzrd_config(colinfo_df, datavzrd_template, ann_group_column, ann_name_column, prefix):
    # get set of groups from file
    groups = set(colinfo_df[ann_group_column])

    # get all column names from specific group
    def get_group_cols(colinfo_df, ann_group_column, group, ann_name_column):
        return list(colinfo_df.query(ann_group_column + "=='" + group + "'")[ann_name_column])

    # create a dictionary with all groups and columns and pass to yaml template
    yaml_variables = {
        "prefix": prefix,
        "groupnames": groups,
        "colnames": dict(
            zip(groups, [get_group_cols(colinfo_df, ann_group_column, group, ann_name_column) for group in groups])
        ),
    }
    for col in colinfo_df.keys():
        yaml_variables.update({col: dict(zip(colinfo_df[ann_name_column], colinfo_df[col]))})

    # convert strings from data_type_value column that contain 'key1=value1,key2=value2,[...] to dictionaries
    for dtv_key in yaml_variables["data_type_value"].keys():
        if not pd.isna(yaml_variables["data_type_value"][dtv_key]):
            yaml_variables["data_type_value"][dtv_key] = convert_to_dict(
                yaml_variables["data_type_value"][dtv_key], "="
            )

    # render yaml template with yte and save as separate config file
    with open(datavzrd_template, "r") as template, open(prefix + "-datavzrd-config-rend.yaml", "w") as outfile:
        result = yte.process_yaml(template, outfile=outfile, variables=yaml_variables)


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()

    # Read variant TSV file that will be processed
    variant_df = pd.read_csv(args.variant_tsv, sep="\t")
    # Load annotation column database used for referencing information
    colinfo_df = pd.read_csv(args.colinfo_tsv, sep="\t")

    # Since integer columns are by default not read correctly if empty values are there, convert dtypes before proceeding
    variant_df = variant_df.convert_dtypes()
    colinfo_df = colinfo_df.convert_dtypes()

    # Processing TSV file: column formatting + input checks
    variant_df, colinfo_df = process_ann_cols(
        variant_df, colinfo_df, args.ann_name_column, args.ann_group_column, args.identifiers, "variant"
    )

    # Split variant_tsv by groups defined in colinfo_tsv and save as TSV files
    for group in set(colinfo_df[args.ann_group_column]):
        split_df_by_group(
            colinfo_df,
            variant_df,
            group,
            args.ann_name_column,
            args.ann_group_column,
            args.identifiers,
            "variant",
            args.prefix,
        )

    # render datavzrd config based on this groups
    render_datavzrd_config(colinfo_df, args.datavzrd_template, args.ann_group_column, args.ann_name_column, args.prefix)
