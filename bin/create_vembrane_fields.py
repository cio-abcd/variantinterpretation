#!/usr/bin/env python

import re
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='The general purpose of this script is to easily convert annotation fields into vembrane input parameters. \
        The input are field names from the INFO/FORMAT column or annotation string as CSQ in the VCF file. \
        The output has the format: column_name["input_field"][sampleindex] for each field of input_fields. \
        You can also directly perform calculation operations which will be transcribed to vembrane-compatible fields. \
        , e.g. , AD[1]/DP will be converted to column_name["AD"][sampleindex][0]/column_name["DP"][sampleindex]. \
        Vembrane interprets this operation and divides the AD value by the DP value to get the allele fraction.'
    )
    parser.add_argument(
        "--input_fields",
        help="space-separated input fields. The fields only allow letters, numbers, underscores, square brackets and mathematical operands.",
        type=str,
        nargs="+",
    )
    parser.add_argument(
        "--column_name",
        help="string that specifies the location of the input_field for vembrane, e.g., FORMAT, INFO or CSQ.",
        type=str,
        nargs=1,
        default=None,
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
        help="integer sample index for all fields_with_sampleindex.",
        type=int,
        nargs=1,
        default=0,
    )
    parser.add_argument(
        "--header",
        help="if enabled, instead of formatting as described only outputs fields that can be used as header for vembrane.",
        action="store_true",
    )
    parser.add_argument(
        "--end_with_comma",
        help="if enabled, prints a comma at the end of the string.",
        action="store_true",
    )

    return parser.parse_args()


def input_check(input_strings):
    for input_string in input_strings:
        if re.fullmatch(r"^[A-Za-z0-9+\-*/\[\]_]+$", input_string) is None:
            raise ValueError(
                f'Error: The input_field "{input_string}" should only contain letters, numbers, square brackets, mathematical operands or underscores.'
            )


def format_field(
    input_field,
    column_name,
    fields_with_sampleindex,
    sampleindex,
    header,
):
    # formatting fields for vembrane input
    def create_field(field_string):
        result = f'{column_name[0]}["{field_string}"]'
        # if sampleindex is defined, it will be appended
        if field_string in fields_with_sampleindex or "all" in fields_with_sampleindex:
            result += f"{sampleindex}"
        return result

    # Formatting fields for header lines: only column_name underscore field
    def create_header(field_string):
        result = f"{column_name[0]}_{field_string}"
        # if sampleindex is defined, it will be appended
        if field_string in fields_with_sampleindex or "all" in fields_with_sampleindex:
            result += f"{sampleindex}"
        return result

    def process_field(mathsplit_field, input_field_formatted):
        # only use letters and underscores (no brackets and numbers)
        only_field = re.sub(r"[^A-Za-z_]", "", mathsplit_field)
        if header is True:
            # create header format
            only_field_formatted = create_header(only_field)
        else:
            # create field format
            only_field_formatted = create_field(only_field)
        # replace from original field; this preserves brackets and numbers from the input.
        input_field_formatted = re.sub(only_field, only_field_formatted, input_field_formatted)
        return input_field_formatted

    # first split input by mathematical operands
    mathsplit_fields = re.split(r"[+\-*/]", input_field)
    # define format_field that will be subsequently manipulated
    input_field_formatted = input_field
    for mathsplit_field in mathsplit_fields:
        # allow number-only fields and do not format them
        if re.match(r"[0-9]", mathsplit_field) is not None:
            pass
        else:
            input_field_formatted = process_field(mathsplit_field, input_field_formatted)

    return input_field_formatted


if __name__ == "__main__":
    args = parse_arguments()

    input_check(args.input_fields)

    # Format the input fields
    output_strings = []
    for input_field in args.input_fields:
        input_field_formatted = format_field(
            input_field,
            args.column_name,
            args.fields_with_sampleindex,
            args.sampleindex,
            args.header,
        )
        output_strings.append(input_field_formatted)

    output = ",".join(output_strings)
    if args.end_with_comma:
        output += ","

    print(output)
