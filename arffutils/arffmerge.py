#!/usr/bin/env python


"""Read in a main csv (could be an arff) and an additional csv (could
be an arff), insert columns from the additional csv into the main csv
(joining on a key column), and write an output csv (or arff).

Example
----
$ cat > main.arff << EOF
@relation main
@attribute key_col numeric
@attribute target {true,false}
@data
1,true
2,false
EOF

$ cat > additional_input_cols.arff << EOF
@relation additional_input_cols
@attribute key_col numeric
@attribute add_col numeric
@attribute target {a,b}
@data
1,11,a
2,12,b
3,13,a
EOF

$ arffmerge main.arff additional_input_cols.arff output.arff --add-input-position 1:2
OR
$ arffmerge main.arff additional_input_cols.arff output.arff --add-input-position add_col:target

$ cat output.arff
@relation output
@attribute key_col numeric
@attribute add_col numeric
@attribute target {true,false}
@data
1,11,true
2,12,false

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
    add_attr_lines, add_data = get_additional_csv(args)
    read_add_write(args, add_attr_lines, add_data)


def parse_args(cmd_line):
    """Parse the given command-line."""
    parser = argparse.ArgumentParser(description="Merge columns from two csvs using a key column to join.")
    parser.add_argument("main_csv", help="the csv to which we want to add new columns (can be arff)")
    parser.add_argument("add_cols_csv", help="the csv from which we want to read the additional columns (can be arff)")
    parser.add_argument("output_csv", help="the filename of the output csv (is arff if input is arff)")
    parser.add_argument("-o", "--output-position", default=-1, type=int,
                        help="position in main-csv to insert new columns (default: before last)")
    parser.add_argument("-i", "--add-input-position", default="1:",
                        help="position in add-cols-csv of attributes to select, " +
                        "can use col-names for arffs (default 1:)")
    parser.add_argument("--main-csv-delim", default=",",
                        help="delimiter in main-csv (default ',')")
    parser.add_argument("--add-csv-delim", default=",",
                        help="delimiter in add-cols-csv (default ',')")
    parser.add_argument("--output-csv-delim", default=",",
                        help="delimiter in output-csv (default ',')")
    parser.add_argument("--main-key-col", type=int, default=0,
                        help="index of key column in main-csv (default 0)")
    parser.add_argument("--add-key-col", type=int, default=0,
                        help="index of key column in add-cols-csv (default 0)")
    return parser.parse_args(cmd_line)


def get_additional_csv(args):
    """Read in the required columns from the 'additional-csv' file as
    a dictionary with the key-column as the dictionary key.
    """
    with io_handler(args.add_cols_csv) as add_file:
        is_arff, attr_names, attr_lines, _ = get_metadata_if_arff(add_file)
        first, last = parse_additional_cols_args(args.add_input_position, is_arff, attr_names)
        key_col, delim = args.add_key_col, args.add_csv_delim
        return (attr_lines[first:last],
                {line[key_col]: line[first:last] for line in csv.reader(add_file, delimiter=delim)})


def parse_additional_cols_args(pos_string, is_arff, attr_names):
    """Parse the column-specification for the additional-columns csv.
    It can be numeric, e.g. 1, 1:, 1:15, or if the file is an arff it
    can use column-names, e.g. Col1, Col1: Col1:Col15.
    """
    def get_column_pos(pos_str):
        """pos_str could be a numeric string or a col-name.
        Convert it to integer position.
        """
        try:
            return int(pos_str)
        except ValueError:
            if not is_arff:
                # If the file is a csv then int'ing above should have worked.
                raise ValueError("can't specify column-pos by name ({}) with non-arff csv".format(pos_str))
            pos = attr_names.index(pos_str)
            if pos == -1:
                raise ValueError(pos_str + " is not a valid column in the additional-columns file")
            else:
                return pos
    pos_pair = pos_string.split(":")
    first = get_column_pos(pos_pair[0])
    if len(pos_pair) == 1 or not pos_pair[1]:
        second = None
    else:
        second = get_column_pos(pos_pair[1])
    return first, second


def read_add_write(args, add_attr_lines, add_data):
    """Do the main work: read in the input csv, look for the
    key-column in the dictionary of additional cols, and write
    the new row out to the output csv.
    """
    with io_handler(args.main_csv) as in_file, io_handler(args.output_csv, "w") as out_file:
        # Basic setup and metadata:
        key_col, output_pos = args.main_key_col, args.output_position
        is_arff = handle_arff_headers(in_file, out_file, add_attr_lines, output_pos)
        missing = (['?'] if is_arff else ['']) * get_data_width(add_data)
        # CSV setup (we've advanced past the metadata):
        reader = csv.reader(in_file, delimiter=args.main_csv_delim)
        writer = csv.writer(out_file, delimiter=args.output_csv_delim, lineterminator="\n")
        # Iterate through the reader and write each new row:
        for line in reader:
            inv_id = line[key_col]
            try:
                line_to_add = add_data[inv_id]
            except KeyError:
                print("Warning: key {} does not have additional data row".format(inv_id), file=sys.stderr)
                line_to_add = missing
            output_line = line[:output_pos] + line_to_add + line[output_pos:]
            writer.writerow(output_line)


def handle_arff_headers(in_file, out_file, add_attr_lines, output_pos):
    """If the input csv is an arff then get its metadata and write it
    to the output csv (arff). If the additional csv is also an arff
    then get its metadata as well and add the additional columns'
    metadata to the output metadata.
    """
    is_arff, _, attr_lines, _ = get_metadata_if_arff(in_file)
    if attr_lines and add_attr_lines:
        # The additional csv is an arff; add metadata.
        attr_lines = attr_lines[:output_pos] + add_attr_lines + attr_lines[output_pos:]
    else:
        print("Warning: merging non-arff csv into arff; you'll need to hand-edit the metadata.", file=sys.stderr)
    out_file.writelines(create_metadata_rows(remove_known_extensions(basename(out_file.name)), attr_lines))
    return is_arff


def remove_known_extensions(filename):
    "Remove any of the following extensionf from `filename`: arff, csv, txt."
    return re.sub(".(arff|csv|txt)$", "", filename)


def get_data_width(dict_of_lists):
    """Given a dictionary of the form {k1: list1, k2, list2, etc.},
    return the length of list1.
    """
    first_row = list(dict_of_lists.values())[0]
    return len(first_row)


if __name__ == "__main__":
    main()
