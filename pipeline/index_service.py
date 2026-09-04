import pandas as pd

from pipeline.data_repository import (
    load_unified_data
)

from pipeline.cleaner import (
    clean_fares
)

from pipeline.validator import (
    validate_required_columns
)

from pipeline.index_calculator import (
    calculate_historical_index,
    calculate_percentage_change
)


def get_index_data():

    df = load_unified_data()

    validate_required_columns(df)

    df = clean_fares(df)

    weights_df = pd.read_csv(
        "data/route_weights.csv"
    )

    historical = calculate_historical_index(
        df,
        weights_df
    )

    if not historical:
        return {
            "index": 100.0,
            "previous_index": None,
            "percentage_change": 0.0,
            "date": None
        }

    dates = sorted(
        historical.keys()
    )

    current_date = dates[-1]

    current_index = historical[
        current_date
    ]

    previous_index = None

    if len(dates) >= 2:

        previous_date = dates[-2]

        previous_index = historical[
            previous_date
        ]

    percentage_change = 0.0

    if previous_index is not None:

        percentage_change = (
            calculate_percentage_change(
                previous_index,
                current_index
            )
        )

    return {
        "index": current_index,
        "previous_index": previous_index,
        "percentage_change": round(
            percentage_change,
            2
        ),
        "date": current_date
    }