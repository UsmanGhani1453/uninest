from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.core.dependencies import require_roles
from app.models.listing import Listing
from app.schemas.listing import ListingResponse
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["administration"])


class ListingRejection(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


@router.get("/listings/pending", response_model=list[ListingResponse])
async def pending_listings(_: User = Depends(require_roles("admin"))):
    items = await Listing.find(
        Listing.is_verified == False,
        Listing.is_rejected != True,
    ).sort(-Listing.created_at).to_list()
    return [
        {
            "id": str(item.id),
            "title": item.title,
            "description": item.description,
            "accommodation_type": item.accommodation_type,
            "rent_per_month": item.rent_per_month,
            "security_deposit": item.security_deposit,
            "address": item.address,
            "area": item.area,
            "city": item.city,
            "university_names": item.university_names,
            "amenities": item.amenities,
            "image_urls": item.image_urls,
            "bedrooms": item.bedrooms,
            "bathrooms": item.bathrooms,
            "capacity": item.capacity,
            "rooms": [room.model_dump() for room in item.rooms],
            "owner_id": item.owner_id,
            "is_verified": item.is_verified,
            "is_available": item.is_available,
            "is_rejected": item.is_rejected,
            "verification_note": item.verification_note,
            "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
        }
        for item in items
    ]


@router.patch("/listings/{listing_id}/verify")
async def verify_listing(listing_id: str, user: User = Depends(require_roles("admin"))):
    if not PydanticObjectId.is_valid(listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    item = await Listing.get(listing_id)
    if not item:
        raise HTTPException(status_code=404, detail="Listing not found")
    if not item.rooms:
        raise HTTPException(
            status_code=409,
            detail="Add room and seat counts before verifying this listing.",
        )
    item.is_verified = True
    item.is_rejected = False
    item.verification_note = None
    item.reviewed_by = str(user.id)
    item.reviewed_at = datetime.now(timezone.utc)
    await item.save()
    return {
        "id": str(item.id),
        "is_verified": item.is_verified,
        "is_rejected": item.is_rejected,
        "reviewed_by": item.reviewed_by,
        "reviewed_at": item.reviewed_at,
    }


@router.patch("/listings/{listing_id}/reject")
async def reject_listing(
    listing_id: str,
    payload: ListingRejection,
    user: User = Depends(require_roles("admin")),
):
    if not PydanticObjectId.is_valid(listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    item = await Listing.get(listing_id)
    if not item:
        raise HTTPException(status_code=404, detail="Listing not found")
    item.is_verified = False
    item.is_rejected = True
    item.verification_note = payload.reason.strip()
    item.reviewed_by = str(user.id)
    item.reviewed_at = datetime.now(timezone.utc)
    await item.save()
    return {
        "id": str(item.id),
        "is_verified": item.is_verified,
        "is_rejected": item.is_rejected,
        "verification_note": item.verification_note,
        "reviewed_by": item.reviewed_by,
        "reviewed_at": item.reviewed_at,
    }
