import os

import pandas as pd

from app.database import SessionLocal

from app.models import FareRecord


def load_database_data():

    db = SessionLocal()

    try:

        records = (

            db.query(FareRecord)

            .order_by(
                FareRecord.collection_date,
                FareRecord.collection_time
            )

            .all()

        )

        if not records:

            return pd.DataFrame()

        data = []

        for record in records:

            data.append({

                "date": record.collection_date,

                "route": record.route,

                "airline": record.airline,

                "source": record.source,

                "lead_time": record.lead_time,

                "total_fare": record.total_fare

            })

        return pd.DataFrame(data)

    finally:

        db.close()


def load_unified_data(
    sample_file="data/sample_fares.csv",
    raw_file="data/raw_fares.csv"
):

    datasets = []

    if os.path.exists(sample_file):

        sample_df = pd.read_csv(
            sample_file
        )

        datasets.append(
            sample_df
        )

    if os.path.exists(raw_file):

        raw_df = pd.read_csv(
            raw_file
        )

        if not raw_df.empty:

            required_columns = [
                "date",
                "departure_date",
                "route",
                "airline",
                "source",
                "lead_time",
                "total_fare"
            ]

            missing = [
                column
                for column in required_columns
                if column not in raw_df.columns
            ]

            if not missing:

                raw_df = raw_df[
                    required_columns
                ]

                datasets.append(
                    raw_df
                )

    if not datasets:

        raise FileNotFoundError(
            "No fare data files found."
        )

    unified_df = pd.concat(
        datasets,
        ignore_index=True
    )

    return unified_df