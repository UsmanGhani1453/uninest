from pydantic import BaseModel, ConfigDict, Field, model_validator


class ListingRoomInput(BaseModel):
    id: str | None = None
    name: str = Field(min_length=1, max_length=80)
    seat_count: int = Field(ge=1, le=100)


class ListingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=5, max_length=140)
    description: str = Field(min_length=20, max_length=5000)
    accommodation_type: str = "hostel"
    rent_per_month: float = Field(gt=0)
    security_deposit: float = Field(default=0, ge=0)
    address: str = Field(min_length=5, max_length=500)
    area: str = Field(min_length=2, max_length=100)
    city: str = "Lahore"
    rooms: list[ListingRoomInput] = Field(min_length=1, max_length=100)
    university_names: list[str] = Field(default_factory=list)
    amenities: list[str] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    bathrooms: int = Field(default=1, ge=1)


class ListingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=5, max_length=140)
    description: str | None = Field(default=None, min_length=20, max_length=5000)
    accommodation_type: str | None = None
    rent_per_month: float | None = Field(default=None, gt=0)
    security_deposit: float | None = Field(default=None, ge=0)
    address: str | None = Field(default=None, min_length=5, max_length=500)
    area: str | None = Field(default=None, min_length=2, max_length=100)
    city: str | None = None
    rooms: list[ListingRoomInput] | None = Field(default=None, min_length=1, max_length=100)
    university_names: list[str] | None = None
    amenities: list[str] | None = None
    image_urls: list[str] | None = None
    bathrooms: int | None = Field(default=None, ge=1)
    is_available: bool | None = None

    @model_validator(mode="after")
    def room_ids_must_be_unique(self):
        if self.rooms is not None:
            room_ids = [room.id for room in self.rooms if room.id is not None]
            if len(room_ids) != len(set(room_ids)):
                raise ValueError("Room IDs must be unique.")
        return self


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
    rooms: list[ListingRoomInput] = Field(default_factory=list)
    owner_id: str
    is_verified: bool
    is_available: bool
    is_rejected: bool = False
    verification_note: str | None = None
    reviewed_at: str | None = None
