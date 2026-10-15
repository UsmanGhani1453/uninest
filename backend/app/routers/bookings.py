from fastapi import APIRouter, Depends, HTTPException, Query
from beanie import PydanticObjectId
from app.core.config import settings
from app.core.dependencies import require_roles
from app.models.booking import Booking
from app.models.listing import Listing
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingStatusUpdate

router = APIRouter(prefix="/bookings", tags=["bookings"])


def booking_dict(item: Booking) -> dict:
    return {
        "id": str(item.id), "listing_id": item.listing_id, "student_id": item.student_id,
        "owner_id": item.owner_id, "move_in_date": item.move_in_date,
        "duration_months": item.duration_months, "monthly_rent_snapshot": item.monthly_rent_snapshot,
        "security_deposit_snapshot": item.security_deposit_snapshot,
        "commission_rate_snapshot": item.commission_rate_snapshot,
        "commission_amount_snapshot": item.commission_amount_snapshot,
        "status": item.status, "student_message": item.student_message,
        "created_at": item.created_at,
    }


@router.post("", status_code=201)
async def create_booking(payload: BookingCreate, user: User = Depends(require_roles("student"))):
    if not PydanticObjectId.is_valid(payload.listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    listing = await Listing.get(payload.listing_id)
    if not listing or not listing.is_available or not listing.is_verified:
        raise HTTPException(status_code=404, detail="Verified available listing not found")
    rate = settings.BOOKING_COMMISSION_RATE
    item = Booking(
        listing_id=str(listing.id), student_id=str(user.id), owner_id=listing.owner_id,
        move_in_date=payload.move_in_date, duration_months=payload.duration_months,
        monthly_rent_snapshot=listing.rent_per_month,
        security_deposit_snapshot=listing.security_deposit,
        commission_rate_snapshot=rate,
        commission_amount_snapshot=round(listing.rent_per_month * rate, 2),
        student_message=payload.student_message,
    )
    await item.insert()
    return booking_dict(item)


@router.get("/mine")
async def my_bookings(user: User = Depends(require_roles("student"))):
    items = await Booking.find(Booking.student_id == str(user.id)).sort(-Booking.created_at).to_list()
    return [booking_dict(x) for x in items]


@router.get("/owner")
async def owner_bookings(user: User = Depends(require_roles("owner", "admin"))):
    items = await Booking.find(Booking.owner_id == str(user.id)).sort(-Booking.created_at).to_list()
    return [booking_dict(x) for x in items]


@router.patch("/{booking_id}/status")
async def update_booking_status(booking_id: str, payload: BookingStatusUpdate, user: User = Depends(require_roles("owner", "admin"))):
    if payload.status not in {"approved", "rejected", "cancelled"}:
        raise HTTPException(status_code=400, detail="Invalid booking status")
    if not PydanticObjectId.is_valid(booking_id):
        raise HTTPException(status_code=404, detail="Booking not found")
    item = await Booking.get(booking_id)
    if not item or (item.owner_id != str(user.id) and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Booking not found")
    item.status = payload.status
    await item.save()
    return booking_dict(item)
