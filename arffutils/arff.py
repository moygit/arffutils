#!/usr/bin/env python3

"""Stub arff class.

Example usage:

from arffutils.arff import Arff
a = Arff("training.arff", "train")  # optional tag "train"

# Get name
a.name

# Get list of numeric feature names:
a.numeric_features

# Get dictionary of nominal feature names and possible values:
a.nominal_features

# Get arff metadata and data:
data, metadata = a.data, a.metadata

# Get data as a Pandas dataframe:
df = a.df
"""


import pandas as pd
from scipy.io import arff as s_arff

TARGET_CLASS_NAME = "TargetClass"


class Arff:
    """Very basic features for now."""
    def __init__(self, arff_object, name="arff", target_class_name=TARGET_CLASS_NAME):
        self.name = name
        self.target_class_name = target_class_name
        self.data, self.metadata = s_arff.loadarff(arff_object)
        self.df = pd.DataFrame({name: self.data[name]
                                for name in self.metadata.names()})
        if self.target_class_name in self.metadata.names():
            self.df[self.target_class_name] = (self.df[self.target_class_name] == b'true')
        self.nominal_features = self._get_nominal_features()
        self.numeric_features = self._get_numeric_features()

    def _get_nominal_features(self):
        """
        Returns a dictionary with the nominal attribute names as keys,
        and a list of attribute values as the value.
        """
        features = {}
        for name, ftype in zip(self.metadata.names(), self.metadata.types()):
            if ftype != 'nominal':
                continue
            features[name] = list(self.metadata[name][1])
            features[name].append('?')
        return features

    def _get_numeric_features(self):
        """
        Returns a list of numeric attributes.
        """
        features = []
        for name, ftype in zip(self.metadata.names(), self.metadata.types()):
            if ftype != 'numeric':
                continue
            features.append(name)
        return features
