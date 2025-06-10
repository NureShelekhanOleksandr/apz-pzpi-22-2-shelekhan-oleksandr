from fastapi import APIRouter, Depends, HTTPException, status
from app.crud import property as property_crud
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

router = APIRouter(
    prefix="/properties",
    tags=["properties"],
)


@router.get("/", response_model=List[Property])
async def read_properties(db: AsyncSession = Depends(get_db)):
    """Read all properties."""
    return await property_crud.get_properties(db)


@router.get("/available", response_model=List[PropertyWithAvailabilityPeriods])
async def get_available_properties(db: AsyncSession = Depends(get_db)):
    """Get all available properties and their booking windows."""
    return await property_crud.get_available_properties(db)


@router.get("/{property_id}", response_model=Property)
async def read_property(property_id: int, db: AsyncSession = Depends(get_db)):
    """Read a property by ID."""
    return await property_crud.get_property(db, property_id)


@router.post("/", response_model=Property)
async def create_property(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(role_required([Role.OWNER])),
    _: User = Depends(check_not_blocked),
):
    """Create a new property."""
    return await property_crud.create_property(db, property_data, current_user)


@router.put("/{property_id}", response_model=Property)
async def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(role_required([Role.OWNER])),
    _: User = Depends(check_not_blocked),
):
    """Update an existing property."""
    return await property_crud.update_property(
        db, property_id, property_data, current_user
    )


@router.delete("/{property_id}", response_model=Property)
async def delete_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(role_required([Role.OWNER, Role.ADMIN])),
    _: User = Depends(check_not_blocked),
):
    """Delete a property"""
    return await property_crud.delete_property(db, property_id, current_user)
