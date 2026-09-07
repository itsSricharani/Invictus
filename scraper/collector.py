import time
from datetime import datetime, timedelta

import pandas as pd

from scraper.mock_scraper import MockScraper
from scraper.google_flights_scraper import fetch_route_fares

from scraper.config import (
    ROUTES,
    AIRLINES,
    LEAD_TIMES,
    DATA_FILE,
    ACTIVE_SOURCE,
    ROUTE_AIRPORTS
)

from scraper.storage import (
    load_existing_data,
    remove_duplicate_records,
    save_new_records
)


def _build_record(
    collection_date,
    collection_time,
    departure_date,
    route,
    airline,
    lead_time,
    result
):
    return {
        "collection_date": collection_date,
        "collection_time": collection_time,
        "date": collection_date,
        "departure_date": departure_date,
        "route": route,
        "airline": airline,
        "source": ACTIVE_SOURCE,
        "lead_time": lead_time,
        "base_fare": result.get("base_fare"),
        "taxes": result.get("taxes"),
        "fees": result.get("fees"),
        "total_fare": result["total_fare"],
        "availability": result.get("availability", "available")
    }


def _collect_mock(collection_date, collection_time, now):
    scraper = MockScraper()
    records = []

    for route in ROUTES:
        for airline in AIRLINES:
            for lead_time in LEAD_TIMES:
                departure_date = (
                    now.date() + timedelta(days=lead_time)
                ).isoformat()

                try:
                    result = scraper.fetch_fares(
                        route=route,
                        airline=airline,
                        lead_time=lead_time,
                        departure_date=departure_date
                    )

                    record = _build_record(
                        collection_date, collection_time, departure_date,
                        route, airline, lead_time, result
                    )

                    records.append(record)

                    print(
                        f"Collected: {route} | {airline} | "
                        f"T+{lead_time} | Rs {record['total_fare']}"
                    )

                except Exception as error:
                    print(f"Failed: {route} | {airline} | T+{lead_time}")
                    print(f"Error: {error}")

    return records


def _collect_google_flights(collection_date, collection_time, now):
    records = []

    for route in ROUTES:
        airports = ROUTE_AIRPORTS[route]
        origin = airports["origin"]
        destination = airports["destination"]

        for lead_time in LEAD_TIMES:
            departure_date = (
                now.date() + timedelta(days=lead_time)
            ).isoformat()

            try:
                fares_by_airline = fetch_route_fares(
                    origin, destination, departure_date
                )
            except Exception as error:
                print(f"Failed: {route} | T+{lead_time}")
                print(f"Error: {error}")
                continue

            for airline in AIRLINES:
                fare = fares_by_airline.get(airline)

                if fare is None:
                    print(
                        f"No {airline} flights found: "
                        f"{route} | T+{lead_time}"
                    )
                    continue

                result = {
                    "base_fare": None,
                    "taxes": None,
                    "fees": None,
                    "total_fare": fare,
                    "availability": "available"
                }

                record = _build_record(
                    collection_date, collection_time, departure_date,
                    route, airline, lead_time, result
                )

                records.append(record)

                print(
                    f"Collected: {route} | {airline} | "
                    f"T+{lead_time} | Rs {fare}"
                )

            # Be polite to Google Flights between route/date queries.
            time.sleep(1)

    return records


def collect_fares():
    now = datetime.now()

    collection_date = now.date().isoformat()
    collection_time = now.strftime("%H:%M:%S")

    if ACTIVE_SOURCE == "mock":
        records = _collect_mock(collection_date, collection_time, now)

    elif ACTIVE_SOURCE == "google_flights":
        records = _collect_google_flights(
            collection_date, collection_time, now
        )

    else:
        raise ValueError(f"Unknown source: {ACTIVE_SOURCE}")

    return pd.DataFrame(records)


def run_collection():

    print("\nStarting fare collection...\n")

    new_data = collect_fares()

    existing_data = load_existing_data(DATA_FILE)

    new_records = remove_duplicate_records(
        new_data,
        existing_data
    )

    saved_count = save_new_records(
        new_records,
        DATA_FILE
    )

    try:
        from app.database import SessionLocal
        from app.repository import save_fare_records
        db = SessionLocal()
        try:
            records_dict = new_data.to_dict(orient="records")
            save_fare_records(db, records_dict)
        finally:
            db.close()
    except Exception as error:
        print(f"Database save warning: {error}")

    collected_count = len(new_data)

    duplicate_count = (
        collected_count
        - len(new_records)
    )

    print("\nCollection complete.")
    print(f"Total collected: {collected_count}")
    print(f"New records saved: {saved_count}")
    print(f"Duplicates skipped: {duplicate_count}")

    return {
        "collected": collected_count,
        "saved": saved_count,
        "duplicates": duplicate_count
    }


if __name__ == "__main__":
    run_collection()