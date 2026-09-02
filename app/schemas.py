from pydantic import BaseModel
from datetime import datetime


class FareRecordBase(BaseModel):

    collection_date: str

    collection_time: str

    departure_date: str

    route: str

    airline: str

    source: str

    lead_time: int

    total_fare: float


class FareRecordResponse(
    FareRecordBase
):

    id: int

    created_at: datetime | None

    class Config:
        from_attributes = True