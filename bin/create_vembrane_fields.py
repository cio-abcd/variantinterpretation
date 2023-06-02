#!/usr/bin/env python

import re
import sys
import argparse

def format_string(input_string, column_name, fields_with_index=None, fieldindex=None, fields_with_sampleindex=None, sampleindex=None):
    if (fields_with_index or fieldindex) and sampleindex is None:
        raise ValueError("Sample index needs to be specified when using fields_with_index or fieldindex.")

    if fields_with_sampleindex is None and sampleindex is not None:
        fields_with_sampleindex = "all"

    if fields_with_index is None and fieldindex is not None:
        raise ValueError("fields_with_index needs to be specified when using fieldindex.")

    def field_format(match):
        field_name = match.group(1)
        if fields_with_index and field_name in fields_with_index:
            if fieldindex is not None:
                return _format_field(field_name, sampleindex, fieldindex)
            else:
                raise ValueError("Field index needs to be specified when using fields_with_index.")
        elif fields_with_sampleindex == "all":
            if sampleindex is not None:
                return _format_field(field_name, sampleindex)
            else:
                raise ValueError("Sample index needs to be specified when using fields_with_sampleindex == all.")
        elif fields_with_sampleindex and field_name in fields_with_sampleindex is not None:
            if sampleindex is not None:
                return _format_field(field_name, sampleindex)
            else:
                raise ValueError("Sample index needs to be specified when using fields_with_sampleindex.")
        else:
            return _format_field(field_name)

    def _format_field(field, sampleindex=None, fieldindex=None):
        result = f'{column_name}["{field}"]'
        if sampleindex is not None:
            result += f'[{sampleindex}]'
            if fieldindex is not None:
                result += f'[{fieldindex}]'
        return result

    formatted_string = re.sub(r'([A-Za-z_]+)', field_format, input_string)
    return formatted_string

if __name__ == '__main__':
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Formats fields (i.e. words) from a string for vembrane input. It outputs the format: column_name["FIELD"][sampleindex][fieldindex]. This script helps to convert input parameters into vembrane language.')
    parser.add_argument('input_string', help='Input string in which fields are defined as linked letters disrupted by non-letters.')
    parser.add_argument('--column_name', help='Can be either FORMAT, INFO or CSQ (or another INFO field annotation supported by vembrane.)')
    parser.add_argument('--fields_with_index', nargs='*', help='Fields to apply fieldindex parameter (requires --sampleindex)')
    parser.add_argument('--fieldindex', type=int, help='Field index for all fields_with_index (requires --sampleindex)')
    parser.add_argument('--fields_with_sampleindex', nargs='?', const='all', help='Fields to apply sampleindex parameter (options: None, all, [fields])')
    parser.add_argument('--sampleindex', type=int, help='Sample index for all fields_with_sampleindex.')

    # Parse the command line arguments
    args = parser.parse_args()

    # Format the string
    try:
        output_string = format_string(args.input_string, args.column_name, args.fields_with_index, args.fieldindex, args.fields_with_sampleindex, args.sampleindex)
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

    # Print the result to stdout
    print(output_string)
