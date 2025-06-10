from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.schemas.user import User
from sqlalchemy import select, delete
from fastapi import HTTPException
from app.crud.booking import get_booking


async def create_payment(db: AsyncSession, payment_data: PaymentCreate, user: User):
    """Create a new payment."""

    if payment_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive.")

    booking = await get_booking(db, payment_data.booking_id, user)

    if booking.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to create a payment for this booking.",
        )
    
    property = booking.property

    if payment_data.amount > property.price:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be less than or equal to the total amount.",
        )

    new_payment = Payment(**payment_data.model_dump())
    db.add(new_payment)
    await db.commit()
    await db.refresh(new_payment)

    return new_payment


async def check_user_payment(db: AsyncSession, payment_id: int, user: User):
    """Check if the user is allowed to view/update/delete a payment."""
    result = await db.execute(select(Payment).filter(Payment.id == payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")

    booking = await get_booking(db, payment.booking_id, user)

    if booking.user_id != user.id and booking.property.owner_id != user.id:
        raise HTTPException(
            status_code=403, detail="You are not allowed to access this payment."
        )

    return payment


async def get_payment(db: AsyncSession, payment_id: int, user: User):
    """Get a payment by ID."""
    payment = await check_user_payment(db, payment_id, user)
    return payment


async def update_payment(
    db: AsyncSession, payment_id: int, payment_data: PaymentUpdate, user: User
):
    """Update an existing payment."""

    payment = await check_user_payment(db, payment_id, user)

    for key, value in payment_data.model_dump(exclude_none=True).items():
        setattr(payment, key, value)

    await db.commit()
    await db.refresh(payment)

    return payment


async def delete_payment(db: AsyncSession, payment_id: int, user: User):
    """Delete a payment."""

    payment = await check_user_payment(db, payment_id, user)

    await db.execute(delete(Payment).filter(Payment.id == payment_id))
    await db.commit()

    return payment
