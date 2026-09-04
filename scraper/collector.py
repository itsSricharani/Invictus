from datetime import datetime, timedelta

import pandas as pd

from scraper.mock_scraper import MockScraper
from scraper.indigo_scraper import IndigoScraper

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

    if ACTIVE_SOURCE == "indigo":
        return IndigoScraper(headless=True)

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

            # The current IndigoScraper only supports IndiGo.
            if (
                ACTIVE_SOURCE == "indigo"
                and airline != "IndiGo"
            ):
                continue

            for lead_time in LEAD_TIMES:

                departure_date = (
                    now.date()
                    + timedelta(days=lead_time)
                ).isoformat()

                try:

                    result = scraper.fetch_fares(
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
                        "base_fare": result.get(
                            "base_fare"
                        ),
                        "taxes": result.get(
                            "taxes"
                        ),
                        "fees": result.get(
                            "fees"
                        ),
                        "total_fare": result[
                            "total_fare"
                        ],
                        "availability": result.get(
                            "availability",
                            "available"
                        )
                    }

                    records.append(record)

                    print(
                        f"Collected: "
                        f"{route} | "
                        f"{airline} | "
                        f"T+{lead_time} | "
                        f"₹{record['total_fare']}"
                    )

                except Exception as error:

                    print(
                        f"Failed: "
                        f"{route} | "
                        f"{airline} | "
                        f"T+{lead_time}"
                    )

                    print(
                        f"Error: {error}"
                    )

    return pd.DataFrame(records)


def run_collection():

    print(
        "\nStarting fare collection...\n"
    )

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

    collected_count = len(new_data)

    duplicate_count = (
        collected_count
        - len(new_records)
    )

    print(
        "\nCollection complete."
    )

    print(
        f"Total collected: {collected_count}"
    )

    print(
        f"New records saved: {saved_count}"
    )

    print(
        f"Duplicates skipped: {duplicate_count}"
    )

    return {
        "collected": collected_count,
        "saved": saved_count,
        "duplicates": duplicate_count
    }


if __name__ == "__main__":
    run_collection()