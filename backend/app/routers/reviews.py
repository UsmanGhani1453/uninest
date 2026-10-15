from fastapi import APIRouter, Depends, HTTPException
from beanie import PydanticObjectId
from app.core.dependencies import require_roles
from app.models.booking import Booking
from app.models.listing import Listing
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", status_code=201)
async def create_review(payload: ReviewCreate, user: User = Depends(require_roles("student"))):
    if not PydanticObjectId.is_valid(payload.booking_id):
        raise HTTPException(status_code=404, detail="Booking not found")
    booking = await Booking.get(payload.booking_id)
    if not booking or booking.student_id != str(user.id) or booking.status != "approved":
        raise HTTPException(status_code=403, detail="Only students with approved bookings can review")
    if await Review.find_one(Review.booking_id == str(booking.id)):
        raise HTTPException(status_code=409, detail="This booking already has a review")
    review = Review(
        listing_id=booking.listing_id, student_id=str(user.id),
        booking_id=str(booking.id), rating=payload.rating, comment=payload.comment,
    )
    await review.insert()
    return {"id": str(review.id), "listing_id": review.listing_id, "rating": review.rating, "comment": review.comment}


@router.get("/listing/{listing_id}")
async def listing_reviews(listing_id: str):
    if not PydanticObjectId.is_valid(listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    items = await Review.find(Review.listing_id == listing_id).sort(-Review.created_at).to_list()
    return [{"id": str(x.id), "rating": x.rating, "comment": x.comment, "created_at": x.created_at} for x in items]
