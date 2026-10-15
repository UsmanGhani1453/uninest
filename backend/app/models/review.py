from datetime import datetime, timezone
from beanie import Document
from pydantic import Field


class Review(Document):
    listing_id: str
    student_id: str
    booking_id: str
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=3, max_length=1500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "reviews"
