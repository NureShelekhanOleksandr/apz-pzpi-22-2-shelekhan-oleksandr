from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.booking import Booking
from app.models.property import Property
from app.models.user import User
from app.schemas.user import User
from app.enums.user_role import Role
from app.schemas.booking import BookingCreate, BookingUpdate, PersonalizedOffer
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from datetime import date
from sklearn.cluster import KMeans
import numpy as np


async def check_availability(
    db: AsyncSession,
    property_id: int,
    start_date: date,
    end_date: date,
    booking_id: int = None,
) -> bool:
    """Check if a property is available for booking in the given date range."""
    if start_date >= end_date:
        raise HTTPException(
            status_code=400, detail="Start date must be before the end date."
        )

    result = await db.execute(
        select(Booking)
        .filter(Booking.property_id == property_id)
        .filter(Booking.start_date < end_date)
        .filter(Booking.end_date > start_date)
        .filter(Booking.id != booking_id)
    )
    overlapping_bookings = result.scalars().all()

    return len(overlapping_bookings) == 0


async def create_booking(db: AsyncSession, booking: BookingCreate, user: User):
    """Create a new booking."""
    if not await check_availability(
        db, booking.property_id, booking.start_date, booking.end_date
    ):
        raise HTTPException(
            status_code=400, detail="Property is not available for booking."
        )

    new_booking = Booking(**booking.model_dump(), user_id=user.id)
    # get the property with the owner
    query = select(Property).where(Property.id == booking.property_id).options(
        selectinload(Property.owner)
    )
    result = await db.execute(query)
    property = result.scalar_one()
    new_booking.property = property
    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)
    return new_booking


async def update_booking(
    db: AsyncSession, booking_id: int, booking: BookingUpdate, user: User
):
    """Update booking details."""
    db_booking = await get_booking(db, booking_id, user)

    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if db_booking.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="You are not allowed to update this booking."
        )

    if booking.start_date or booking.end_date:
        start_date = booking.start_date or db_booking.start_date
        end_date = booking.end_date or db_booking.end_date

        if not await check_availability(
            db, db_booking.property_id, start_date, end_date, booking_id
        ):
            raise HTTPException(
                status_code=400, detail="Property is not available for booking."
            )

    for key, value in booking.model_dump().items():
        setattr(db_booking, key, value)

    await db.commit()
    await db.refresh(db_booking)
    return db_booking


async def delete_booking(db: AsyncSession, booking_id: int, user: User):
    """Delete a booking."""
    db_booking = await get_booking(db, booking_id, user)
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if db_booking.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="You are not allowed to delete this booking."
        )
    delete_query = delete(Booking).where(Booking.id == booking_id).returning(Booking)
    result = await db.execute(delete_query)
    deleted_booking = result.scalar_one()
    await db.commit()
    return deleted_booking


async def get_booking(db: AsyncSession, booking_id: int, user: User):
    """Retrieve a booking by ID."""
    query = (
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.property))
    )
    result = await db.execute(query)
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if user.role == Role.USER and booking.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="You are not allowed to view this booking."
        )
    elif user.role == Role.OWNER and booking.property.owner_id != user.id:
        raise HTTPException(
            status_code=403, detail="You are not allowed to view this booking."
        )
    return booking


async def get_bookings(db: AsyncSession, user: User):
    """Retrieve all bookings for a user."""
    query = (
        select(Booking)
        .where(Booking.user_id == user.id)
        .options(selectinload(Booking.property))
    )
    result = await db.execute(query)
    bookings = result.scalars().all()
    return bookings


async def get_personalized_offers(db: AsyncSession, user: User):
    """
    Розрахувати персоналізовані пропозиції для користувача на основі попередніх бронювань.
    """

    # Отримати всі бронювання для користувача
    query = (
        select(Booking)
        .where(Booking.user_id == user.id)
        .options(selectinload(Booking.property))
    )
    result = await db.execute(query)
    bookings = result.scalars().all()

    # Якщо у користувача немає бронювань, повернути порожній список
    if not bookings:
        return []

    # Підготувати дані для кластеризації: property_id та тривалість перебування (у днях)
    data = np.array(
        [[b.property_id, (b.end_date - b.start_date).days] for b in bookings]
    )

    # Визначити кількість кластерів
    n_clusters = min(3, len(data))

    # Застосувати кластеризацію KMeans для групування бронювань у кластери
    kmeans = KMeans(n_clusters=n_clusters).fit(data)
    clusters = kmeans.predict(data)

    # Отримати всі властивості
    all_properties_query = select(Property)
    all_properties_result = await db.execute(all_properties_query)
    all_properties = all_properties_result.scalars().all()

    # Отримати властивості, які користувач ще не бронював
    booked_property_ids = {b.property_id for b in bookings}
    new_properties = [p for p in all_properties if p.id not in booked_property_ids]

    offers = []
    # Генерувати персоналізовані пропозиції на основі кластерів
    for cluster in set(clusters):
        cluster_indices = np.where(clusters == cluster)[0]
        cluster_bookings = [bookings[i] for i in cluster_indices]
        
        # Вибрати нову властивість для пропозиції
        if new_properties:
            property = new_properties.pop(0)
        else:
            property = cluster_bookings[0].property

        # Розрахувати знижку на основі кількості бронювань у кластері
        total_days = sum((b.end_date - b.start_date).days for b in cluster_bookings)
        discount = min(20.0, 5.0 + 0.1 * total_days) 

        message = "Спеціальна пропозиція саме для вас!"
        offers.append(
            PersonalizedOffer(property=property, discount=discount, message=message)
        )

    return offers


async def get_owner_bookings(db: AsyncSession, owner_id: int):
    """Retrieve all bookings for properties owned by the owner."""
    query = (
        select(Booking)
        .join(Booking.property)
        .where(Property.owner_id == owner_id)
        .options(selectinload(Booking.property))
    )
    result = await db.execute(query)
    bookings = result.scalars().all()
    return bookings
