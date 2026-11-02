from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_user
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


def notification_dict(item: Notification) -> dict:
    return {
        "id": str(item.id),
        "event_type": item.event_type,
        "title": item.title,
        "message": item.message,
        "booking_id": item.booking_id,
        "listing_id": item.listing_id,
        "is_read": item.is_read,
        "created_at": item.created_at,
        "read_at": item.read_at,
    }


@router.get("")
async def list_notifications(user: User = Depends(get_current_user)):
    items = await Notification.find(
        Notification.recipient_id == str(user.id)
    ).sort(-Notification.created_at).limit(50).to_list()
    unread_count = await Notification.find(
        Notification.recipient_id == str(user.id),
        Notification.is_read == False,
    ).count()
    return {"items": [notification_dict(item) for item in items], "unread_count": unread_count}


@router.patch("/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: User = Depends(get_current_user)):
    if not PydanticObjectId.is_valid(notification_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    item = await Notification.get(notification_id)
    if not item or item.recipient_id != str(user.id):
        raise HTTPException(status_code=404, detail="Notification not found")
    if not item.is_read:
        item.is_read = True
        item.read_at = datetime.now(timezone.utc)
        await item.save()
    return notification_dict(item)


@router.patch("/read-all")
async def mark_all_notifications_read(user: User = Depends(get_current_user)):
    unread_items = await Notification.find(
        Notification.recipient_id == str(user.id),
        Notification.is_read == False,
    ).to_list()
    read_at = datetime.now(timezone.utc)
    for item in unread_items:
        item.is_read = True
        item.read_at = read_at
        await item.save()
    return {"updated_count": len(unread_items)}
