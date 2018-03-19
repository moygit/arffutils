#!/usr/bin/env python


"""Read in a main csv (could be an arff) and N possibly-overlapping
sets of keys, and split the rows of the csv into N csvs (or arffs)
depending on which set(s) each row's key is in.

Rows for keys not in any of the sets are written to the specified
"remainder" file.

Example
----

$ arffsplit in.arff -d, -k1 -n2 \
        -s ./key_set_1.txt ./key_set_2.txt \
        -o ./out_1.arff ./out_2.arff \
        -r ./remainder.arff

"""


from __future__ import print_function

from os.path import basename

import argparse
import csv
import re
import sys

import six

from .utils import create_metadata_rows, get_metadata_if_arff
from .io import io_handler

if six.PY2:
    from contextlib2 import ExitStack
else:
    from contextlib import ExitStack


def main():
    """Docstring to make pylint happy."""
    main_with_args(sys.argv[1:])


def main_with_args(cmd_line):
    """Auxiliary main for easier end-to-end testing."""
    args = parse_args(cmd_line)
    key_sets = read_key_sets(args.set_file_names, args.key_column_in_sets, args.delimiter_in_sets)
    set_up_and_do_split(args, key_sets, args.file_to_split, args.output_file_names, args.remainder_file_name)


def parse_args(cmd_line):
    """Parse the given command-line."""
    parser = argparse.ArgumentParser(description="Split a given file by key " +
                                     "given two or more sets of keys")
    parser.add_argument("file_to_split")
    parser.add_argument("-d", "--delimiter", default=",", help="delimiter in file to split (default comma)")
    parser.add_argument("-k", "--key-column-in-main-csv", type=int, default=0,
                        help="column number of key in file to split (default 0)")
    parser.add_argument("--key-column-in-sets", type=int, default=0,
                        help="column number of key in key-set files (default 0)")
    parser.add_argument("--delimiter-in-sets", default=",",
                        help="delimiter in key-set files (default comma)")
    parser.add_argument("-s", "--set-file-names", required=True, nargs="*", help="filenames of sets specified")
    parser.add_argument("-o", "--output-file-names", required=True, nargs="*", help="filenames to write output")
    parser.add_argument("-r", "--remainder-file-name", required=True,
                        help="filename to write remaining rows (i.e. whose keys are not in any set)")
    args = parser.parse_args(cmd_line)
    if len(args.output_file_names) != len(args.set_file_names):
        parser.error("Number of output filenames needs to match number of set filenames.")
    return args


def read_key_sets(key_set_filenames, key_column, delimiter):
    "Given the filenames of N sets of keys, read them in as sets."
    def read_set(file_name):
        "Read a single set."
        with io_handler(file_name) as file_:
            reader = csv.reader(file_, delimiter=delimiter)
            return set([line[key_column] for line in reader if line])
    return [read_set(file_name) for file_name in key_set_filenames]


def copy_metadata_if_arff(in_file, out_files):
    """If the input file is an arff then get its metadata and write it
    to the output file(s).
    """
    is_arff, _, attr_lines, _ = get_metadata_if_arff(in_file)
    if is_arff:
        for out_file in out_files:
            rel_name = remove_known_extensions(basename(out_file.name))
            out_file.writelines(create_metadata_rows(rel_name, attr_lines))


def remove_known_extensions(filename):
    "Remove any of the following extensionf from `filename`: arff, csv, txt."
    return re.sub(".(arff|csv|txt)$", "", filename)


def set_up_and_do_split(args, key_sets, in_filename, out_filenames, rmdr_filename):
    """Read in the file to split and write each line to the
    appropriate file decided by its key (if key is in set N then write
    to file N)
    """
    with io_handler(in_filename) as in_file, io_handler(rmdr_filename, "w") as rmdr_file, ExitStack() as file_stack:
        out_files = [file_stack.enter_context(io_handler(fname, "w")) for fname in out_filenames]
        # Arff metadata if necessary (NOTE: we're writing to rmdr_file as well):
        copy_metadata_if_arff(in_file, out_files + [rmdr_file])
        # Set up CSV reader and writers:
        reader = csv.reader(in_file, delimiter=args.delimiter)
        writers = [csv.writer(out_file, delimiter=args.delimiter, lineterminator="\n") for out_file in out_files]
        rmdr_writer = csv.writer(rmdr_file, delimiter=args.delimiter, lineterminator="\n")
        # And do the actual split:
        split_file(reader, args.key_column_in_main_csv, key_sets, writers, rmdr_writer)


def split_file(reader, key_column, key_sets, writers, rmdr_writer):
    """Do the actual split: iterate, check each line's key, and write."""
    for i, line in enumerate(reader):
        if i % 500000 == 0:
            print(i, "...", end="")
            sys.stdout.flush()
        key_ = line[key_column]
        written = False
        for index, key_set in enumerate(key_sets):
            if key_ in key_set:
                writers[index].writerow(line)
                written = True
        if not written:
            rmdr_writer.writerow(line)
    print("done!")


if __name__ == "__main__":
    main()
