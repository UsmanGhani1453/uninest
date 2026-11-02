from datetime import datetime, timezone
from typing import Literal

from beanie import Document
from pydantic import Field


class Notification(Document):
    recipient_id: str
    event_type: Literal[
        "booking_requested",
        "booking_approved",
        "booking_rejected",
        "booking_cancelled",
    ]
    title: str
    message: str
    booking_id: str
    listing_id: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: datetime | None = None

    class Settings:
        name = "notifications"
