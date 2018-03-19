#!/usr/bin/env python

"""arff-handling utility functions used in other scripts.

NOTE: most of these are part of an earlier approach and are now deprecated.
I hope to clean them out gradually.
"""

import os.path
import re
import sys


import warnings

# Hat tip:
# https://wiki.python.org/moin/PythonDecoratorLibrary#Generating_Deprecation_Warnings
def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""
    def new_func(*args, **kwargs):
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


def get_metadata_if_arff(in_file):
    """If the given in_file is an arff then get its meta-data and
    fast-forward it past the meta-data. in_file needs to support the
    seek method so we can reset it if it's not an arff.

    Returns:
    - is_arff: boolean saying whether it's an arff
    - attr_names: list of attribute names
    - attr_lines: list of complete attribute lines
    - all_metadata_lines: list of all metadata lines (including comments and blank lines)
    """
    # Define basic regexes used for arff-handling:
    comment = re.compile(r'^%')
    empty = re.compile(r'^\s+$')
    relation = re.compile(r'''^@[Rr][Ee][Ll][Aa][Tt][Ii][Oo][Nn]\s*(([^']\S*)|('[^{},%].*')|("[^{},%].*"))$''')
    datameta = re.compile(r'^@[Dd][Aa][Tt][Aa]')
    attribute = re.compile(r'^@[Aa][Tt][Tt][Rr][Ii][Bb][Uu][Tt][Ee]\s*(..*$)')

    # Skip past empty lines or comments:
    attr_names, attr_lines, all_metadata_lines = [], [], []
    line = in_file.readline().strip()
    while comment.match(line) or empty.match(line):
        all_metadata_lines.append(line)
        line = in_file.readline().strip()
    # First non-empty non-comment; it it a "relation" line?
    is_arff = relation.match(line) is not None

    if is_arff:
        # Add the relation line we just read:
        all_metadata_lines.append(line)
        # And read the rest of the metadata:
        while not datameta.match(line):
            line = in_file.readline().strip()
            all_metadata_lines.append(line)
            if attribute.match(line):
                attr_lines.append(line)
                attr_names.append(line.split()[1])
    else:
        # Not an arff; nothing to write, just reset.
        in_file.seek(0)
    return is_arff, attr_names, attr_lines, all_metadata_lines


def create_metadata_rows(rel_name, attr_lines):
    """Given a relation name and a list of all attribute lines,
    return the full list of all metadata rows.
    """
    lines = ["@relation " + rel_name, ""] + attr_lines + ["", "@data"]
    return [line + "\n" for line in lines]


# The following is old code that is still used in a few places, e.g.
# in the weight-calculation script. Deprecated because these will
# likely cause issues for large arffs.

@deprecated
def read_file_metadata(in_):
    "Read only the ARFF metadata from a file or stream."
    if isinstance(in_, str) and os.path.isfile(in_):
        in_ = open(in_)
    data = []
    for line in in_:
        data.append(line.strip("\n"))
        if line == "@data\n":
            break
    in_.close()
    return data

@deprecated
def read_file(in_):
    "Read from file or stream."
    if isinstance(in_, str) and os.path.isfile(in_):
        in_ = open(in_)
    data = in_.read().splitlines()
    in_.close()
    return data

@deprecated
def write_file(out_, lines):
    "Write the given lines to the given file or stream (out_)."
    if lines[0][-1] != "\n":
        lines = [line + "\n" for line in lines]
    if isinstance(out_, str):
        out_ = open(out_, 'w')
    out_.writelines(lines)
    if out_ != sys.stdout:
        out_.close()

@deprecated
def separate_arff_headers(filename, details=False):
    """Divide an arff into meta-data + data. If `details` is True then
    further split meta-data into pre-attribute-rows, attribute-rows,
    and post-attribute-rows.
    """
    lines = read_file(filename)
    data_pos = 1 + lines.index('@data')
    meta, data = lines[:data_pos], lines[data_pos:]
    if details:
        pre, cols, post = split_on_condition(meta, lambda row: row.startswith("@attribute"))
        return pre, cols, post, data
    else:
        return meta, data

@deprecated
def split_rows(rows):
    "Split a CSV row stupidly (i.e. don't look for commas inside quotes)."
    return [row.split(',') for row in rows]

@deprecated
def join_rows(rows):
    "Join a CSV row stupidly (i.e. don't look for commas inside quotes)."
    return [','.join(row) for row in rows]

@deprecated
def split_on_condition(lis_, condition_func):
    """Split a list based on a given condition: return the portions
    before the condition is true, while it's true, and after it's
    true.
    """
    pre, mid, post = [], [], []
    in_pre, in_mid, in_post = True, False, False
    for item in lis_:
        if in_pre:
            if condition_func(item):
                in_pre, in_mid = False, True
                mid.append(item)
            else:
                pre.append(item)
            continue
        if in_mid:
            if condition_func(item):
                mid.append(item)
            else:
                in_mid, in_post = False, True
                post.append(item)
            continue
        if in_post:
            if condition_func(item):
                raise TypeError("condition is true in post-condition segment of list on item {}".format(item))
            else:
                post.append(item)
            continue
    return pre, mid, post

@deprecated
def get_column_pos_by_name(arff_cols, *wanted_cols):
    """Given a list of column-names and a list of wanted column-names,
    return the indices of the wanted columns in the full list.
    """
    arff_cols = [row.split()[1] for row in arff_cols]
    # Check that all wanted columns exist:
    arff_cols_set = set(arff_cols)
    missing = [col for col in wanted_cols if col not in arff_cols_set]
    if missing:
        raise KeyError("Missing column(s): " + ", ".join(missing))
    # Nothing missing, get the columns we want:
    wanted_cols = set(wanted_cols)
    return [i for i, col in enumerate(arff_cols) if col in wanted_cols]

@deprecated
def _delete_specified_positions(list_, positions_to_delete):
    "Get a copy of the list with the items in the specified positions deleted."
    return [item for i, item in enumerate(list_) if i not in positions_to_delete]

@deprecated
def delete_columns(pre, cols, post, data, cols_to_delete):
    "Delete arff attributes from metadata and data."
    indices_to_delete = get_column_pos_by_name(cols, *cols_to_delete)
    new_cols = _delete_specified_positions(cols, indices_to_delete)
    new_data = join_rows([_delete_specified_positions(row, indices_to_delete) for row in split_rows(data)])
    return pre, new_cols, post, new_data
