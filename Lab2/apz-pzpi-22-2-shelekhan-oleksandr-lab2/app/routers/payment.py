from fastapi import APIRouter, Depends, HTTPException
from app.schemas.payment import PaymentCreate, Payment, PaymentUpdate
from app.crud import payment as payment_crud
from app.crud import notification as notification_crud
from app.core.database import get_db
from app.dependencies import get_current_user, role_required
from app.enums.user_role import Role
from app.enums.payment import PaymentStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.schemas.booking import Booking
from app.schemas.user import User
from app.schemas.notification import NotificationCreate

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)


@router.post("/", response_model=Payment)
async def create_new_payment(
    payment: PaymentCreate,
    db=Depends(get_db),
    current_user=Depends(role_required([Role.USER])),
):
    new_payment = await payment_crud.create_payment(db, payment, current_user)

    # Get booking details for notification
    booking = new_payment.booking
    property_name = (
        booking.property.name if booking and booking.property else "Unknown Property"
    )

    # Notification for guest
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=current_user.id,
            message=f"Payment of ${new_payment.amount} for '{property_name}' has been processed.",
            type="success" if new_payment.status == PaymentStatus.SUCCESS else "error",
        ),
    )

    # Notification for owner if payment is successful
    if (
        new_payment.status == PaymentStatus.SUCCESS
        and booking
        and booking.property.owner
    ):
        await notification_crud.create_notification(
            db,
            NotificationCreate(
                user_id=booking.property.owner.id,
                message=f"Payment of ${new_payment.amount} received for '{property_name}'.",
                type="success",
            ),
        )

    return new_payment


@router.get("/{payment_id}", response_model=Payment)
async def read_payment(
    payment_id: int, db=Depends(get_db), current_user=Depends(get_current_user)
):
    return await payment_crud.get_payment(db, payment_id, current_user)


@router.delete("/{payment_id}")
async def delete_payment(
    payment_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    deleted_payment = await payment_crud.delete_payment(db, payment_id, current_user)

    # Notification for payment deletion
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=current_user.id,
            message=f"Payment of ${deleted_payment.amount} has been cancelled.",
            type="warning",
        ),
    )

    return deleted_payment


@router.get("/", response_model=List[Payment])
async def get_user_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await payment_crud.get_user_payments(db, current_user)
