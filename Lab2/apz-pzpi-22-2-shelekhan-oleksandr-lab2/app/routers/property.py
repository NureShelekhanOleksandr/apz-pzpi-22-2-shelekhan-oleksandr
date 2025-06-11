from fastapi import APIRouter, Depends, HTTPException, status
from app.crud import property as property_crud
from app.crud import notification as notification_crud
from app.schemas.property import (
    PropertyCreate,
    Property,
    PropertyUpdate,
    PropertyWithAvailabilityPeriods,
    AvailabilityPeriod,
)
from app.core.database import get_db
from app.dependencies import role_required, check_not_blocked
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.enums.user_role import Role
from app.models.user import User
from app.schemas.notification import NotificationCreate
from sqlalchemy import select

router = APIRouter(
    prefix="/properties",
    tags=["properties"],
)


@router.get("/", response_model=List[Property])
async def read_properties(db: AsyncSession = Depends(get_db)):
    """Read all properties."""
    # Fetch all properties from the database
    return await property_crud.get_properties(db)


@router.get("/available", response_model=List[PropertyWithAvailabilityPeriods])
async def get_available_properties(db: AsyncSession = Depends(get_db)):
    """Get all available properties and their booking windows."""
    # Fetch available properties and their availability periods
    return await property_crud.get_available_properties(db)


@router.get("/my-properties", response_model=List[Property])
async def read_owner_properties(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(role_required([Role.OWNER])),
    _: User = Depends(check_not_blocked),
):
    """Get all properties owned by the current user."""
    return await property_crud.get_properties_by_owner(db, current_user.id)


@router.get("/{property_id}", response_model=Property)
async def read_property(property_id: int, db: AsyncSession = Depends(get_db)):
    """Read a property by ID."""
    # Fetch property by ID from the database
    return await property_crud.get_property(db, property_id)


@router.get("/{property_id}/availability", response_model=List[AvailabilityPeriod])
async def get_property_availability(
    property_id: int, db: AsyncSession = Depends(get_db)
):
    """Get availability periods for a specific property."""
    return await property_crud.get_property_availability(db, property_id)


@router.post("/", response_model=Property)
async def create_property(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(role_required([Role.OWNER])),
    _: User = Depends(check_not_blocked),
):
    """Create a new property."""
    # Create a new property in the database
    new_property = await property_crud.create_property(db, property_data, current_user)

    # Notification for owner
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=current_user.id,
            message=f"Your property '{new_property.name}' has been successfully created and is now available for booking!",
            type="success",
        ),
    )

    return new_property


@router.put("/{property_id}", response_model=Property)
async def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(role_required([Role.OWNER])),
    _: User = Depends(check_not_blocked),
):
    """Update an existing property."""
    # Update property details in the database
    updated_property = await property_crud.update_property(
        db, property_id, property_data, current_user
    )

    # Notification for owner
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=current_user.id,
            message=f"Your property '{updated_property.name}' has been successfully updated!",
            type="info",
        ),
    )

    return updated_property


@router.delete("/{property_id}", response_model=Property)
async def delete_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(role_required([Role.OWNER, Role.ADMIN])),
    _: User = Depends(check_not_blocked),
):
    """Delete a property"""
    # Delete property from the database
    deleted_property = await property_crud.delete_property(
        db, property_id, current_user
    )

    # Notification for owner
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=current_user.id,
            message=f"Your property '{deleted_property.name}' has been deleted.",
            type="warning",
        ),
    )

    return deleted_property
