from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from beanie import Document
from pydantic import BaseModel, Field


class ListingRoom(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str = Field(min_length=1, max_length=80)
    seat_count: int = Field(ge=1, le=100)


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
    rooms: list[ListingRoom] = Field(default_factory=list)
    availability_version: int = 0
    owner_id: str
    is_verified: bool = False
    is_rejected: bool = False
    verification_note: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    is_available: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "listings"
        indexes = ["text"]
