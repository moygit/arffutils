#!/usr/bin/env python


"""Select columns from a csv (could be an arff), either by
column-position or (for an arff) by column-name.

$ cat > input.arff << EOF
@relation input
@attribute key_col numeric
@attribute add_col numeric
@attribute target {a,b}
@data
1,11,a
2,12,b
3,13,a
EOF

$ arffselect -i input.arff -n 0 2
OR
$ arffselect -i input.arff -n key_col target
@relation output
@attribute key_col numeric
@attribute target {a,b}
@data
1,a
2,b
3,a

"""


from __future__ import print_function

import argparse
import csv
import re
import sys

from os.path import basename
from .utils import create_metadata_rows, get_metadata_if_arff
from .io import io_handler


def main():
    """Docstring to make pylint happy."""
    main_with_args(sys.argv[1:])


def main_with_args(unparsed_args):
    """Auxiliary main for easier end-to-end testing."""
    args = parse_args(unparsed_args)
    columns = get_columns_list(args.columns, args.config_file)
    select(args.input_csv, args.output_csv, columns, args.input_csv_delim, args.output_csv_delim)


def parse_args(cmd_line):
    """Parse the given command-line."""
    parser = argparse.ArgumentParser(description="Select columns from a csv")
    parser.add_argument("-i", "--input-csv", default=sys.stdin,
                        help="the csv from which we want to select columns (can be arff)")
    parser.add_argument("-o", "--output-csv", default=sys.stdout,
                        help="the filename of the output csv (is arff if input is arff)")
    cols_group = parser.add_mutually_exclusive_group(required=True)
    cols_group.add_argument("-n", "--columns", nargs="*",
                            help="positions in main-csv of attributes to select, can use col-names for arffs")
    cols_group.add_argument("-f", "--config-file",
                            help="positions in main-csv of attributes to select, " +
                            "specified in whitespace-separated list in config-file")
    parser.add_argument("--input-csv-delim", default=",", help="delimiter in input-csv (default ',')")
    parser.add_argument("--output-csv-delim", default=",", help="delimiter in output-csv (default ',')")
    return parser.parse_args(cmd_line)


def get_columns_list(columns, config_file):
    """Read the list of columns to select either directly from args or
    from the specified config-file.
    """
    if columns is not None:
        return columns
    if config_file is not None:
        with io_handler(config_file) as config:
            return re.split(r"\s+", config.read().strip())
    raise SyntaxError("Dude, don't confuse me by giving both -n (--columns) and -f (--config-file).")


def select(in_file, out_file, col_strs_to_select, input_csv_delim, output_csv_delim):
    """Do the actual selection: read metadata, get columns to select, write metadata, and write rows.

    in_file: file-like object to read from
    out_file: file-like object to write to
    input_csv_delim: delimiter in in_file
    output_csv_delim: delimiter in out_file
    col_strs_to_select: list of columns to select (as strings)
    """
    with io_handler(in_file) as in_, io_handler(out_file, "w") as out_:
        # Read metadata and get columns to select (as integers):
        cols_to_select = handle_metadata_and_get_columns(in_, out_, col_strs_to_select)
        # CSV setup (we've advanced past the metadata):
        reader = csv.reader(in_, delimiter=input_csv_delim)
        writer = csv.writer(out_, delimiter=output_csv_delim, lineterminator="\n")
        # Iterate through the reader and write each new row:
        for line in reader:
            output_line = [line[i] for i in cols_to_select]
            writer.writerow(output_line)


def handle_metadata_and_get_columns(in_, out_, col_strs_to_select):
    """Read metadata if available, get column positions to select, and
    write metadata if necessary.
    """
    # Read metadata and get columns to select (as integers):
    is_arff, attr_names, attr_lines, _ = get_metadata_if_arff(in_)
    cols_to_select = [get_column_to_select(col_str, is_arff, attr_names) for col_str in col_strs_to_select]
    # Write metadata:
    if is_arff:
        attr_lines_to_select = [attr_lines[i] for i in cols_to_select]
        name = remove_known_file_extensions(basename(out_.name)) if hasattr(out_, "name") else "output"
        out_.writelines(create_metadata_rows(name, attr_lines_to_select))
    return cols_to_select


def get_column_to_select(col_str, is_arff, attr_names):
    """Given a column position (as string) or a column name and a list
    of column names, return the integer column position.

    Examples
    ----
    >>> get_column_to_select("1", *, *)
    1
    >>> get_column_to_select("col1", True, ["col0", "col1", "col2"])
    1
    """
    try:
        return int(col_str)
    except ValueError:
        if not is_arff:
            # If the file is a non-arff csv then int'ing above should have worked.
            raise ValueError("can't specify column-pos by name ({}) with non-arff csv".format(col_str))
        try:
            return attr_names.index(col_str)
        except ValueError:
            raise ValueError(col_str + " is not a valid column in the csv/arff")


def remove_known_file_extensions(filename):
    "Remove any of the following extensions from `filename`: arff, csv, txt."
    return re.sub(".(arff|csv|txt)$", "", filename)


if __name__ == "__main__":
    main()
