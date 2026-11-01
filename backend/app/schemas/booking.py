from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    listing_id: str
    move_in_date: date = Field(description="Requested move-in date; must be today or later")
    duration_months: int = Field(ge=1, le=24)
    student_message: str | None = Field(default=None, max_length=1000)


class BookingStatusUpdate(BaseModel):
    status: Literal["approved", "rejected", "cancelled"]
