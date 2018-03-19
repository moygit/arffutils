#!/usr/bin/env python


import six
if six.PY2:
    from StringIO import StringIO
else:
    from io import StringIO

import nose
from nose.tools import assert_raises_regexp

import arffutils.utils as ar


TEST_COLS = ["@attribute col1 numeric",
             "@attribute col2 numeric",
             "@attribute col3 {PENDING,IN_REVIEW,APPROVED,DECLINED,CANCELED}",
             "@attribute col4 {FRAUDULENT,UNSET,GOOD}",
             "@attribute col5 {SUCCESSFUL,CHARGEBACK}",
             "@attribute col6 {true,false}"]


def test_get_metadata_works_on_arff():
    # Given this arff:
    arff = StringIO("".join(["% comment\n",
                             "@relation foo\n",
                             "\n",
                             "@attribute a {A,B,C}\n",
                             "\n",
                             "@attribute b {D,E,F}\n",
                             "\n",
                             "@data\n",
                             "A,D\n",
                             "% comment\n",
                             "B,E\n",
                             "C,F\n"]))
    # When we read its metadata and the first following line:
    is_arff, attr_names, attr_lines, all_metadata_lines = ar.get_metadata_if_arff(arff)
    next_line = arff.readline().strip()
    # Then we recognized it as an arff, the metadata is correct,
    # and the first non-metadata line is the first data line:
    assert is_arff
    assert attr_names == ["a", "b"]
    assert attr_lines == ["@attribute a {A,B,C}", "@attribute b {D,E,F}"]
    assert len(all_metadata_lines) == 8
    assert next_line == "A,D"

def test_get_metadata_works_on_nonarff_csv():
    # Given this non-arff csv:
    csv = StringIO("".join(["A,D\n", "B,E\n", "C,F\n"]))
    # When we try to read its metadata and the first following line:
    is_arff, attr_names, attr_lines, all_metadata_lines = ar.get_metadata_if_arff(csv)
    next_line = csv.readline().strip()
    # Then we recognized it as a non-arff, there's no metadata,
    # and the first data line is read correctly:
    assert not is_arff
    assert attr_names == []
    assert attr_lines == []
    assert all_metadata_lines == []
    assert next_line == "A,D"

def test_split_on_condition_works():
    arff = ["@rel foo", "", "@attr a a_type", "@attr b b_type", "@attr c c_type", "", "@data"]
    pre, mid, post = ar.split_on_condition(arff, lambda x: x.startswith("@attr"))
    assert pre == ["@rel foo", ""]
    assert mid == ["@attr a a_type", "@attr b b_type", "@attr c c_type"]
    assert post == ["", "@data"]

def test_delete_works():
    meta = ["@rel foo", "", "@attr a {A,B,C}", "@attr b {D,E,F}", "@attr del_1 numeric",
            "@attr c numeric", "@attr del_2 {G,H,I}", "@attr d numeric", "", "@data"]
    data = ["?,E,9,1.0,G,?", "A,?,?,?,?,2.0", "?,?,?,?,?,?"]
    pre, cols, post = ar.split_on_condition(meta, lambda x: x.startswith("@attr"))
    _, post_del_cols, _, post_del_data = ar.delete_columns(pre, cols, post, data, ["del_1", "del_2"])

    # After deletion and missing-replacement, should be:
    assert post_del_cols == ["@attr a {A,B,C}", "@attr b {D,E,F}", "@attr c numeric", "@attr d numeric"]
    assert post_del_data == ["?,E,1.0,?", "A,?,?,2.0", "?,?,?,?"]

def test_split_on_condition_fails_on_bad_data():
    arff = ["@rel foo", "", "@attr a a_type", "@attr b b_type", "@attr c c_type", "", "@data", "@attr error"]
    error_msg = "condition is true in post-condition segment of list on item @attr error"
    with assert_raises_regexp(TypeError, error_msg):
        ar.split_on_condition(arff, lambda x: x.startswith("@attr"))

def test_split_rows():
    rows = ["1,2,3,4", "5,6,7", "8,9", "10"]
    split_rows = ar.split_rows(rows)
    assert split_rows == [['1', '2', '3', '4'], ['5', '6', '7'], ['8', '9'], ['10']]

def test_join_rows():
    rows = [['1', '2', '3', '4'], ['5', '6', '7'], ['8', '9'], ['10']]
    join_rows = ar.join_rows(rows)
    assert join_rows == ["1,2,3,4", "5,6,7", "8,9", "10"]

def test_get_column_pos_by_name_works():
    positions = ar.get_column_pos_by_name(TEST_COLS, "col2", "col3")
    assert positions == [1, 2]

def test_get_column_pos_by_name_fails_on_missing_name():
    with assert_raises_regexp(KeyError, "Missing column.*: foo"):
        ar.get_column_pos_by_name(TEST_COLS, "col2", "col3", "foo")


if __name__ == '__main__':
    nose.main()
