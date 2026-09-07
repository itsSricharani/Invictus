import os

import pandas as pd


REQUIRED_COLUMNS = [
    "collection_date",
    "collection_time",
    "date",
    "departure_date",
    "route",
    "airline",
    "source",
    "lead_time",
    "base_fare",
    "taxes",
    "fees",
    "total_fare",
    "availability"
]


def initialize_storage(file_path):

    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:

        df = pd.DataFrame(columns=REQUIRED_COLUMNS)

        df.to_csv(

            file_path,

            index=False,

            lineterminator="\n"

        )


def load_existing_data(file_path):

    initialize_storage(file_path)

    try:

        df = pd.read_csv(file_path)
        df.columns = [c.strip() for c in df.columns]

        if "departure_date" not in df.columns:

            df["departure_date"] = pd.NA

        return df

    except pd.errors.EmptyDataError:

        return pd.DataFrame(

            columns=REQUIRED_COLUMNS

        )


def remove_duplicate_records(new_df, existing_df):

    if existing_df.empty:
        return new_df.copy()

    duplicate_columns = [
        "collection_date",
        "collection_time",
        "departure_date",
        "route",
        "airline",
        "source",
        "lead_time"
    ]

    existing_keys = set(
        existing_df[
            duplicate_columns
        ]
        .astype(str)
        .apply(tuple, axis=1)
    )

    new_keys = (
        new_df[
            duplicate_columns
        ]
        .astype(str)
        .apply(tuple, axis=1)
    )

    mask = ~new_keys.isin(existing_keys)

    return new_df[mask].copy()


def save_new_records(new_df, file_path):

    initialize_storage(file_path)

    if new_df.empty:

        print("No new records to save.")

        return 0

    existing_df = pd.read_csv(file_path)

    if "departure_date" not in existing_df.columns:

        existing_df["departure_date"] = pd.NA

        existing_df = existing_df.reindex(
            columns=REQUIRED_COLUMNS
        )

        existing_df.to_csv(

            file_path,

            index=False,

            lineterminator="\n"

        )

    new_df = new_df.reindex(
        columns=REQUIRED_COLUMNS
    )

    new_df.to_csv(

        file_path,

        mode="a",

        header=False,

        index=False,

        lineterminator="\n"

    )

    print(

        f"Saved {len(new_df)} new records."

    )

    return len(new_df)