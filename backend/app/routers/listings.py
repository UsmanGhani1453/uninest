from fastapi import APIRouter, Depends, HTTPException, Query
from beanie import PydanticObjectId
from app.core.dependencies import get_current_user, require_roles
from app.models.listing import Listing
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
        capacity=item.capacity, owner_id=item.owner_id, is_verified=item.is_verified,
        is_available=item.is_available
    )


@router.get("", response_model=list[ListingResponse])
async def search_listings(
    q: str | None = None,
    area: str | None = None,
    university: str | None = None,
    accommodation_type: str | None = None,
    min_rent: float | None = Query(default=None, ge=0),
    max_rent: float | None = Query(default=None, ge=0),
    verified_only: bool = True,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    items = await Listing.find(
        Listing.is_available == True,
        *( [Listing.is_verified == True] if verified_only else [] ),
        *( [Listing.area == area] if area else [] ),
        *( [Listing.accommodation_type == accommodation_type] if accommodation_type else [] ),
        *( [Listing.university_names == university] if university else [] ),
        *( [Listing.rent_per_month >= min_rent] if min_rent is not None else [] ),
        *( [Listing.rent_per_month <= max_rent] if max_rent is not None else [] ),
    ).sort(-Listing.created_at).skip(skip).limit(limit).to_list()
    if q:
        query = q.casefold()
        items = [x for x in items if query in x.title.casefold() or query in x.description.casefold() or query in x.area.casefold()]
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
    if not item:
        raise HTTPException(status_code=404, detail="Listing not found")
    return to_response(item)


@router.post("", response_model=ListingResponse, status_code=201)
async def create_listing(payload: ListingCreate, user: User = Depends(require_roles("owner", "admin"))):
    item = Listing(**payload.model_dump(), owner_id=str(user.id))
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
    for key, value in changes.items():
        setattr(item, key, value)
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
