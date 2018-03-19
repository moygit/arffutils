# pylint: disable=missing-docstring
# not necessary here: we know test_metrics tests arffmetrics.py, etc.

import io
import os.path

import nose

import arffutils.arff as arff
import arffutils.arffmetrics as metrics


_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "metrics")
_TRAIN_FILE = os.path.join(_DATA_PATH, "train.arff")
_TEST_FILE = os.path.join(_DATA_PATH, "test.arff")
_STATS_REPORT_FILE = os.path.join(_DATA_PATH, "stats_report.html")
_CORRECT_STATS_REPORT_FILE = os.path.join(_DATA_PATH, "correct_stats_report.html")
_COMP_REPORT_FILE = os.path.join(_DATA_PATH, "comp_report.html")
_CORRECT_COMP_REPORT_FILE = os.path.join(_DATA_PATH, "correct_comp_report.html")


_TRAIN_STR = u"@attribute numeric_col_1 numeric" + "\n" + \
              "@attribute numeric_col_2 numeric" + "\n" + \
              "@attribute {} {{false,true}}".format(metrics.TARGET_CLASS_NAME) + "\n" + \
              "@data" + "\n" + \
              "1.0,1.0,false" + "\n" + \
              "2.0,1.0,false" + "\n" + \
              "3.0,1.0,false" + "\n" + \
              "4.0,1.0,false" + "\n" + \
              "5.0,1.0,true"
_TRAIN = arff.Arff(io.StringIO(_TRAIN_STR), "train")

_TEST_STR = u"@attribute numeric_col_1 numeric" + "\n" + \
             "@attribute numeric_col_2 numeric" + "\n" + \
             "@attribute {} {{false,true}}".format(metrics.TARGET_CLASS_NAME) + "\n" + \
             "@data" + "\n" + \
             "5.0,2.0,true" + "\n" + \
             "4.0,2.0,false" + "\n" + \
             "3.0,2.0,false" + "\n" + \
             "2.0,2.0,false" + "\n" + \
             "1.0,2.0,false"
_TEST = arff.Arff(io.StringIO(_TEST_STR), "test")

_NUMERIC_1 = metrics.NumericFeatureStats("numeric_col_1", _TRAIN, _TEST)
_NUMERIC_2 = metrics.NumericFeatureStats("numeric_col_2", _TRAIN, _TEST)
_TRAIN_STATS = metrics.DataSetStats(_TRAIN)
_COMP_STATS = metrics.DataSetComparison(_TRAIN, _TEST)


def test_numeric_col_1_stats():
    stats = _NUMERIC_1.stats
    assert len(stats) == 3
    for each_stat in stats.items():
        assert len(each_stat) == 2
    assert stats["all"]["train"]["Pct missing"] == 0.0
    assert stats["all"]["train"]["Median"] == 3.0
    assert stats["all"]["train"]["Min"] == 1.0
    assert stats["all"]["train"]["Max"] == 5.0
    assert stats["all"]["train"]["Mean"] == 3.0
    assert stats["all"]["train"]["Skew"] == 0.0
    assert stats["all"]["train"]["F vs T KS"] == 1.0

    assert stats["all"]["test"]["Median"] == 3.0
    assert stats["false"]["train"]["Median"] == 2.5
    assert stats["false"]["test"]["Median"] == 2.5
    assert stats["true"]["train"]["Median"] == 5.0
    assert stats["true"]["test"]["Median"] == 5.0

def test_numeric_col_2_stats():
    stats = _NUMERIC_2.stats
    assert len(stats) == 3
    for each_stat in stats.items():
        assert len(each_stat) == 2
    assert stats["all"]["train"]["Pct missing"] == 0.0
    assert stats["all"]["train"]["Median"] == 1.0
    assert stats["all"]["train"]["Min"] == 1.0
    assert stats["all"]["train"]["Max"] == 1.0
    assert stats["all"]["train"]["Mean"] == 1.0
    assert stats["all"]["train"]["Stdev"] == 0.0
    assert stats["all"]["train"]["Skew"] == 0.0
    assert stats["all"]["train"]["F vs T KS"] == 0.0

def test_stats_table():
    table = _NUMERIC_1._get_stats_table()
    assert len(table) == 7
    # Check column-headers:
    headers = table[0]
    assert headers == ["SETS"] + metrics.ALL_STAT_NAMES
    # Check row headers (i.e. column 1):
    col_1 = list(zip(*table))[0]
    row_headers = ('SETS', 'train (all)', 'test (all)', 'train (false)',
                   'test (false)', 'train (true)', 'test (true)')
    assert col_1 == row_headers

def test_train_dataset_stats():
    # Check counts:
    expected_counts = [['Counts for dataset', 'all', 'false', 'true'], ['train', 5, 4, 1]]
    assert _TRAIN_STATS._get_counts() == expected_counts
    # Check numeric_col_1 stats:
    train_stats_num_1 = _TRAIN_STATS.stats["numeric_col_1"]["stats"]
    num_1_stats = _NUMERIC_1.stats["all"]["train"]
    assert num_1_stats == train_stats_num_1
    # Check numeric_col_2 stats:
    train_stats_num_2 = _TRAIN_STATS.stats["numeric_col_2"]["stats"]
    num_2_stats = _NUMERIC_2.stats["all"]["train"]
    for k in train_stats_num_2.keys():
        assert num_2_stats[k] == train_stats_num_2[k]

def test_comp_stats():
    # Check counts:
    expected_counts = [['Counts for dataset', 'all', 'false', 'true'],
                       ['train', 5, 4, 1], ['test', 5, 4, 1]]
    assert _COMP_STATS._get_counts() == expected_counts
    # Check KS-stats:
    expected_ks_stats = {"numeric_col_1": {'all': 0.0, 'false': 0.0, 'true': 0.0},
                         "numeric_col_2": {'all': 1.0, 'false': 1.0, 'true': 1.0}}
    ks_stats = dict([(f["name"], f["ks-stat"]) for f in _COMP_STATS.features])
    assert ks_stats["numeric_col_1"] == expected_ks_stats["numeric_col_1"]
    assert ks_stats["numeric_col_2"] == expected_ks_stats["numeric_col_2"]

def test_arff_stats_write_report():
    metrics.write_stats_report(_TRAIN_FILE, "train", _STATS_REPORT_FILE)
    _assert_files_equal(_STATS_REPORT_FILE, _CORRECT_STATS_REPORT_FILE)

def test_arff_comp_write_report():
    metrics.write_comp_report(_TRAIN_FILE, "train", _TEST_FILE, "test", _COMP_REPORT_FILE)
    _assert_files_equal(_COMP_REPORT_FILE, _CORRECT_COMP_REPORT_FILE)

def _assert_files_equal(actual_file_name, expected_file_name):
    with open(actual_file_name) as actual_f, open(expected_file_name) as expected_f:
        actual = actual_f.read()
        expected = expected_f.read()
        assert actual == expected


if __name__ == "__main__":
    nose.main()
