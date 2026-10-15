from datetime import datetime, timezone
from typing import Literal
from beanie import Document
from pydantic import Field


class Listing(Document):
    title: str = Field(min_length=5, max_length=140)
    description: str = Field(min_length=20, max_length=5000)
    accommodation_type: Literal["hostel", "apartment", "room"] = "hostel"
    rent_per_month: float = Field(gt=0)
    security_deposit: float = Field(default=0, ge=0)
    address: str
    area: str
    city: str = "Lahore"
    university_names: list[str] = Field(default_factory=list)
    amenities: list[str] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    bedrooms: int = Field(default=1, ge=1)
    bathrooms: int = Field(default=1, ge=1)
    capacity: int = Field(default=1, ge=1)
    owner_id: str
    is_verified: bool = False
    is_available: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "listings"
        indexes = ["text"]
