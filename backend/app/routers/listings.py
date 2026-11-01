from fastapi import APIRouter, Depends, HTTPException, Query
from beanie import PydanticObjectId
from app.core.dependencies import get_current_user, require_roles
from app.models.booking import Booking
from app.models.listing import Listing, ListingRoom
from app.models.user import User
from app.schemas.listing import ListingCreate, ListingUpdate, ListingResponse

router = APIRouter(prefix="/listings", tags=["listings"])


def to_response(item: Listing) -> ListingResponse:
    return ListingResponse(
        id=str(item.id), title=item.title, description=item.description,
        accommodation_type=item.accommodation_type, rent_per_month=item.rent_per_month,
        security_deposit=item.security_deposit, address=item.address, area=item.area,
        city=item.city, university_names=item.university_names, amenities=item.amenities,
        image_urls=item.image_urls, bedrooms=item.bedrooms, bathrooms=item.bathrooms,
        capacity=item.capacity, rooms=[room.model_dump() for room in item.rooms],
        owner_id=item.owner_id, is_verified=item.is_verified,
        is_available=item.is_available, is_rejected=item.is_rejected,
        verification_note=item.verification_note,
        reviewed_at=item.reviewed_at.isoformat() if item.reviewed_at else None,
    )


@router.get("", response_model=list[ListingResponse])
async def search_listings(
    q: str | None = None,
    area: str | None = None,
    university: str | None = None,
    accommodation_type: str | None = None,
    min_rent: float | None = Query(default=None, ge=0),
    max_rent: float | None = Query(default=None, ge=0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    items = await Listing.find(
        Listing.is_available == True,
        Listing.is_verified == True,
        Listing.is_rejected != True,
        {"rooms.0": {"$exists": True}},
        *( [Listing.area == area] if area else [] ),
        *( [Listing.accommodation_type == accommodation_type] if accommodation_type else [] ),
        *( [Listing.rent_per_month >= min_rent] if min_rent is not None else [] ),
        *( [Listing.rent_per_month <= max_rent] if max_rent is not None else [] ),
    ).sort(-Listing.created_at).skip(skip).limit(limit).to_list()

    if university:
        university_query = university.casefold()
        items = [
            item for item in items
            if any(name.casefold() == university_query or university_query in name.casefold() for name in item.university_names)
        ]

    if q:
        query = q.casefold()
        items = [
            x for x in items
            if query in x.title.casefold()
            or query in x.description.casefold()
            or query in x.area.casefold()
            or any(query in name.casefold() for name in x.university_names)
        ]
    return [to_response(x) for x in items]


@router.get("/mine", response_model=list[ListingResponse])
async def my_listings(user: User = Depends(require_roles("owner", "admin"))):
    items = await Listing.find(Listing.owner_id == str(user.id)).sort(-Listing.created_at).to_list()
    return [to_response(x) for x in items]


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: str):
    if not PydanticObjectId.is_valid(listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    item = await Listing.get(listing_id)
    if not item or not item.is_verified or item.is_rejected or not item.is_available or not item.rooms:
        raise HTTPException(status_code=404, detail="Listing not found")
    return to_response(item)


@router.post("", response_model=ListingResponse, status_code=201)
async def create_listing(payload: ListingCreate, user: User = Depends(require_roles("owner", "admin"))):
    room_data = [room.model_dump(exclude={"id"}) for room in payload.rooms]
    total_seats = sum(room["seat_count"] for room in room_data)
    item = Listing(
        **payload.model_dump(exclude={"rooms"}),
        rooms=[ListingRoom(**room) for room in room_data],
        bedrooms=len(room_data),
        capacity=total_seats,
        owner_id=str(user.id),
        is_verified=False,
        is_available=True,
    )
    await item.insert()
    return to_response(item)


@router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing(listing_id: str, payload: ListingUpdate, user: User = Depends(require_roles("owner", "admin"))):
    if not PydanticObjectId.is_valid(listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    item = await Listing.get(listing_id)
    if not item or (item.owner_id != str(user.id) and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Listing not found")
    changes = payload.model_dump(exclude_unset=True)
    content_fields = set(changes) - {"is_available"}
    if "rooms" in changes:
        current_rooms = {room.id: room for room in item.rooms}
        updated_rooms = []
        for room in changes.pop("rooms"):
            room_id = room.get("id")
            if room_id in current_rooms:
                updated_rooms.append(
                    current_rooms[room_id].model_copy(
                        update={"name": room["name"], "seat_count": room["seat_count"]}
                    )
                )
            else:
                updated_rooms.append(
                    ListingRoom(name=room["name"], seat_count=room["seat_count"])
                )

        approved_bookings = await Booking.find(
            Booking.listing_id == str(item.id),
            Booking.status == "approved",
        ).to_list()
        updated_by_id = {room.id: room for room in updated_rooms}
        for booking in approved_bookings:
            target = updated_by_id.get(booking.room_id or "")
            if target is None or (booking.seat_number or 0) > target.seat_count:
                raise HTTPException(
                    status_code=409,
                    detail="Room changes cannot remove a seat assigned to an approved booking.",
                )
        item.rooms = updated_rooms
        item.bedrooms = len(updated_rooms)
        item.capacity = sum(room.seat_count for room in updated_rooms)
    for key, value in changes.items():
        setattr(item, key, value)
    if content_fields and user.role != "admin":
        item.is_verified = False
        item.is_rejected = False
        item.verification_note = None
        item.reviewed_by = None
        item.reviewed_at = None
    await item.save()
    return to_response(item)


@router.delete("/{listing_id}", status_code=204)
async def delete_listing(listing_id: str, user: User = Depends(require_roles("owner", "admin"))):
    if not PydanticObjectId.is_valid(listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    item = await Listing.get(listing_id)
    if not item or (item.owner_id != str(user.id) and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Listing not found")
    await item.delete()
