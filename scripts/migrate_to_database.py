import pandas as pd

from sqlalchemy.orm import Session

from app.database import SessionLocal

from app.models import FareRecord


CSV_FILE = "data/raw_fares.csv"


def migrate_data():

    print("\nStarting CSV to SQLite migration...\n")

    df = pd.read_csv(CSV_FILE)

    print(f"Total records found: {len(df)}")

    required_columns = [

        "collection_date",

        "collection_time",

        "departure_date",

        "route",

        "airline",

        "source",

        "lead_time",

        "total_fare"

    ]

    missing_columns = [

        column

        for column in required_columns

        if column not in df.columns

    ]

    if missing_columns:

        raise ValueError(

            f"Missing columns: {missing_columns}"

        )

    df = df.dropna(

        subset=[

            "departure_date",

            "total_fare"

        ]

    )

    print(

        f"Valid records for migration: {len(df)}"

    )

    db: Session = SessionLocal()

    inserted_count = 0

    skipped_count = 0

    try:

        for _, row in df.iterrows():

            existing_record = (

                db.query(FareRecord)

                .filter(

                    FareRecord.collection_date
                    == str(row["collection_date"]),

                    FareRecord.collection_time
                    == str(row["collection_time"]),

                    FareRecord.route
                    == str(row["route"]),

                    FareRecord.airline
                    == str(row["airline"]),

                    FareRecord.source
                    == str(row["source"]),

                    FareRecord.lead_time
                    == int(row["lead_time"])

                )

                .first()

            )

            if existing_record:

                skipped_count += 1

                continue

            record = FareRecord(

                collection_date=str(
                    row["collection_date"]
                ),

                collection_time=str(
                    row["collection_time"]
                ),

                departure_date=str(
                    row["departure_date"]
                ),

                route=str(
                    row["route"]
                ),

                airline=str(
                    row["airline"]
                ),

                source=str(
                    row["source"]
                ),

                lead_time=int(
                    row["lead_time"]
                ),

                total_fare=float(
                    row["total_fare"]
                )

            )

            db.add(record)

            inserted_count += 1

        db.commit()

        print(f"Records inserted: {inserted_count}")

        print(f"Duplicates skipped: {skipped_count}")

        print("\nMigration completed successfully.")

    except Exception as error:

        db.rollback()

        print(f"\nMigration failed: {error}")

        raise

    finally:

        db.close()


if __name__ == "__main__":

    migrate_data()