from datetime import datetime, timedelta
from app.database import SessionLocal

from app.repository import save_fare_records
import pandas as pd

from scraper.mock_scraper import MockScraper
from scraper.config import (
    ROUTES,
    AIRLINES,
    LEAD_TIMES,
    DATA_FILE,
    ACTIVE_SOURCE
)
from scraper.storage import (
    load_existing_data,
    remove_duplicate_records,
    save_new_records
)


def get_scraper():
    if ACTIVE_SOURCE == "mock":
        return MockScraper()

    raise ValueError(
        f"Unknown source: {ACTIVE_SOURCE}"
    )


def collect_fares():
    scraper = get_scraper()

    records = []

    now = datetime.now()

    collection_date = now.date().isoformat()
    collection_time = now.strftime("%H:%M:%S")

    for route in ROUTES:
        for airline in AIRLINES:
            for lead_time in LEAD_TIMES:

                departure_date = (
                    now.date()
                    + timedelta(days=lead_time)
                ).isoformat()

                try:
                    fare = scraper.fetch_fares(
                        route=route,
                        airline=airline,
                        lead_time=lead_time,
                        departure_date=departure_date
                    )

                    record = {

                        "collection_date": collection_date,

                        "collection_time": collection_time,

                        "date": collection_date,

                        "departure_date": departure_date,

                        "route": route,

                        "airline": airline,

                        "source": ACTIVE_SOURCE,

                        "lead_time": lead_time,

                        "total_fare": fare   

                    }

                    records.append(record)

                    print(
                        f"Collected: {route} | "
                        f"{airline} | "
                        f"T+{lead_time} | "
                        f"₹{fare}"
                    )

                except Exception as error:

                    print(
                        f"Failed: {route} | "
                        f"{airline} | "
                        f"T+{lead_time}"
                    )

                    print(
                        f"Error: {error}"
                    )

    return pd.DataFrame(records)


def run_collection():

    print("\nStarting fare collection...\n")

    new_data = collect_fares()

    existing_data = load_existing_data(
        DATA_FILE
    )

    new_records = remove_duplicate_records(
        new_data,
        existing_data
    )

    saved_count = save_new_records(
        new_records,
        DATA_FILE
    )

    db = SessionLocal()

    try:

        database_result = save_fare_records(
            db,
            new_data.to_dict(
                orient="records"
            )
        )

    finally:

        db.close()

    collected_count = len(new_data)

    duplicate_count = (
        collected_count - len(new_records)
    )

    print(
        "\nCollection complete."
    )

    print(
        f"Total collected: {collected_count}"
    )

    print(
        f"CSV records saved: {saved_count}"
    )

    print(
        f"CSV duplicates skipped: {duplicate_count}"
    )

    print(
        f"Database records inserted: "
        f"{database_result['inserted']}"
    )

    print(
        f"Database duplicates skipped: "
        f"{database_result['duplicates']}"
    )

    return {

        "collected": collected_count,

        "csv_saved": saved_count,

        "csv_duplicates": duplicate_count,

        "database_inserted": (
            database_result["inserted"]
        ),

        "database_duplicates": (
            database_result["duplicates"]
        )

    }

    


if __name__ == "__main__":
    run_collection()