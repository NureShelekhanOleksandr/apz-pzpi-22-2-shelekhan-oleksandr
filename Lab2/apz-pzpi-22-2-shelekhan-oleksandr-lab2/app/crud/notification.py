from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from typing import List


async def create_notification(
    db: AsyncSession, notification: NotificationCreate
) -> Notification:
    notif = Notification(**notification.dict())
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


async def get_user_notifications(db: AsyncSession, user_id: int) -> List[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )
    return result.scalars().all()


async def mark_notification_read(
    db: AsyncSession, notification_id: int, user_id: int
) -> Notification:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
    )
    notif = result.scalar_one_or_none()
    if notif:
        notif.read = True
        await db.commit()
        await db.refresh(notif)
    return notif


async def delete_notification(
    db: AsyncSession, notification_id: int, user_id: int
) -> bool:
    result = await db.execute(
        delete(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
    )
    await db.commit()
    return result.rowcount > 0


async def delete_all_user_notifications(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        delete(Notification).where(Notification.user_id == user_id)
    )
    await db.commit()
    return result.rowcount
