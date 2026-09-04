from scraper.collector import collect_fares

from app.database import SessionLocal
from app.repository import save_fare_records


def collect_fares_and_store():

    db = SessionLocal()

    try:
        data = collect_fares()

        records = data.to_dict(
            orient="records"
        )

        result = save_fare_records(
            db,
            records
        )

        return {
            "status": "success",
            "collected": len(records),
            "inserted": result["inserted"],
            "duplicates": result["duplicates"]
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()