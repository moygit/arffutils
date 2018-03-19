#!/usr/bin/env python3

# pylint: disable=missing-docstring
# not necessary here: we know test_arff tests arff.py, etc.

import io
import nose

import arffutils.arff as arff


TARGET_CLASS_NAME = "tclass"

class TestArff(object):
    def setUp(self):
        arff_str = "@attribute numeric_col numeric" + "\n" + \
                   "@attribute nominal_col {A,B}" + "\n" + \
                   "@attribute {} {{false,true}}".format(TARGET_CLASS_NAME) + "\n" + \
                   "@data" + "\n" + \
                   "1.0,A,false" + "\n" + \
                   "2.0,B,true"
        arff_str_io = io.StringIO(arff_str)
        self.arff = arff.Arff(arff_str_io, "arff_test", TARGET_CLASS_NAME)

    def test_name(self):
        assert self.arff.name == "arff_test"

    def test_numerical_features(self):
        assert self.arff.numeric_features == ["numeric_col"]

    def test_nominal_features(self):
        assert set(self.arff.nominal_features.keys()) == set(["nominal_col", TARGET_CLASS_NAME])

    def test_dataframe(self):
        assert len(self.arff.df) == 2
        assert self.arff.df["nominal_col"][0] == b'A'
        assert self.arff.df["numeric_col"][0] == 1
        assert not self.arff.df[TARGET_CLASS_NAME][0]
        assert self.arff.df[TARGET_CLASS_NAME][1]

    def test_arff(self):
        assert len(self.arff.data) == 2
        assert self.arff.data[0][0] == 1.0
        assert self.arff.data[0][1] == b'A'

if __name__ == "__main__":
    nose.main()
