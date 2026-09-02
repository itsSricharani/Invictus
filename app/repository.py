from sqlalchemy.orm import Session

from app.models import FareRecord


def record_exists(
    db: Session,
    collection_date,
    collection_time,
    route,
    airline,
    source,
    lead_time
):

    existing_record = (

        db.query(FareRecord)

        .filter(

            FareRecord.collection_date
            == str(collection_date),

            FareRecord.collection_time
            == str(collection_time),

            FareRecord.route
            == str(route),

            FareRecord.airline
            == str(airline),

            FareRecord.source
            == str(source),

            FareRecord.lead_time
            == int(lead_time)

        )

        .first()

    )

    return existing_record is not None


def save_fare_records(
    db: Session,
    records
):

    inserted_count = 0

    skipped_count = 0

    for record in records:

        exists = record_exists(

            db,

            record["collection_date"],

            record["collection_time"],

            record["route"],

            record["airline"],

            record["source"],

            record["lead_time"]

        )

        if exists:

            skipped_count += 1

            continue

        fare_record = FareRecord(

            collection_date=str(
                record["collection_date"]
            ),

            collection_time=str(
                record["collection_time"]
            ),

            departure_date=str(
                record["departure_date"]
            ),

            route=str(
                record["route"]
            ),

            airline=str(
                record["airline"]
            ),

            source=str(
                record["source"]
            ),

            lead_time=int(
                record["lead_time"]
            ),

            total_fare=float(
                record["total_fare"]
            )

        )

        db.add(fare_record)

        inserted_count += 1

    db.commit()

    return {

        "inserted": inserted_count,

        "duplicates": skipped_count

    }