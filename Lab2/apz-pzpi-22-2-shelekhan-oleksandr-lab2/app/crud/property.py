from sqlalchemy.ext.asyncio import AsyncSession
from app.models.property import Property
from app.models.user import User, Role
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyWithAvailabilityPeriods, AvailabilityPeriod
from app.schemas.user import User
from sqlalchemy import select, delete
from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from app.enums.booking_status import BookingStatus
from datetime import date
from datetime import timedelta


async def create_property(
    db: AsyncSession, property_data: PropertyCreate, user: User
):
    """Create a new property."""
    new_property = Property(**property_data.model_dump(), owner_id=user.id)
    db.add(new_property)
    await db.commit()
    await db.refresh(new_property)

    return new_property


async def update_property(
    db: AsyncSession, property_id: int, property_data: PropertyUpdate, user: User
):
    """Update an existing property."""
    result = await db.execute(select(Property).filter(Property.id == property_id))
    property = result.scalar_one_or_none()

    if not property:
        raise HTTPException(status_code=404, detail="Property not found.")

    if property.owner_id != user.id:
        raise HTTPException(
            status_code=403, detail="You are not allowed to update this property."
        )

    for key, value in property_data.model_dump(exclude_none=True).items():
        setattr(property, key, value)

    await db.commit()
    await db.refresh(property)

    return property


async def delete_property(db: AsyncSession, property_id: int, user: User):
    """Delete a property."""
    result = await db.execute(select(Property).filter(Property.id == property_id))
    property = result.scalar_one_or_none()

    if not property:
        raise HTTPException(status_code=404, detail="Property not found.")

    if property.owner_id != user.id:
        raise HTTPException(
            status_code=403, detail="You are not allowed to delete this property."
        )

    await db.execute(delete(Property).filter(Property.id == property_id))
    await db.commit()

    return property


async def get_property(db: AsyncSession, property_id: int):
    """Read a property by ID."""
    result = await db.execute(select(Property).filter(Property.id == property_id))
    property = result.scalar_one_or_none()

    if not property:
        raise HTTPException(status_code=404, detail="Property not found.")

    return property


async def get_properties(db: AsyncSession):
    """Read all properties."""
    result = await db.execute(select(Property))
    properties = result.scalars().all()

    return properties


async def get_available_properties(db: AsyncSession):
    """Get all available properties along with their free time windows."""
    # Load all properties along with their bookings
    result = await db.execute(select(Property).options(selectinload(Property.bookings)))
    properties = result.scalars().all()

    today = date.today()
    max_date = today + timedelta(days=365)  # Assume we are looking for availability up to a year ahead
    available_properties = []

    for property in properties:
        # Get all bookings for the property
        bookings = sorted(property.bookings, key=lambda b: b.start_date)

        # Find free periods
        availability_periods = []
        current_start = today

        for booking in bookings:
            if current_start < booking.start_date:
                # Add available period
                availability_periods.append({
                    "start_date": current_start,
                    "end_date": booking.start_date - timedelta(days=1)
                })
            # Update current start
            current_start = max(current_start, booking.end_date + timedelta(days=1))

        # If there is a period left after the last booking
        if current_start <= max_date:
            availability_periods.append({
                "start_date": current_start,
                "end_date": max_date
            })

        # Add property with available periods if there is at least one
        if availability_periods:
            available_properties.append(PropertyWithAvailabilityPeriods(
                id=property.id,
                owner_id=property.owner_id,
                name=property.name,
                description=property.description,
                rooms=property.rooms,
                price=property.price,
                location=property.location,
                availability_periods=availability_periods
            ))

    return available_properties