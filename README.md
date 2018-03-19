The utilities are `arffmerge`, `arffselect`, `arffsplit`, and
`arffmetrics`. You can find brief examples in the module docstrings
and more examples in the tests.


### arffmerge

Read in a main csv (could be an arff) and an additional
csv (could be an arff), insert columns from the additional csv into
the main csv (joining on a key column), and write an output csv (or
arff). For example usage please see
[the arffmerge docstring](https://github.com/moygit/arffutils/blob/master/arffutils/arffmerge.py).


### arffselect

Select columns from a csv (could be an arff), either by
column-position or (for an arff) by column-name. For example usage
please see
[the arffselect docstring](https://github.com/moygit/arffutils/blob/master/arffutils/arffselect.py).


### arffsplit

Read in a main csv (could be an arff) and N possibly-overlapping sets
of keys, and split the rows of the csv into N csvs (or arffs)
depending on which set(s) each row's key is in. For example usage
please see
[the arffsplit docstring](https://github.com/moygit/arffutils/blob/master/arffutils/arffsplit.py).


### arffmetrics

Generate statistics on the numerical features either for a single arff
or comparing two arffs. The main use of the latter is to ensure that
features in, say, a training arff and a test arff have similar
distributions. We use the Kolmogoroff-Smirnoff statistic to sort
features by mismatch: the more different the training set data and the
test set data are for a feature, the higher it ranks.  For a bit of
detail please see
[the arffmetrics docstring](https://github.com/moygit/arffutils/blob/master/arffutils/arffmetrics.py).

