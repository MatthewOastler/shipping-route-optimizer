

# economics/vessel_profiles.py

import pandas as pd


def load_vessels(
    vessel_file="data/vessels.csv"
):
    """
    Load vessel database.
    """

    return pd.read_csv(
        vessel_file
    )


def get_vessel_profile(
    vessel_name,
    vessel_file="data/vessels.csv"
):
    """
    Return vessel profile as dictionary.
    """

    vessels = pd.read_csv(
        vessel_file
    )

    vessel = vessels[
        vessels["vessel_name"]
        ==
        vessel_name
    ]

    if vessel.empty:

        raise ValueError(
            f"Vessel not found: {vessel_name}"
        )

    return vessel.iloc[0].to_dict()


def calculate_capacity_utilization(
    cargo_tonnes,
    cargo_capacity_tonnes
):
    """
    Cargo utilization %.
    """

    if cargo_capacity_tonnes <= 0:

        return 0

    return round(

        (
            float(cargo_tonnes)
            /
            float(cargo_capacity_tonnes)
        )
        *
        100,

        2

    )


if __name__ == "__main__":

    profile = get_vessel_profile(
        "Pacific Bulk"
    )

    print(profile)