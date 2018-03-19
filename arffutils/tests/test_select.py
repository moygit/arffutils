# pylint: disable=missing-docstring
# not necessary here: we know test_select tests arffselect.py, etc.

from nose.tools import assert_raises
import nose
import six

import arffutils.arffselect as select

if six.PY2:
    from StringIO import StringIO
else:
    from io import StringIO


ARFF_META = "".join(["@relation foo\n",
                     "\n",
                     "@attribute col0 numeric\n",
                     "@attribute col1 numeric\n",
                     "@attribute col2 numeric\n",
                     "\n",
                     "@data\n"])
CSV_DATA = "1,2,5\n" + "3,4,6\n"


def test_get_columns_list():
    assert_raises(SyntaxError, select.get_columns_list, None, None)
    _test_case_for_get_columns_list(["1", "2"], None, ["1", "2"])
    _test_case_for_get_columns_list(["1", "2"], StringIO("2 3"), ["1", "2"])
    _test_case_for_get_columns_list(None, StringIO("2 3"), ["2", "3"])


def _test_case_for_get_columns_list(cols, config, expected):
    # When:
    result = select.get_columns_list(cols, config)
    # Then:
    if isinstance(result, str):
        assert result == expected
    else:
        assert set(result) == set(expected)


def test_handle_metadata_and_get_columns():
    _test_case_for_h_m_g_c(CSV_DATA, ["0", "1", "2"], expected_result=[0, 1, 2])
    _test_case_for_h_m_g_c(CSV_DATA, ["col0", "col1"], expected_err=ValueError)
    _test_case_for_h_m_g_c(ARFF_META + CSV_DATA, ["col0", "col1", "col2"],
                           expected_result=[0, 1, 2], expected_out=ARFF_META)
    _test_case_for_h_m_g_c(ARFF_META + CSV_DATA, ["col0", "col3"], expected_err=ValueError)


def _test_case_for_h_m_g_c(csv_str, cols_to_select, expected_result=None, expected_err=None, expected_out=None):
    # Given:
    in_ = StringIO(csv_str)
    out_ = StringIO()
    if expected_err is not None:
        # When/then:
        assert_raises(expected_err, select.handle_metadata_and_get_columns, in_, out_, cols_to_select)
    if expected_result is not None:
        # When:
        result = select.handle_metadata_and_get_columns(in_, out_, cols_to_select)
        # Then:
        assert result == expected_result
        if expected_out is not None:
            assert out_.getvalue() == expected_out.replace("foo", "output")


def test_select():
    expected_arff_meta = "".join(["@relation foo\n",
                                  "\n",
                                  "@attribute col1 numeric\n",
                                  "\n",
                                  "@data\n"])
    expected_csv_data = "2\n" + "4\n"
    expected_arff = expected_arff_meta + expected_csv_data
    arff = ARFF_META + CSV_DATA
    _run_test_case_for_select(CSV_DATA, ["1"], expected_out=expected_csv_data)
    _run_test_case_for_select(CSV_DATA, ["col1"], expected_err=ValueError)
    _run_test_case_for_select(arff, ["1"], expected_out=expected_arff)
    _run_test_case_for_select(arff, ["col1"], expected_out=expected_arff)
    _run_test_case_for_select(arff, ["col3"], expected_err=ValueError)


def test_col_swap():
    expected_arff_meta = "".join(["@relation foo\n",
                                  "\n",
                                  "@attribute col2 numeric\n",
                                  "@attribute col1 numeric\n",
                                  "\n",
                                  "@data\n"])
    expected_csv_data = "5,2\n" + "6,4\n"
    expected_arff = expected_arff_meta + expected_csv_data
    arff = ARFF_META + CSV_DATA
    _run_test_case_for_select(arff, ["col2", "col1"], expected_out=expected_arff)


def _run_test_case_for_select(csv_str, cols_to_select, expected_err=None, expected_out=None):
    # Given:
    in_ = StringIO(csv_str)
    out_ = StringIO()
    if expected_err is not None:
        # When/then:
        assert_raises(expected_err, select.select, in_, out_, cols_to_select, ",", ",")
    if expected_out is not None:
        # When:
        select.select(in_, out_, cols_to_select, ",", ",")
        # Then
        assert out_.getvalue() == expected_out.replace("foo", "output")


if __name__ == '__main__':
    nose.main()
