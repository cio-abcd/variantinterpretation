#!/usr/bin/env python

import re
import argparse
from typing import List, Union

class input_fields:
    """
    Converts a string of comma-separated values into a list of strings (to_list).
    Validates input only contains letters, numbers, square brackets, mathematical operands or underscores (input_check).
    """

    def __init__(self, vstr, sep=","):
        """
        vstr (str): The input string containing separated values.
        sep (str): The separator used in the string (default is ',').
        """
        self.vstr = vstr
        self.sep = sep
        parsed_list = self.to_list()
        self.input_check(parsed_list)
        self.values = parsed_list

    def input_check(self, input_strings):
        for input_string in input_strings:
            if re.fullmatch(r"^[A-Za-z0-9+\-*/\[\]_,]+$", input_string) is None:
                raise ValueError(
                    f'Error: The input_field "{input_string}" should only contain letters, numbers, '
                    f'square brackets, mathematical operands or underscores. '
                    f'Separate entries are separated by "{self.sep}".'
                )

    def to_list(self):
        values = [v.strip() for v in self.vstr.split(self.sep)]
        return values
    
    def __iter__(self):
        return iter(self.values)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='The general purpose of this script is to easily convert annotation fields into vembrane input parameters. \
        The input are field names from the INFO/FORMAT column or CSQ annotation string in the VCF file. \
        The output has the format: column_name["input_field"] FOR INFO and CSQ column and FORMAT["format_field"][sampleindex] for FORMAT column fields. \
        You can also directly perform calculation operations which will be transcribed to vembrane-compatible fields. \
        , e.g. , AD[1]/DP in --format_fields will be converted to FORMAT["AD"][sampleindex][0]/FORMAT["DP"][sampleindex]. \
        Vembrane interprets this operation and divides the AD value by the DP value.'
    )
    parser.add_argument(
        "--csq_fields",
        help="comma-separated CSQ fields. The fields only allow letters, numbers, underscores, square brackets and mathematical operands.",
        type=input_fields,
        nargs="+",
    )
    parser.add_argument(
        "--format_fields",
        help="comma-separated FORMAT fields. The fields only allow letters, numbers, underscores, square brackets and mathematical operands.",
        type=input_fields,
        nargs="+",
    )
    parser.add_argument(
        "--info_fields",
        help="comma-separated INFO fields. The fields only allow letters, numbers, underscores, square brackets and mathematical operands.",
        type=input_fields,
        nargs="+",
    )
    parser.add_argument(
        "--other_fields",
        help="comma-separated or space-separated fields. This field will NOT be formatted and just added to vembrane and header line. The fields only allow letters, numbers, underscores, square brackets and mathematical operands.",
        type=str,
        nargs="+",
    )
    parser.add_argument(
        "--allele_fraction",
        help="Specify here how to calculate allele_fraction. Only allows values: FORMAT_AF, FORMAT_AD, mutect2, freebayes.",
        choices=["FORMAT_AF", "FORMAT_AD", "mutect2", "freebayes"],
        type=str,
    )
    parser.add_argument(
        "--read_depth",
        help='Specify here from which FORMAT field to extract read depth. The column will always be named "read_depth" for downstream compatibility.',
        type=str,
    )
    parser.add_argument(
        "--file_out",
        help="output file for temporary storing vembrane and header strings.",
        type=str,
    )

    return parser.parse_args()

def formatting_field(
    input_field: str,
    column_name: str,
    all_samples: bool,
) -> str:
    """
    This function formats a single field according to vembrane input. It generates an vembrane input string and header string.
    The fields are split by mathematical operands, which are then processed by formatting_mathfield().
    """

    def formatting_mathfield(mathsplit_field: str, input_field: str) -> str:
        # only use letters and underscores (no brackets and numbers)
        only_field = re.sub(r"[^A-Za-z_]", "", mathsplit_field)

        # Formatting fields for header lines: only column_name underscore field
        header_field = f"{column_name}_{only_field}"
        # formatting fields for vembrane input
        only_field_formatted = f'{column_name}["{only_field}"]'

        # add sample index fields
        if all_samples:
            header_field += "[{sample}]"
            only_field_formatted += "[s]"

        # replace from original field; this preserves brackets and numbers from the input.
        header_field = re.sub(only_field, header_field, input_field)
        input_field_formatted = re.sub(only_field, only_field_formatted, input_field)

        # if all_samples is true, iterate through each sample in vembrane
        if all_samples:
            header_field = 'for_each_sample(lambda sample: f"' + header_field + '")'
            input_field_formatted = (
                "for_each_sample(lambda s: " + input_field_formatted + ")"
            )

        return input_field_formatted, header_field

    # first split input by mathematical operands
    mathsplit_fields = re.split(r"[+\-*/]", input_field)
    # define format_field that will be subsequently manipulated
    for mathsplit_field in mathsplit_fields:
        # allow number-only fields and do not format them
        if re.match(r"[0-9]", mathsplit_field) is not None:
            pass
        else:
            input_field, header_field = formatting_mathfield(
                mathsplit_field, input_field
            )

    return input_field, header_field

def flatten(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]

if __name__ == "__main__":
    args = parse_arguments()
    vembrane_strings = []
    header_strings = []

    if args.other_fields:
        # Formatting fields coming from external arguments.
        for other_field in args.other_fields:
            vembrane_strings.append(other_field)
            header_strings.append(other_field)

    # add allele fraction in here
    if args.allele_fraction:
        if args.allele_fraction in ["mutect2", "FORMAT_AF"]:
            vembrane_strings.append(
                'for_each_sample(lambda s: FORMAT["AF"][s] if FORMAT["AF"][s] else None)'
            )
            header_strings.append(
                'for_each_sample(lambda sample: f"allele_fraction{sample}")'
            )
        elif args.allele_fraction in ["freebayes", "FORMAT_AD"]:
            vembrane_strings.append(
                'for_each_sample(lambda s: FORMAT["AD"][s][1]/FORMAT["DP"][s] if FORMAT["AD"][s][1] and FORMAT["DP"][s] else None)'
            )
            header_strings.append(
                'for_each_sample(lambda sample: f"allele_fraction{sample}")'
            )
        else:
            raise ValueError("ERROR: Did not specify correct allele_fraction.")

    # add read depth
    if args.read_depth:
        vembrane_strings.append(
            'for_each_sample(lambda s: FORMAT["' + str(args.read_depth) + '"][s])'
        )
        header_strings.append('for_each_sample(lambda sample: f"read_depth{sample}]")')

    if args.format_fields:
        args.format_fields = flatten(args.format_fields)
        # Formatting the FORMAT fields.
        for format_field in args.format_fields:
            format_field, format_header_field = formatting_field(
                input_field=format_field,
                column_name="FORMAT",
                all_samples=True,
            )
            vembrane_strings.append(format_field)
            header_strings.append(format_header_field)

    if args.info_fields:
        args.info_fields = flatten(args.info_fields)
        # Formatting the INFO fields.
        for info_field in args.info_fields:
            info_field, info_header_field = formatting_field(
                input_field=info_field,
                column_name="INFO",
                all_samples=False,
            )
            vembrane_strings.append(info_field)
            header_strings.append(info_header_field)

    if args.csq_fields:
        # First flatten list of lists generated by splitting comma-separated values
        args.csq_fields = flatten(args.csq_fields)
        # Formatting the CSQ fields.
        for csq_field in args.csq_fields:
            csq_field, csq_header_field = formatting_field(
                input_field=csq_field,
                column_name="CSQ",
                all_samples=False,
            )
            vembrane_strings.append(csq_field)
            header_strings.append(csq_header_field)

    vembrane_out = ",".join(vembrane_strings)
    header_out = ",".join(header_strings)

    with open(args.file_out, "wt") as f:
        f.write(vembrane_out + "\n" + header_out)
