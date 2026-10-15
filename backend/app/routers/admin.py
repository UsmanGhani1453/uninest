from fastapi import APIRouter, Depends, HTTPException
from beanie import PydanticObjectId
from app.core.dependencies import require_roles
from app.models.listing import Listing
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["administration"])


@router.get("/listings/pending")
async def pending_listings(_: User = Depends(require_roles("admin"))):
    items = await Listing.find(Listing.is_verified == False).sort(-Listing.created_at).to_list()
    return [{
        "id": str(x.id), "title": x.title, "owner_id": x.owner_id,
        "address": x.address, "area": x.area, "rent_per_month": x.rent_per_month,
        "created_at": x.created_at
    } for x in items]


@router.patch("/listings/{listing_id}/verify")
async def verify_listing(listing_id: str, user: User = Depends(require_roles("admin"))):
    if not PydanticObjectId.is_valid(listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    item = await Listing.get(listing_id)
    if not item:
        raise HTTPException(status_code=404, detail="Listing not found")
    item.is_verified = True
    await item.save()
    return {"id": str(item.id), "is_verified": item.is_verified}
