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

    sample_file="data/sample_fares.csv"

):

    datasets = []

    # Historical sample data

    if os.path.exists(sample_file):

        sample_df = pd.read_csv(sample_file)

        datasets.append(sample_df)

    # Live collected data from SQLite

    database_df = load_database_data()

    if not database_df.empty:

        datasets.append(database_df)

    if not datasets:

        raise FileNotFoundError(

            "No fare data sources found."

        )

    unified_df = pd.concat(

        datasets,

        ignore_index=True

    )

    return unified_df