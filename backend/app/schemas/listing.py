from pydantic import BaseModel, Field


class ListingCreate(BaseModel):
    title: str = Field(min_length=5, max_length=140)
    description: str = Field(min_length=20, max_length=5000)
    accommodation_type: str = "hostel"
    rent_per_month: float = Field(gt=0)
    security_deposit: float = Field(default=0, ge=0)
    address: str
    area: str
    city: str = "Lahore"
    university_names: list[str] = []
    amenities: list[str] = []
    image_urls: list[str] = []
    bedrooms: int = Field(default=1, ge=1)
    bathrooms: int = Field(default=1, ge=1)
    capacity: int = Field(default=1, ge=1)


class ListingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=140)
    description: str | None = Field(default=None, min_length=20, max_length=5000)
    rent_per_month: float | None = Field(default=None, gt=0)
    security_deposit: float | None = Field(default=None, ge=0)
    address: str | None = None
    area: str | None = None
    amenities: list[str] | None = None
    image_urls: list[str] | None = None
    is_available: bool | None = None


class ListingResponse(BaseModel):
    id: str
    title: str
    description: str
    accommodation_type: str
    rent_per_month: float
    security_deposit: float
    address: str
    area: str
    city: str
    university_names: list[str]
    amenities: list[str]
    image_urls: list[str]
    bedrooms: int
    bathrooms: int
    capacity: int
    owner_id: str
    is_verified: bool
    is_available: bool
