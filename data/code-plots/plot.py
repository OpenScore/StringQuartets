#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NAME
===============================
Plot (plot.py)


BY
===============================
Mark Gotham


LICENCE:
===============================
Creative Commons Attribution-ShareAlike 4.0 International License
https://creativecommons.org/licenses/by-sa/4.0/


ABOUT:
===============================
Basic scripts for extracting and plotting summary information about the corpus.

"""

from collections import Counter
import matplotlib.pyplot as plt
from pathlib import Path
import yaml

THIS_FOLDER = Path(__file__).parent
DATA_FOLDER = THIS_FOLDER.parent
REPO_FOLDER = DATA_FOLDER.parent


# ------------------------------------------------------------------------------

# Shared

def get_info(
        what: str = "composers",
        path_to_data: str | Path = DATA_FOLDER
):
    """
    Read in one of the yaml files provided in the repo's `Data/` directory
    (e.g., `Data/composers.yaml`)
    """

    if what not in ["composers", "corpus", "sets", "scores"]:
        raise ValueError("Argument `what` invalid: must be one of validTypes")

    path_to_data = path_to_data / f"{what}.yaml"

    with open(path_to_data) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    return data


# ------------------------------------------------------------------------------

# Composers

def composer_dates(
        plot: bool = True,
        also_plot_active: bool = True,
        start: int = 1730,
        stop: int = 1950,
        step: int = 5,
        write_path: str | Path = THIS_FOLDER,
        write_name: str = "composer_dates",
        write_format: str = "pdf",
):
    """
    Get birth and death dates for all composers in the corpus and
    (optionally) plot the number of corpus composers that are alive in a given year.

    :param bool plot: Plot or simply return the data.
    :param bool also_plot_active: Include an approximation of active years by removing the first 20 years of each entry.
    :param int start: The first year to be counted
    :param int stop: The first year that will _not_ be counted (the last + 1)
    :param int step: The size of sampling increment
    :param write_path: The path of the directory to write to
    :param str write_name: The name of the file to write (default, "composer_dates").
    :param str write_format: The format of the file to write (default, "pdf").

    """

    composers = get_info()  # what="composers"

    bin_values = range(start, stop + 1, step)  # here include 'stop' in range for use with axis labels, etc.
    # Cf https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.hist.html

    adjusted_bin_values = [*range(start, stop, step)]  # exclude 'stop'
    adjusted_bin_values.append(stop - 1)  # include one less than 'stop'
    # NB final bin is one unit (i.e., year) wider than the other bins

    years_alive = []
    years_active = []

    for composer in composers.values():
        b, d = composer["born"], composer["died"]
        if not b and not d:
            continue # ignore composers with incomplete data
        years_alive += range(b, d + 1)
        if also_plot_active:
            years_active += range(b + 20, d + 1)

    if also_plot_active:
        what_to_plot = [years_alive, years_active]
        weights = [[1.0/step] * len(x) for x in what_to_plot]
        plot_lab = ["Alive", "Active (approx.)"]
        y_lab = "# composers"
    else:
        what_to_plot = years_alive
        weights = [1.0/step] * len(years_alive)
        plot_lab = ""
        y_lab = "Number of corpus composers alive"

    if plot:
        plt.figure(figsize=(10, 6))
        plt.hist(what_to_plot,
                 bins=adjusted_bin_values,
                 #width=step*0.45,
                 weights=weights,
                 alpha=0.5,
                 align="left",
                 label=plot_lab)
        if also_plot_active:
            plt.legend()

        bot, top = plt.ylim()
        ylim = round(top)

        d = 50 # show dashes on multiples of this many years
        plt.vlines([d * x for x in range(start//d + 1, stop//d)], 0, ylim, linestyles="dashed")
        if step == 1:
            plt.xlabel(f"Year", fontsize=14, family="serif")
        else:
            plt.xlabel(f"Year ({step}-year average)", fontsize=14, family="serif")
        plt.ylabel(y_lab, fontsize=14, family="serif")
        plt.yticks([x for x in range(0, ylim, 5)])
        plt.yticks([x for x in range(0, ylim)], minor=True)
        plt.xticks(bin_values[0::2], rotation=90)
        plt.xticks(bin_values, minor=True)
        plt.tight_layout()
        plt.savefig(
            write_path / f"{write_name}.{write_format}",
            facecolor="w", edgecolor="w", format=write_format
        )
    else:
        return what_to_plot


# ------------------------------------------------------------------------------

# Counts: Scores and Nationalities

def scores_per_composer(
        how_many: int = 7,  # those with more than 2
        write_path: str | Path = THIS_FOLDER,
        write_name: str = "composer_scores",
        write_format: str = "pdf",
) -> None:
    """Plots the number of scores per composer for those with the most."""

    scores = get_info(what="scores")
    composers = [score["path"].split("/")[0] for score in scores.values()]
    most_common = Counter(composers).most_common(how_many)
    plot_counts("Scores", most_common, write_path, write_name, write_format)


def composer_nationalities(
        how_many: int = 13,  # all
        write_path: str | Path = THIS_FOLDER,
        write_name: str = "composer_nationalities",
        write_format: str = "pdf",
) -> None:
    """Plots the most common nationalities in the corpus."""

    composers = get_info(what="composers")
    nationalities = [comp["desc"].split(" ")[0] for comp in composers.values()]
    most_common = Counter(nationalities).most_common(how_many)
    plot_counts("Nationalities", most_common, write_path, write_name, write_format)


def plot_counts(
        what: str,
        count: list | tuple,
        write_path: str | Path = THIS_FOLDER,
        write_name: str = "plot",
        write_format: str = "pdf"
) -> None:
    """Shared function for plotting counts of scores and nationalities"""

    plt.figure(figsize=(15, 10))
    plt.barh(
        range(len(count)),
        [x[1] for x in count],
        tick_label=["  " + x[0].replace("_", " ") for x in count]
    )
    plt.xlabel(f"{what} in the corpus", fontsize=14, family="serif")
    # plt.ylabel(what, fontsize=14, family="serif")
    plt.tight_layout()
    plt.savefig(
        write_path / f"{write_name}.{write_format}",
        facecolor="w", edgecolor="w", format=write_format
    )


# ------------------------------------------------------------------------------

def run_all():
    composer_dates()
    scores_per_composer()
    composer_nationalities()


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    run_all()
