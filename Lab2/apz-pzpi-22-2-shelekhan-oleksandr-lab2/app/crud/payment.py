from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment
from app.models.property import Property
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.schemas.user import User
from sqlalchemy import select, delete
from fastapi import HTTPException
from app.crud.booking import get_booking
from app.models.booking import Booking
from sqlalchemy.orm import selectinload


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

    if payment_data.amount > booking.booking_price:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be less than or equal to the booking price.",
        )

    new_payment = Payment(**payment_data.model_dump())
    db.add(new_payment)
    await db.commit()
    await db.refresh(new_payment)

    # Load the payment with all relationships
    result = await db.execute(
        select(Payment)
        .filter(Payment.id == new_payment.id)
        .options(
            selectinload(Payment.booking)
            .selectinload(Booking.property)
            .selectinload(Property.owner)
        )
    )
    payment_with_relations = result.scalar_one()

    return payment_with_relations


async def check_user_payment(db: AsyncSession, payment_id: int, user: User):
    """Check if the user is allowed to view/update/delete a payment."""
    result = await db.execute(
        select(Payment)
        .filter(Payment.id == payment_id)
        .options(
            selectinload(Payment.booking)
            .selectinload(Booking.property)
            .selectinload(Property.owner)
        )
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")

    booking = payment.booking

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


async def get_user_payments(db: AsyncSession, user: User):
    """Get all payments for the current user."""
    query = (
        select(Payment)
        .join(Booking)
        .where(Booking.user_id == user.id)
        .options(selectinload(Payment.booking).selectinload(Booking.property))
    )
    result = await db.execute(query)
    return result.scalars().all()
