from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Iterable, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from beanie import PydanticObjectId
from pymongo.errors import PyMongoError

from app.core.config import settings
from app.core.dependencies import get_current_user, require_roles
from app.models.booking import Booking
from app.models.listing import Listing, ListingRoom
from app.models.notification import Notification
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingStatusUpdate

router = APIRouter(prefix="/bookings", tags=["bookings"])

BOOKING_NOTIFICATION_TITLES = {
    "booking_requested": "New booking request",
    "booking_approved": "Booking approved",
    "booking_rejected": "Booking request declined",
    "booking_cancelled": "Booking cancelled",
}
BookingNotificationEvent = Literal[
    "booking_requested",
    "booking_approved",
    "booking_rejected",
    "booking_cancelled",
]


async def notify_booking_event(
    event_type: BookingNotificationEvent,
    recipient_ids: Iterable[str],
    booking: Booking,
    message: str,
    session,
) -> None:
    for recipient_id in set(recipient_ids):
        if not recipient_id:
            continue
        await Notification(
            recipient_id=recipient_id,
            event_type=event_type,
            title=BOOKING_NOTIFICATION_TITLES[event_type],
            message=message,
            booking_id=str(booking.id),
            listing_id=booking.listing_id,
        ).insert(session=session)


async def admin_user_ids(session) -> list[str]:
    admins = await User.find(User.role == "admin", session=session).to_list()
    return [str(admin.id) for admin in admins]


def stay_end_date(start: date, duration_months: int) -> date:
    month_index = start.month - 1 + duration_months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(start.day, monthrange(year, month)[1]))


def stays_overlap(
    first_start: date,
    first_duration: int,
    second_start: date,
    second_duration: int,
) -> bool:
    first_end = stay_end_date(first_start, first_duration)
    second_end = stay_end_date(second_start, second_duration)
    return first_start < second_end and second_start < first_end


def room_has_available_seat(
    room: ListingRoom,
    move_in_date: date,
    duration_months: int,
    approved_bookings: Iterable[Booking],
) -> bool:
    occupied_seats = {
        booking.seat_number
        for booking in approved_bookings
        if booking.room_id == room.id
        and booking.seat_number is not None
        and stays_overlap(
            move_in_date,
            duration_months,
            booking.move_in_date,
            booking.duration_months,
        )
    }
    return any(seat_number not in occupied_seats for seat_number in range(1, room.seat_count + 1))


def booking_dict(item: Booking) -> dict:
    return {
        "id": str(item.id), "listing_id": item.listing_id, "student_id": item.student_id,
        "owner_id": item.owner_id, "move_in_date": item.move_in_date,
        "duration_months": item.duration_months, "monthly_rent_snapshot": item.monthly_rent_snapshot,
        "room_id": item.room_id, "room_name": item.room_name_snapshot,
        "seat_number": item.seat_number,
        "security_deposit_snapshot": item.security_deposit_snapshot,
        "commission_rate_snapshot": item.commission_rate_snapshot,
        "commission_amount_snapshot": item.commission_amount_snapshot,
        "status": item.status, "resolution_note": item.resolution_note,
        "cancelled_at": item.cancelled_at, "cancelled_by": item.cancelled_by,
        "student_message": item.student_message,
        "created_at": item.created_at,
    }


@router.post("", status_code=201)
async def create_booking(
    payload: BookingCreate,
    request: Request,
    user: User = Depends(require_roles("student")),
):
    if payload.move_in_date < date.today():
        raise HTTPException(status_code=422, detail="Move-in date cannot be in the past")
    if not PydanticObjectId.is_valid(payload.listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    listing = await Listing.get(payload.listing_id)
    if (
        not listing
        or not listing.is_available
        or not listing.is_verified
        or listing.is_rejected
    ):
        raise HTTPException(status_code=404, detail="Verified available listing not found")
    if listing.owner_id == str(user.id):
        raise HTTPException(status_code=400, detail="You cannot book your own listing")
    if not listing.rooms:
        raise HTTPException(status_code=409, detail="This listing has no configured room seats yet.")

    approved_bookings = await Booking.find(
        Booking.listing_id == str(listing.id),
        Booking.status == "approved",
    ).to_list()
    if not any(
        room_has_available_seat(room, payload.move_in_date, payload.duration_months, approved_bookings)
        for room in listing.rooms
    ):
        raise HTTPException(
            status_code=409,
            detail="No seats are available in this property for the selected dates. Please choose another listing.",
        )

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
    try:
        async with await request.app.state.mongo_client.start_session() as mongo_session:
            async with mongo_session.start_transaction():
                await item.insert(session=mongo_session)
                admins = await admin_user_ids(mongo_session)
                recipients = [listing.owner_id, *admins]
                message = (
                    f"A student requested a seat at {listing.title} for "
                    f"{item.move_in_date.isoformat()}."
                )
                await notify_booking_event(
                    "booking_requested",
                    recipients,
                    item,
                    message,
                    mongo_session,
                )
    except PyMongoError as error:
        raise HTTPException(
            status_code=503,
            detail="Could not save this booking request and its notifications. Please retry.",
        ) from error
    return booking_dict(item)


@router.get("/mine")
async def my_bookings(user: User = Depends(require_roles("student"))):
    items = await Booking.find(Booking.student_id == str(user.id)).sort(-Booking.created_at).to_list()
    return [booking_dict(x) for x in items]


@router.get("/owner")
async def owner_bookings(user: User = Depends(require_roles("owner", "admin"))):
    query = {} if user.role == "admin" else {"owner_id": str(user.id)}
    items = await Booking.find(query).sort(-Booking.created_at).to_list()
    return [booking_dict(x) for x in items]


@router.patch("/{booking_id}/status")
async def update_booking_status(
    request: Request,
    booking_id: str,
    payload: BookingStatusUpdate,
    user: User = Depends(get_current_user),
):
    if not PydanticObjectId.is_valid(booking_id):
        raise HTTPException(status_code=404, detail="Booking not found")
    item = await Booking.get(booking_id)
    if not item:
        raise HTTPException(status_code=404, detail="Booking not found")

    is_admin = user.role == "admin"
    is_owner = user.role == "owner" and item.owner_id == str(user.id)
    is_student = user.role == "student" and item.student_id == str(user.id)
    if not (is_admin or is_owner or is_student):
        raise HTTPException(status_code=404, detail="Booking not found")

    try:
        async with await request.app.state.mongo_client.start_session() as mongo_session:
            async with mongo_session.start_transaction():
                item = await Booking.get(booking_id, session=mongo_session)
                if not item:
                    raise HTTPException(status_code=404, detail="Booking not found")
                previous_status = item.status

                if item.status == "pending":
                    if payload.status == "cancelled":
                        if not (is_student or is_admin):
                            raise HTTPException(
                                status_code=403,
                                detail="Only the student or an admin can cancel a pending booking",
                            )
                    elif not (is_owner or is_admin):
                        raise HTTPException(
                            status_code=403,
                            detail="Only the listing owner or an admin can review a booking",
                        )
                elif item.status == "approved":
                    if payload.status != "cancelled":
                        raise HTTPException(
                            status_code=409,
                            detail="Approved bookings can only be cancelled",
                        )
                    if is_student and item.move_in_date <= date.today():
                        raise HTTPException(
                            status_code=403,
                            detail="Students can cancel an approved booking only before the move-in date. Contact the property owner or an admin.",
                        )
                    if not (is_student or is_owner or is_admin):
                        raise HTTPException(status_code=403, detail="You cannot cancel this booking")
                    listing = await Listing.get(item.listing_id, session=mongo_session)
                    if listing:
                        # Serialize cancellations with approvals so a released seat is immediately reusable.
                        listing.availability_version += 1
                        await listing.save(session=mongo_session)
                else:
                    raise HTTPException(
                        status_code=409,
                        detail="Rejected or cancelled bookings cannot be changed",
                    )

                if payload.status == "approved":
                    listing = await Listing.get(item.listing_id, session=mongo_session)
                    if (
                        not listing
                        or not listing.is_available
                        or not listing.is_verified
                        or listing.is_rejected
                    ):
                        raise HTTPException(
                            status_code=409,
                            detail="This property is no longer available for booking.",
                        )
                    if not listing.rooms:
                        raise HTTPException(
                            status_code=409,
                            detail="This listing has no configured room seats.",
                        )

                    # All seat approvals write the listing in the same transaction to serialize allocation.
                    listing.availability_version += 1
                    await listing.save(session=mongo_session)
                    approved_bookings = await Booking.find(
                        Booking.listing_id == item.listing_id,
                        Booking.status == "approved",
                        session=mongo_session,
                    ).to_list()
                    legacy_booking_without_seat = any(
                        booking.room_id is None
                        and stays_overlap(
                            item.move_in_date,
                            item.duration_months,
                            booking.move_in_date,
                            booking.duration_months,
                        )
                        for booking in approved_bookings
                    )
                    if legacy_booking_without_seat:
                        item.status = "rejected"
                        item.resolution_note = (
                            "An existing approved booking has no seat assignment. "
                            "Please contact the property owner and choose another listing."
                        )
                    else:
                        assigned_room = None
                        assigned_seat = None
                        for room in listing.rooms:
                            occupied_seats = {
                                booking.seat_number
                                for booking in approved_bookings
                                if booking.room_id == room.id
                                and booking.seat_number is not None
                                and stays_overlap(
                                    item.move_in_date,
                                    item.duration_months,
                                    booking.move_in_date,
                                    booking.duration_months,
                                )
                            }
                            assigned_seat = next(
                                (
                                    seat_number
                                    for seat_number in range(1, room.seat_count + 1)
                                    if seat_number not in occupied_seats
                                ),
                                None,
                            )
                            if assigned_seat is not None:
                                assigned_room = room
                                break
                        if assigned_room is None or assigned_seat is None:
                            item.status = "rejected"
                            item.resolution_note = (
                                "No seats remain available for these dates. "
                                "Please choose another property."
                            )
                        else:
                            item.room_id = assigned_room.id
                            item.room_name_snapshot = assigned_room.name
                            item.seat_number = assigned_seat

                if item.status == "pending" or (
                    item.status == "approved" and payload.status == "cancelled"
                ):
                    item.status = payload.status
                if item.status == "cancelled":
                    item.cancelled_at = datetime.now(timezone.utc)
                    item.cancelled_by = str(user.id)
                await item.save(session=mongo_session)
                if item.status != previous_status:
                    listing = await Listing.get(item.listing_id, session=mongo_session)
                    listing_title = listing.title if listing else "the property"
                    admins = [] if is_admin else await admin_user_ids(mongo_session)
                    if item.status == "approved":
                        event_type = "booking_approved"
                        recipients = [item.student_id, *admins]
                        message = f"Your booking at {listing_title} was approved."
                    elif item.status == "rejected":
                        event_type = "booking_rejected"
                        recipients = [item.student_id, *admins]
                        message = item.resolution_note or f"Your booking request at {listing_title} was declined."
                    else:
                        event_type = "booking_cancelled"
                        if is_admin:
                            recipients = [item.student_id, item.owner_id]
                            message = f"An administrator cancelled the booking at {listing_title}."
                        elif is_student:
                            recipients = [item.owner_id, *admins]
                            message = f"A student cancelled their booking request at {listing_title}."
                        else:
                            recipients = [item.student_id, *admins]
                            message = f"The owner cancelled the booking at {listing_title}."
                    await notify_booking_event(
                        event_type,
                        recipients,
                        item,
                        message,
                        mongo_session,
                    )
    except PyMongoError as error:
        raise HTTPException(
            status_code=503,
            detail="Could not confirm this booking because availability changed. Please retry.",
        ) from error
    return booking_dict(item)
