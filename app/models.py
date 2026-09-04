from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime
)

from app.database import Base


class FareRecord(Base):

    __tablename__ = "fare_records"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    collection_date = Column(
        String,
        nullable=False,
        index=True
    )

    collection_time = Column(
        String,
        nullable=False
    )

    departure_date = Column(
        String,
        nullable=False,
        index=True
    )

    route = Column(
        String,
        nullable=False,
        index=True
    )

    airline = Column(
        String,
        nullable=False
    )

    source = Column(
        String,
        nullable=False
    )

    lead_time = Column(
        Integer,
        nullable=False
    )

    base_fare = Column(
        Float,
        nullable=True
    )

    taxes = Column(
        Float,
        nullable=True
    )

    fees = Column(
        Float,
        nullable=True
    )

    total_fare = Column(
        Float,
        nullable=False
    )

    availability = Column(
        String,
        nullable=False,
        default="available"
    )

    created_at = Column(
        DateTime,
        nullable=True
    )