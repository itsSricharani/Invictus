import pandas as pd


REQUIRED_COLUMNS = [
    "date",
    "departure_date",
    "route",
    "airline",
    "source",
    "lead_time",
    "total_fare"
]


def validate_required_columns(df):

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing required columns: "
            f"{missing_columns}"
        )

    return True


def validate_price_range(
    df,
    minimum=500,
    maximum=100000
):

    invalid_prices = df[
        (df["total_fare"] < minimum)
        |
        (df["total_fare"] > maximum)
    ]

    return invalid_prices


def validate_weights(weights_df):

    total_weight = (
        weights_df["weight"].sum()
    )

    if abs(total_weight - 1.0) > 0.001:

        raise ValueError(
            "Route weights must sum to 1. "
            f"Current sum: {total_weight}"
        )

    return True