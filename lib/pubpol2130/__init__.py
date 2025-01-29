from collections import defaultdict
from itertools import chain

import pandas as pd
import requests
import census
from us import states

__all__ = ["condensed_populations"]

RACE_LABELS = {
    "black": "Black or African American",
    "asian": "Asian",
    "nhpi": "Native Hawaiian and Other Pacific Islander",
    "amin": "American Indian and Alaska Native",
    "other": "Some Other Race",
    "white": "White",
}

CONDENSED_HIERARCHY = (
    ("black", lambda races: "black" in races),
    ("aapi", lambda races: "asian" in races or "nhpi" in races),
    ("amin", lambda races: "amin" in races),
    ("other", lambda races: "other" in races),
    ("white", lambda races: "white" in races),
)


def condensed_populations(
    census: census.Census, in_query: str, for_query: str, year: int = 2020
) -> pd.DataFrame:
    variables_response = requests.get(
        "https://api.census.gov/data/2020/dec/pl/variables.json"
    )
    variables_response.raise_for_status()
    variables = variables_response.json()["variables"]

    column_groups = defaultdict(list)
    column_groups["total"] = ["P1_001N"]
    column_groups["non_hispanic"] = ["P2_003N"]

    group_labels = {
        key: set(race for race, label in RACE_LABELS.items() if label in props["label"])
        for key, props in variables.items()
        if (props["group"] == "P2" and "Not Hispanic or Latino" in props["label"])
    }
    columns = {}
    for col, races in group_labels.items():
        if races:
            columns[tuple(sorted(races))] = col

    for contents, column in columns.items():
        for label, label_fn in CONDENSED_HIERARCHY:
            if label_fn(contents):
                column_groups[label].append(column)
                break

    column_union = list(chain(*column_groups.values()))

    populations = census.pl.get(
        column_union,
        geo={"for": for_query, "in": in_query},
        year=year,
    )
    populations_df = pd.DataFrame(populations)

    for group, group_columns in column_groups.items():
        populations_df[group] = populations_df[group_columns].sum(axis=1)
    populations_df["hispanic"] = (
        populations_df["total"] - populations_df["non_hispanic"]
    )
    populations_df = populations_df.drop(columns=[*column_union, "non_hispanic"]).copy()

    return populations_df
