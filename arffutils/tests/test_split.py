# pylint: disable=missing-docstring
# not necessary here: we know test_split tests arffsplit.py, etc.

import os
import os.path

import nose
import six
if six.PY2:
    from StringIO import StringIO
else:
    from io import StringIO

import arffutils.arffsplit as split


def test_read_key_sets():
    # Given sets:
    set_1 = StringIO("a\t1\nb\t2\nc\t3\n")
    set_2 = StringIO("d\t3\ne\t4\nf\t5\n")
    # When we read these sets in:
    sets = split.read_key_sets([set_1, set_2], key_column=1, delimiter="\t")
    # Then the results should match the input;
    assert sets[0] == set(['1', '2', '3'])
    assert sets[1] == set(['3', '4', '5'])


def test_set_up_and_do_split():
    # Given the following 4-line CSV, we're going to "split" it into the
    # first 3 lines and the last 2 lines:
    input_csv = StringIO("".join(["1,a\n", "2,b\n", "3,c\n", "4,d\n", "5,e\n"]))
    sets = [set(['1', '2', '3']), set(['3', '4'])]  # first 3 lines and last 2 lines
    output_1 = StringIO()
    output_2 = StringIO()
    remainder = StringIO()
    # When:
    cmd_line_args = ["ignore", "-d,", "-k0", "-s", "ignore", "ignore", "-o", "ignore", "ignore", "-r", "ignore"]
    args = split.parse_args(cmd_line_args)
    split.set_up_and_do_split(args, sets, input_csv, [output_1, output_2], remainder)
    # Then first output should be first 3 lines, second output should be last 2 lines:
    assert output_1.getvalue() == "1,a\n2,b\n3,c\n"
    assert output_2.getvalue() == "3,c\n4,d\n"
    assert remainder.getvalue() == "5,e\n"


def test_full_arff():
    # Given:
    data_path = os.path.join(os.path.dirname(__file__), "data", "split")
    input_arff = os.path.join(data_path, "test_input.arff")
    set_1 = os.path.join(data_path, "test_set_1.csv")
    set_2 = os.path.join(data_path, "test_set_2.csv")
    output_file_1 = os.path.join(data_path, "test_output_1.arff")
    output_file_2 = os.path.join(data_path, "test_output_2.arff")
    correct_output_file_1 = os.path.join(data_path, "test_correct_output_1.arff")
    correct_output_file_2 = os.path.join(data_path, "test_correct_output_2.arff")
    remainder_file = os.devnull
    # When:
    split.main_with_args([input_arff, "-d,", "-k0", "--key-column-in-sets", "1", "--delimiter-in-sets", ",",
                          "-s", set_1, set_2, "-o", output_file_1, output_file_2, "-r", remainder_file])
    # Then:
    _verify_identical(output_file_1, correct_output_file_1)
    _verify_identical(output_file_2, correct_output_file_2)


def _verify_identical(file1, file2):
    # Read contents of both files:
    with open(file1) as handle:
        contents1 = handle.read()
    with open(file2) as handle:
        contents2 = handle.read()
    # Verify that they're identical:
    assert contents1 == contents2


if __name__ == '__main__':
    nose.main()
