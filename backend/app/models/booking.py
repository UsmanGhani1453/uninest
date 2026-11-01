from datetime import date, datetime, timezone
from typing import Literal
from beanie import Document
from pydantic import Field


class Booking(Document):
    listing_id: str
    student_id: str
    owner_id: str
    move_in_date: date
    duration_months: int = Field(ge=1, le=24)
    room_id: str | None = None
    room_name_snapshot: str | None = None
    seat_number: int | None = Field(default=None, ge=1)
    monthly_rent_snapshot: float
    security_deposit_snapshot: float
    commission_rate_snapshot: float
    commission_amount_snapshot: float
    status: Literal["pending", "approved", "rejected", "cancelled"] = "pending"
    resolution_note: str | None = None
    cancelled_at: datetime | None = None
    cancelled_by: str | None = None
    student_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "bookings"
