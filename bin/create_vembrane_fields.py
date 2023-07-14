#!/usr/bin/env python

import re
import sys
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='The general purpose of this script is to easily convert annotation fields into vembrane input parameters. \
        The input are a comma-separated field names for your annotation or from the VCF file. \
        It output has the format: column_name["input_field"][sampleindex] for each field of input_fields. \
        You can also directly perform calculation operations which will be transcribed to vembrane-compatible fields. \
        , e.g. , AD[0]/DP will be converted to column_name["AD"][sampleindex][0]/column_name["DP"][sampleindex]. \
        Vembrane interprets this operation and divides the AD value by the DP value.'
    )
    parser.add_argument(
        "input_fields",
        help="string with comma-separated input fields. The fields need to be letters separated by non-letters (e.g. mathematical operations).",
        type=str,
        nargs=1,
    )
    parser.add_argument(
        "--column_name",
        help="string that specifies the location of the input_field for vembrane, e.g., FORMAT, INFO or CSQ.",
        type=str,
        nargs=1,
        default=None
    )
    parser.add_argument(
        "--fields_with_sampleindex",
        help="fields to add the sampleindex parameter (options: None, all, [specific fields]).",
        type=str,
        nargs="+",
        default="all",
    )
    parser.add_argument(
        "--sampleindex",
        help="integer sample index for all fields_with_sampleindex."
        type=int,
        nargs=1,
        default=0,
    )
    parser.add_argument(
        "--header_prefix",
        help="if enabled, instead of formatting as described only outputs defined prefix to the string.",
        type=str,
        nargs=1,
        default=None,
    )

    return parser.parse_args()

def format_string(
    input_fields,
    column_name,
    fields_with_sampleindex=None,
    sampleindex=None,
    header_prefix=None,
):
    if fields_with_sampleindex is None and sampleindex is not None:
        fields_with_sampleindex = "all"

    def field_format(match):
        column_name = match.group(1)
        if header_prefix is not None:
            return _format_header(column_name, header_prefix)
        elif fields_with_sampleindex == "all":
            if sampleindex is not None:
                return _format_field(column_name, sampleindex)
            else:
                raise ValueError(
                    "Sample index needs to be specified when using fields_with_sampleindex == all."
                )
        elif (
            fields_with_sampleindex
            and column_name in fields_with_sampleindex is not None
        ):
            if sampleindex is not None:
                return _format_field(column_name, sampleindex)
            else:
                raise ValueError(
                    "Sample index needs to be specified when using fields_with_sampleindex."
                )
        else:
            return _format_field(column_name)

    def _format_field(field, sampleindex=None):
        result = f'{column_name}["{field}"]'
        if sampleindex is not None:
            result += f"[{sampleindex}]"
        return result

    def _format_header(field, header_prefix):
        result = f"{header_prefix}_{field}"
        return result

    formatted_string = re.sub(r"([A-Za-z_]+)", field_format, input_fields)
    return formatted_string


if __name__ == "__main__":

    args = parse_arguments()

    # Format the string
    try:
        output_string = format_string(
            args.input_fields,
            args.column_name,
            args.fields_with_sampleindex,
            args.sampleindex,
            args.header_prefix,
        )
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

    print(output_string)
