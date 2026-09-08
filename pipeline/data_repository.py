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
                "collection_date": record.collection_date,
                "collection_time": record.collection_time,
                "date": record.collection_date,
                "departure_date": record.departure_date,
                "route": record.route,
                "airline": record.airline,
                "source": record.source,
                "lead_time": record.lead_time,
                "base_fare": record.base_fare,
                "taxes": record.taxes,
                "fees": record.fees,
                "total_fare": record.total_fare,
                "availability": record.availability
            })

        df = pd.DataFrame(data)

        for col in df.select_dtypes(include=["object", "string"]).columns:
            df[col] = df[col].astype(str).str.strip()

        return df

    finally:

        db.close()


def load_unified_data(
    sample_file="data/sample_fares.csv"
):

    df = pd.DataFrame()
    data_mode = "live"

    try:
        df = load_database_data()
    except Exception as err:
        print(f"Warning: Failed to load database data: {err}")
        df = pd.DataFrame()

    # Filter out hand-seeded fake rows from sample_fares.csv only.
    # 'Airline' and 'Mock' (capital M) = fake CSV seeds → exclude.
    # 'mock' (lowercase) = live scheduler output via MockScraper → keep.
    # 'google_flights' = real scraper → keep.
    if not df.empty and "source" in df.columns:
        fake_sources = ["Airline", "Mock", "test"]
        df = df[~df["source"].astype(str).str.strip().isin(fake_sources)]

    # Fall back to sample_fares.csv only if live real data is empty
    if df.empty:
        data_mode = "demo"
        if os.path.exists(sample_file):
            sample_df = pd.read_csv(sample_file)
            for col in sample_df.select_dtypes(include=["object", "string"]).columns:
                sample_df[col] = sample_df[col].astype(str).str.strip()
            df = sample_df
        else:
            raise FileNotFoundError("No fare data available (live DB empty and sample file missing).")

    df.attrs["data_mode"] = data_mode
    df.data_mode = data_mode
    return df