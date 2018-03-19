"""Merge testing. Test:
- basic functionality
- range specifications work as expected
"""

import os
import os.path
import sys

from nose.tools import assert_raises
import nose

import arffutils.arffmerge as merge


DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "merge")
MAIN_FILE = os.path.join(DATA_PATH, "test_main.arff")
ADD_CSV = os.path.join(DATA_PATH, "test_additional.csv")
ADD_ARFF = os.path.join(DATA_PATH, "test_additional.arff")
ADD_ARFF_2 = os.path.join(DATA_PATH, "test_additional_2.arff")
OUTPUT_FILE_1 = os.path.join(DATA_PATH, "test_output_1.csv")
CORRECT_OUTPUT_FILE_1 = os.path.join(DATA_PATH, "correct_output_1.csv")
OUTPUT_FILE_2 = os.path.join(DATA_PATH, "test_output_2.arff")
CORRECT_OUTPUT_FILE_2 = os.path.join(DATA_PATH, "correct_output_2.arff")
OUTPUT_FILE_3 = os.path.join(DATA_PATH, "test_output_3.arff")
CORRECT_OUTPUT_FILE_3 = os.path.join(DATA_PATH, "correct_output_3.arff")
OUTPUT_FILE_4 = os.path.join(DATA_PATH, "test_output_4.arff")
CORRECT_OUTPUT_FILE_4 = os.path.join(DATA_PATH, "correct_output_4.arff")


def test_basic_merge_non_arff_csv():
    """Basic functionality for non-arff csv files."""
    # When we merge:
    with open(os.devnull, "w") as null:
        saved_stderr, sys.stderr = sys.stderr, null
        merge.main_with_args([MAIN_FILE, ADD_CSV, OUTPUT_FILE_1, "--add-key-col", "1", "-i", "2"])
        sys.stderr = saved_stderr
    # Then the output matches the (pre-saved) correct output:
    with open(OUTPUT_FILE_1) as actual_f, open(CORRECT_OUTPUT_FILE_1) as correct_f:
        actual = actual_f.read()
        correct = correct_f.read()
        assert actual == correct


def test_basic_merge_arff():
    """Basic functionality for arffs."""
    # When we merge:
    merge.main_with_args([MAIN_FILE, ADD_ARFF, OUTPUT_FILE_2, "--add-key-col", "1", "-i", "2"])
    # Then the output matches the (pre-saved) correct output:
    with open(OUTPUT_FILE_2) as actual_f, open(CORRECT_OUTPUT_FILE_2) as correct_f:
        actual = actual_f.read()
        correct = correct_f.read()
        assert actual == correct


def test_no_cols_specified():
    """When we merge with unspecified column-spec (select all):"""
    merge.main_with_args([MAIN_FILE, ADD_ARFF_2, OUTPUT_FILE_3, "--add-key-col", "0", "-i", "1"])
    # Then the output matches the (pre-saved) correct output:
    with open(OUTPUT_FILE_3) as actual_f, open(CORRECT_OUTPUT_FILE_3) as correct_f:
        actual = actual_f.read()
        correct = correct_f.read()
        assert actual == correct


def test_colnum_range_unbounded():
    """When we merge with unbounded column-spec by number (e.g. "1:"):"""
    merge.main_with_args([MAIN_FILE, ADD_ARFF_2, OUTPUT_FILE_3, "--add-key-col", "0", "-i", "1:"])
    # Then the output matches the (pre-saved) correct output:
    with open(OUTPUT_FILE_3) as actual_f, open(CORRECT_OUTPUT_FILE_3) as correct_f:
        actual = actual_f.read()
        correct = correct_f.read()
        assert actual == correct


def test_colnum_range_bounded():
    """When we merge with bounded column-spec by number (e.g. "1:2"):"""
    merge.main_with_args([MAIN_FILE, ADD_ARFF_2, OUTPUT_FILE_4, "--add-key-col", "0", "-i", "1:2"])
    # Then the output matches the (pre-saved) correct output:
    with open(OUTPUT_FILE_4) as actual_f, open(CORRECT_OUTPUT_FILE_4) as correct_f:
        actual = actual_f.read()
        correct = correct_f.read()
        assert actual == correct


def test_colname_range_bounded():
    """When we merge with bounded column-spec by name (e.g. "add_col_2:add_col_3"):"""
    merge.main_with_args([MAIN_FILE, ADD_ARFF_2, OUTPUT_FILE_4, "--add-key-col", "0", "-i", "add_col_2:add_col_3"])
    # Then the output matches the (pre-saved) correct output:
    with open(OUTPUT_FILE_4) as actual_f, open(CORRECT_OUTPUT_FILE_4) as correct_f:
        actual = actual_f.read()
        correct = correct_f.read()
        assert actual == correct


def test_colname_needs_nonarff():
    """When we specify columns by name for a non-arff CSV we should error:"""
    args = [MAIN_FILE, ADD_CSV, OUTPUT_FILE_1, "--add-key-col", "1", "-i", "add_col_3"]
    # Then the merge fails:
    assert_raises(ValueError, merge.main_with_args, args)


if __name__ == '__main__':
    nose.main()
