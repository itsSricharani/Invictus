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
        nullable=False
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


    total_fare = Column(
        Float,
        nullable=False
    )


    created_at = Column(
        DateTime
    )