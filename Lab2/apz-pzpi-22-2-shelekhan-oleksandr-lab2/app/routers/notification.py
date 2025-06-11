from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies import get_current_user
from app.schemas.notification import Notification
from app.crud import notification as notification_crud
from app.models.user import User
from typing import List

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


@router.get("/", response_model=List[Notification])
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await notification_crud.get_user_notifications(db, current_user.id)


@router.put("/{notification_id}/read", response_model=Notification)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = await notification_crud.mark_notification_read(
        db, notification_id, current_user.id
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = await notification_crud.delete_notification(
        db, notification_id, current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted successfully"}


@router.delete("/")
async def clear_all_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = await notification_crud.delete_all_user_notifications(db, current_user.id)
    return {"message": f"Deleted {count} notifications"}
