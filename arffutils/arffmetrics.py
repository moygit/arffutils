#!/usr/bin/env python3

"""Module to handle metrics-generation either for a single dataset
or comparing two datasets.

Example
----
# For statistics on a single arff:
$ arffmetrics train.arff stats_report.html

# For comparitive statistics on two arffs:
$ arffmetrics train.arff test.arff comp_report.html

(Note: the comparison function can only do two arffs (not three or
more) because we use the Kolmogoroff-Smirnoff statistic to compare
each pair of distributions.)

"""


import base64
import collections
import io
import os.path
import sys
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.stats import ks_2samp
from statsmodels.distributions.empirical_distribution import ECDF

import IPython.display

import arffutils.arff as arffutils
from arffutils.io import io_handler


# Stats configuration:
ALL_STAT_NAMES = ["Pct missing", "Median", "0.01 %ile", "99.99 %ile",
                  "Min", "Max", "Mean", "Stdev", "Skew", "Kurtosis", "F vs T KS"]
GRAPH_SIZE = 5
QUANTILES = [0.0001, 0.9999]
SUBSETS = ["all", "false", "true"]
TARGET_CLASS_NAME = "TargetClass"
UNWANTED_FEATURES = ["KeyColumn", TARGET_CLASS_NAME]

# HTML formatting:
BEGIN_FEATURE = "\n<!-- BEGIN FEATURE {} -->\n"
END_FEATURE = "\n<!-- END FEATURE {} -->\n"
HLINE = "<hr>"
HTML_ID = "<a id={}></a>\n"
IMAGE = '<img src="data:image/png;base64,{}" alt="graph">'
RETURN_TO_SUMMARY = '<a href="#summary">Back to summary</a>'
TITLE = "<h3>{}</h3>\n"
HTML_HEADER = "<html><head><style>body { font-family: Sans-Serif; }</style></head><body>"
HTML_FOOTER = "</body></html>"

# Misc:
USAGE_STRING = """Usage:
- For single-arff statistics:
  `arffmetrics file.arff report.html`
- For two-arff comparitive statistics:
  `arffmetrics file1.arff file2.arff report.html`
"""


def remove(lis_, items_to_remove):
    """Return a copy of the given list with these items removed if
    it contains them.
    """
    lis_copy = lis_.copy()
    for item in items_to_remove:
        try:
            lis_copy.remove(item)
        except ValueError:
            pass
    return lis_copy


class ListTable(list):
    """Overridden list class which takes a 2-dimensional list of
    the form [["a", "b", "c"], [1,2,3],[4,5,6]], and renders an HTML
    Table in IPython Notebook:
    | a | b | c |   <--  Treated as header row
    | 1 | 2 | 3 |
    | 4 | 5 | 6 |
    Note that the first sub-list is treated as a list of headers.
    """
    DECIMAL = "{0:.2f}"
    # Thanks to Caleb Madrigal
    #   http://calebmadrigal.com/display-list-as-table-in-ipython-notebook/
    # Also see IPython/Jupyter's custom display logic:
    #   http://tinyurl.com/ipython-custom-display

    def get_html(self):
        "Get a formatted HTML representation of this table."
        html = ["<table border=\"1\">"]
        # Header row:
        row = self[0]
        html.append("<tr>")
        for col in row:
            html.append("<th>{0}</th>".format(col))
        html.append("</tr>")
        # Other rows:
        for row in self[1:]:
            html.append("<tr>")
            for col in row:
                if isinstance(col, (float, np.float64)):
                    html.append("<td>" + self.DECIMAL.format(col) + "</td>")
                else:
                    html.append("<td>{0}</td>".format(col))
            html.append("</tr>")
        html.append("</table>")
        return "".join(html)


def list_prepend(item, lis_):
    "Get a copy of lis_ with item inserted at the beginning."
    return [item] + list(lis_)


def plot(axes, x_y_pairs, title, title_color="black", legend_names=None):
    """Given a plt.axes object; a list of pairs, each consisting of an
    x-list and a y-list; a plot title, plot title-color, and legend
    names, make the plot in the given axes object.
    """
    for i, (x, y) in enumerate(x_y_pairs):
        label = legend_names[i] if legend_names is not None else None
        axes.plot(x, y, label=label)
    # Rotate the x-axis labels if they might overlap.
    # Quick and dirty way to detect possible overlap...
    first_x = x_y_pairs[0][0]
    if first_x.size and max(first_x) > 10000:
        for tick in axes.get_xticklabels():
            tick.set_rotation(30)
    axes.set_title(title, color=title_color)
    axes.grid()


def plot_pdf(axes, cols, title, legend_names=None, plot_log_log=False):
    """Given an axes object and a Pandas column of numeric values,
    plot the PDF of the distribution of those values, either directly
    or as a log-log plot.
    """
    pdfs = [col.value_counts(sort=False).sort_index() for col in cols]
    if plot_log_log:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="divide by zero encountered in log")
            x_y_pairs = [(np.log(pdf.index.values), np.log(pdf.values)) for pdf in pdfs]
        plot(axes, x_y_pairs, "log-log PDF ({})".format(title), "red", legend_names)
    else:
        x_y_pairs = [(pdf.index.values, pdf.values) for pdf in pdfs]
        plot(axes, x_y_pairs, "PDF ({})".format(title), "black", legend_names)


def plot_cdf(ax_cdf, cols, title, legend_names=None):
    """Given an axes object and a Pandas column of numeric values,
    plot the CDF of the distribution of those values.
    """
    cdfs = [ECDF(col) for col in cols]
    x_y_pairs = [(cdf.x, cdf.y) for cdf in cdfs]
    plot(ax_cdf, x_y_pairs, "CDF ({})".format(title), "black", legend_names)


def homogenize_x_axes_per_column(axes, row_count, col_num):
    """Each column corresponds to the same type of graph (PDF,
    CDF, etc.) for various sets, e.g. all rows in training set,
    target-class-true rows in test set, etc.  Since they're the same
    type of graph, comparison is much easier if all x-axes in the
    column have the same limits.
    """
    all_l, all_r = zip(*[subplot.get_xlim() for subplot in axes[:, col_num]])
    left = min(all_l)
    right = max(all_r)
    for row_num in range(row_count):
        axes[row_num][col_num].set_xlim(left, right)


def dummy_if_empty(series):
    """Python 3's ECDF and our _get_series_stats choke on empty series,
    so work around those.
    """
    return pd.Series(float("nan")) if series.empty else series


def get_single_arff_counts(arff):
    "Get total/false/true counts for a single arff object."
    def get_one_count(group, key):
        "If there are no false cases or no true cases we want 0, not exception"
        try:
            return group[key]
        except KeyError:
            return 0
    total_count = len(arff.df)
    groups = arff.df.groupby(TARGET_CLASS_NAME).size()
    false_count = get_one_count(groups, False)
    true_count = get_one_count(groups, True)
    return [arff.name, total_count, false_count, true_count]


class NumericFeatureStats(object):
    """Metrics for a single feature, either summarizing a single arff
    or comparing two arffs. The HTML representation of this object
    includes a summary-statistics table and PDF and CDF graphs.
    """

    def __init__(self, feature_name, *arffs):
        """
        feature_name = string name of the feature
        arffs = list of the arffs we're looking at (containing either 1 or 2 arffs)
        """
        if len(arffs) < 1 or len(arffs) > 2:
            raise TypeError("NumericFeatureStats needs either 1 or 2 arff objects")
        self.feature_name = feature_name
        self.arffs = arffs
        self.compare = len(arffs) == 2

        self.data = collections.defaultdict(dict)
        for arff in self.arffs:
            self.data["all"][arff.name] = dummy_if_empty(arff.df[self.feature_name])
            self.data["false"][arff.name] = \
                    dummy_if_empty(arff.df[arff.df[TARGET_CLASS_NAME] == False][self.feature_name])
            self.data["true"][arff.name] = \
                    dummy_if_empty(arff.df[arff.df[TARGET_CLASS_NAME] == True][self.feature_name])

        self.comparison, self.stats = self._calculate_stats()

    def _calculate_stats(self):
        """Calculate basic statistics (min, max, etc.) and also
        KS-statistic if we're comparing datasets. This method does
        this computation for all our arffs.
        """
        arff_names = [arff.name for arff in self.arffs]
        comparison = {}
        if self.compare:
            for subset_name in SUBSETS:
                # Get KS-stat and throw away p-value:
                comparison[subset_name] = ks_2samp(*(self.data[subset_name].values()))[0]
        stats = collections.defaultdict(dict)
        for subset_name in SUBSETS:
            for name in arff_names:
                stats[subset_name][name] = self._get_series_stats(self.data[subset_name][name])
        # Add false-vs-true KS to stats for "all":
        for name in arff_names:
            # Get KS-statistic and throw away p-value:
            ks_stat = ks_2samp(self.data["false"][name], self.data["true"][name])
            stats["all"][name]["F vs T KS"] = ks_stat[0]
            stats["false"][name]["F vs T KS"] = "N/A"
            stats["true"][name]["F vs T KS"] = "N/A"
        return comparison, stats

    @staticmethod
    def _get_series_stats(series):
        """Stats (min, max, etc.) for a single Series.
        Note that "single column" here means this feature in a
        *single* Pandas Series coming from a single arff.
        """
        pct_missing = sum(series.isnull()) * 100.0 / len(series)
        series_stats = {"Pct missing": pct_missing, "Median": series.median(),
                        "0.01 %ile": series.quantile(QUANTILES[0]),
                        "99.99 %ile": series.quantile(QUANTILES[1]),
                        "Min": series.min(), "Max": series.max(),
                        "Mean": series.mean(), "Stdev": series.std(),
                        "Skew": series.skew(), "Kurtosis": series.kurt()}
        return series_stats

    def _get_stats_table(self):
        """Get a table of the basic statistics for this feature in
        all of our arffs.
        """
        names = [arff.name for arff in self.arffs]
        set_names = ["{} ({})".format(name, subset_name.lower())
                     for subset_name in SUBSETS for name in names]
        set_names = list_prepend("SETS", set_names)
        all_stats = [[self.stats[subset_name][name][stat] for stat in ALL_STAT_NAMES]
                     for subset_name in SUBSETS for name in names]
        all_stats = list_prepend(ALL_STAT_NAMES, all_stats)
        return ListTable([list_prepend(set_names[i], row)
                          for i, row in enumerate(all_stats)])

    def _make_graphs(self):
        """Make a detailed graph of the PDF, log-log PDF if necessary,
        and CDF of this feature in each arff.
        """
        set_names = [arff.name for arff in self.arffs]
        rows = len(SUBSETS)
        cols = 2
        fig, axes = plt.subplots(rows, cols, squeeze=False,
                                 figsize=(cols * GRAPH_SIZE, rows * GRAPH_SIZE))
        for pos, subset_name in enumerate(SUBSETS):
            self._graph_one_row(subset_name, set_names, axes[pos],
                                [self.data[subset_name][name] for name in set_names])

        for col in range(cols):
            homogenize_x_axes_per_column(axes, rows, col)
        plt.tight_layout()

        # Convert the image into a base-64-encoded string:
        data = io.BytesIO()
        fig.savefig(data, format="png")
        plt.close(fig)
        return base64.encodebytes(data.getvalue()).decode()

    def _graph_one_row(self, title, set_names, axes, cols):
        """Graph a single row (usually this is all cases of a certain
        feature across all arffs, or all false cases, or all true cases).
        """
        # Use "kurtosis > 100" as a lousy proxy for "is a power-law
        # distribution", in which case we want a log-log plot of the PDF
        plot_log_log = self.stats["all"][set_names[0]]["Kurtosis"] > 100
        plot_pdf(axes[0], cols, title, set_names, plot_log_log)
        plot_cdf(axes[-1], cols, title, set_names)
        axes[-1].legend(loc="lower right")

    def get_html(self):
        "Produce actual HTML for this feature."
        html = HTML_ID.format("feature_" + str(self.feature_name)) + \
            TITLE.format(self.feature_name) + \
            self._get_stats_table().get_html() + \
            HLINE + \
            IMAGE.format(self._make_graphs()) + \
            HLINE + \
            RETURN_TO_SUMMARY
        return html


class DataSetStats(object):
    "Metrics for a single dataset."
    def __init__(self, arff):
        self.arff = arff
        self.features = sorted(remove(self.arff.numeric_features, UNWANTED_FEATURES))
        self.stats = dict([(name, self._get_feature(name)) for name in self.features])

    def _get_feature(self, feature_name):
        "Get stats and html for a single feature."
        feature = NumericFeatureStats(feature_name, self.arff)
        feature_data = {"name": feature_name,
                        "stats": feature.stats["all"][self.arff.name],
                        "html": feature.get_html()}
        del feature
        return feature_data

    def _get_counts(self):
        "Get counts table, including headers."
        cols = ["Counts for dataset"] + SUBSETS
        return [cols, get_single_arff_counts(self.arff)]

    def _get_summary_html(self):
        "Get HTML version of basic stats."
        headers = ["Feature"] + ALL_STAT_NAMES
        summary = list_prepend(headers,
                               [self._make_row(self.stats[feature]) for feature in self.features])
        summary_table = ListTable(summary)
        counts_table = ListTable(self._get_counts())
        html = HTML_ID.format("summary") + \
            TITLE.format("Summary statistics for dataset " + self.arff.name) + \
            counts_table.get_html() + \
            summary_table.get_html() + \
            HLINE
        return html

    @staticmethod
    def _make_row(feature):
        "Make a single row in the summary table."
        feature_link = '<a href="#feature_{0}">{0}</a>'.format(feature["name"])
        feature_stats = [feature["stats"][key] for key in ALL_STAT_NAMES]
        return list_prepend(feature_link, feature_stats)

    def gen_report(self):
        "Generate a list of IPython HTML objects comprising the report."
        report = [IPython.display.HTML(self.stats[feature]["html"]) for feature in self.features]
        report = list_prepend(IPython.display.HTML(self._get_summary_html()), report)
        return report

    def display_report(self):
        "Use the IPython API to display the report."
        report = self.gen_report()
        IPython.display.display(*report)

    def write_report(self, file_name):
        "Write the report to the given file."
        with io_handler(file_name, "w") as report_file:
            report_file.write(HTML_HEADER)
            report_file.write(self._get_summary_html())
            report_file.write("\n\n")
            for feature in self.features:
                report_file.write(self.stats[feature]["html"])
                report_file.write("\n\n")
            report_file.write(HTML_FOOTER)


class DataSetComparison(object):
    "Metrics comparing two datasets."

    def __init__(self, *arffs):
        if len(arffs) != 2:
            raise TypeError("DataSetComparison must get 2 arff objects")
        self.arffs = arffs
        self.features = self._get_features()

    def _get_features(self):
        "Get NumericFeatureStats object for each feature."
        all_features = [set(remove(arff.numeric_features, UNWANTED_FEATURES))
                        for arff in self.arffs]
        common_features_set = all_features[0].intersection(all_features[1])
        common_features = sorted(list(common_features_set))
        return sorted([self._get_one_feature(feature) for feature in common_features],
                      key=lambda f: f["ks-stat"]["all"],
                      reverse=True)

    def _get_one_feature(self, feature_name):
        "Get stats and html for a single feature."
        feature = NumericFeatureStats(feature_name, *self.arffs)
        feature_data = {"name": feature_name,
                        "ks-stat": feature.comparison,
                        "html": feature.get_html()}
        del feature
        return feature_data

    def _get_counts(self):
        "Get counts table, including headers, for all arff objects."
        headers = ["Counts for dataset"] + SUBSETS
        return [headers] + [get_single_arff_counts(arff) for arff in self.arffs]

    def _get_summary_html(self):
        "Get HTML version of summary stats."
        ks_stats = [self._make_row(feature) for feature in self.features]
        headers = ["Feature"] + ["KS stat ({})".format(ext) for ext in SUBSETS]
        ks_stats_table = ListTable([headers] + ks_stats)
        counts_table = ListTable(self._get_counts())
        html = HTML_ID.format("summary") + \
            TITLE.format("Summary statistics for datasets " +
                         ", ".join([arff.name for arff in self.arffs])) + \
            counts_table.get_html() + \
            ks_stats_table.get_html() + \
            HLINE
        return html

    @staticmethod
    def _make_row(feature):
        "Make a single row in the summary table."
        feature_link = '<a href="#feature_{0}">{0}</a>'.format(feature["name"])
        feature_stats = [feature["ks-stat"][subset_name] for subset_name in SUBSETS]
        return list_prepend(feature_link, feature_stats)

    def gen_report(self):
        "Generate a list of IPython HTML objects comprising the report."
        report = [IPython.display.HTML(feature["html"]) for feature in self.features]
        report = list_prepend(IPython.display.HTML(self._get_summary_html()), report)
        return report

    def display_report(self):
        "Use the IPython API to display the report."
        report = self.gen_report()
        IPython.display.display(*report)

    def write_report(self, file_name):
        "Write the report to the given file."
        with io_handler(file_name, "w") as report_file:
            report_file.write(HTML_HEADER)
            report_file.write(self._get_summary_html())
            report_file.write("\n\n")
            for feature in self.features:
                report_file.write(feature["html"])
                report_file.write("\n\n")
            report_file.write(HTML_FOOTER)


def main():
    """Docstring to make pylint happy."""
    main_with_args(sys.argv[1:])


def main_with_args(args):
    """Auxiliary main for easier end-to-end testing."""
    # TODO: clean up args-handling
    if len(args) == 2:
        arff_file, report_file = args
        write_stats_report(arff_file, get_name_stub(arff_file), report_file)
    elif len(args) == 3:
        arff_file_1, arff_file_2, report_file = args
        write_comp_report(arff_file_1, get_name_stub(arff_file_1),
                          arff_file_2, get_name_stub(arff_file_2), report_file)
    else:
        print(USAGE_STRING)
        sys.exit(1)


def write_stats_report(arff_file, arff_name, report_file):
    """Write a report with statistics for a single arff file."""
    arff = arffutils.Arff(arff_file, arff_name)
    stats = DataSetStats(arff)
    stats.write_report(report_file)


def write_comp_report(arff_file_1, arff_name_1, arff_file_2, arff_name_2, report_file):
    """Write a report with statistics comparing the two arff files."""
    arff_1 = arffutils.Arff(arff_file_1, arff_name_1)
    arff_2 = arffutils.Arff(arff_file_2, arff_name_2)
    comp = DataSetComparison(arff_1, arff_2)
    comp.write_report(report_file)


def get_name_stub(full_path):
    """Example: get_name_stub("/home/moy/foo/bar.arff") == "bar". """
    return os.path.basename(full_path).split(".")[0]


if __name__ == "__main__":
    main()
