from app.database import SessionLocal

from app.models import FareRecord


def test_database():

    db = SessionLocal()

    try:

        records = db.query(
            FareRecord
        ).all()

        print(
            f"\nTotal database records: "
            f"{len(records)}"
        )

        if records:

            print("\nFirst record:\n")

            first = records[0]

            print(
                f"Collection Date: "
                f"{first.collection_date}"
            )

            print(
                f"Departure Date: "
                f"{first.departure_date}"
            )

            print(
                f"Route: "
                f"{first.route}"
            )

            print(
                f"Airline: "
                f"{first.airline}"
            )

            print(
                f"Lead Time: "
                f"T+{first.lead_time}"
            )

            print(
                f"Fare: ₹{first.total_fare}"
            )

    finally:

        db.close()


if __name__ == "__main__":

    test_database()