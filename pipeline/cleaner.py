import pandas as pd
from pipeline.validator import validate_required_columns

def load_and_clean_data(file_path):
    df = pd.read_csv(file_path)

    validate_required_columns(df)

    initial_count = len(df)

    # Remove rows with missing important values
    df = df.dropna(
        subset=[
            "date",
            "route",
            "airline",
            "source",
            "lead_time",
            "total_fare"
        ]
    )

    # Convert columns to correct types
    df["total_fare"] = pd.to_numeric(
        df["total_fare"],
        errors="coerce"
    )

    df["lead_time"] = pd.to_numeric(
        df["lead_time"],
        errors="coerce"
    )

    # Remove invalid values
    df = df[
        (df["total_fare"] > 0) &
        (df["lead_time"] >= 0)
    ]

    # Remove duplicates
    df = df.drop_duplicates()

    # Remove price outliers
    df = remove_outliers(df)

    final_count = len(df)

    print(f"Initial records: {initial_count}")
    print(f"Valid records: {final_count}")
    print(f"Removed records: {initial_count - final_count}")

    return df


def remove_outliers(df):
    cleaned_groups = []

    # Detect outliers within comparable groups
    group_columns = ["route", "lead_time"]

    for _, group in df.groupby(group_columns):
        if len(group) < 4:
            cleaned_groups.append(group)
            continue

        q1 = group["total_fare"].quantile(0.25)
        q3 = group["total_fare"].quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        group = group[
            (group["total_fare"] >= lower_bound) &
            (group["total_fare"] <= upper_bound)
        ]

        cleaned_groups.append(group)

    return pd.concat(cleaned_groups, ignore_index=True)



def clean_fares(df):

    if df.empty:
        return df.copy()

    cleaned = df.copy()

    if "availability" in cleaned.columns:
        cleaned = cleaned[
            cleaned["availability"]
            == "available"
        ]

    cleaned = cleaned[
        cleaned["total_fare"].notna()
    ]

    cleaned = cleaned[
        cleaned["total_fare"] > 0
    ]

    cleaned = cleaned[
        cleaned["total_fare"] <= 100000
    ]

    preferred_dedup_cols = [
        "collection_date",
        "collection_time",
        "departure_date",
        "route",
        "airline",
        "source",
        "lead_time"
    ]
    dedup_subset = [
        col for col in preferred_dedup_cols
        if col in cleaned.columns
    ]
    cleaned = cleaned.drop_duplicates(
        subset=dedup_subset if dedup_subset else None
    )

    return cleaned.reset_index(
        drop=True
    )