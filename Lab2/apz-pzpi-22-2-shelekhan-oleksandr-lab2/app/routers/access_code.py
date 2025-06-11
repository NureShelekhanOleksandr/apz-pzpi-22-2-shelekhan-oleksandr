from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Booking
from app.crud import (
    access_code as access_code_crud,
    booking as booking_crud,
    access_logs as access_logs_crud,
)
from app.crud import notification as notification_crud
from app.core.database import get_db
from datetime import datetime
from app.dependencies import role_required, get_current_user
from app.iot_utils import check_temperature_task
from app.enums.user_role import Role
from app.iot import SmartLock
from app.schemas.notification import NotificationCreate
import json

router = APIRouter(
    prefix="/access-codes",
    tags=["access-codes"],
)


@router.post("/{booking_id}/generate_access_code")
async def generate_access_code(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(role_required([Role.OWNER, Role.ADMIN])),
):
    """Generate an access code for a booking."""
    booking = await booking_crud.get_booking(db, booking_id, current_user)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.start_date <= datetime.utcnow().date() <= booking.end_date:
        access_code = await access_code_crud.create_access_code(
            booking_id=booking.id,
            valid_from=booking.start_date,
            valid_until=booking.end_date,
            db=db,
        )

        # Notification for guest
        await notification_crud.create_notification(
            db,
            NotificationCreate(
                user_id=booking.user.id,
                message=f"Your access code for '{booking.property.name}' has been generated. Access code: {access_code.code}",
                type="success",
            ),
        )

        # Notification for owner
        await notification_crud.create_notification(
            db,
            NotificationCreate(
                user_id=current_user.id,
                message=f"Access code generated for booking at '{booking.property.name}'.",
                type="info",
            ),
        )

        return {"access_code": access_code.code}
    else:
        raise HTTPException(
            status_code=400,
            detail="Access code can only be generated for active",
        )


@router.delete("/{booking_id}/access_code")
async def delete_access_code(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(role_required([Role.OWNER, Role.ADMIN])),
):
    """Delete the access code for a booking."""
    booking = await booking_crud.get_booking(db, booking_id, current_user)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    await access_code_crud.delete_access_code(booking_id, db)

    # Notification for guest
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=booking.user.id,
            message=f"Access code for '{booking.property.name}' has been revoked.",
            type="warning",
        ),
    )

    return {"message": "Access code deleted"}


@router.get("/{booking_id}/access_code")
async def get_access_code(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get the access code for a booking."""
    booking = await booking_crud.get_booking(db, booking_id, current_user)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    access_code = await access_code_crud.get_access_code(db, booking_id)
    if not access_code:
        raise HTTPException(status_code=404, detail="Access code not found")

    return {"access_code": access_code.code}


@router.post("/{booking_id}/validate_access_code")
async def validate_access_code(
    booking_id: int,
    access_code: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Validate an access code for a booking."""
    booking = await booking_crud.get_booking(db, booking_id, current_user)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    is_valid = await access_code_crud.is_access_code_valid(db, booking_id, access_code)
    return {"is_valid": is_valid}


# send open command to the door
@router.post("/{booking_id}/open_door")
async def open_door(
    booking_id: int,
    access_code: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Open the door for a booking."""
    booking = await booking_crud.get_booking(db, booking_id, current_user)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    is_valid = await access_code_crud.is_access_code_valid(db, booking_id, access_code)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Access code is not valid")

    response = await access_code_crud.send_smart_lock_command(db, booking, "open_lock")

    # Notification for guest
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=booking.user.id,
            message=f"Smart lock opened for '{booking.property.name}'. Welcome!",
            type="info",
        ),
    )

    # Notification for owner
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=booking.property.owner.id,
            message=f"Guest accessed '{booking.property.name}' using smart lock.",
            type="info",
        ),
    )

    return {"message": "Door opened"}


# send close command to the door
@router.post("/{booking_id}/close_door")
async def close_door(
    booking_id: int,
    access_code: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Close the door for a booking."""
    booking = await booking_crud.get_booking(db, booking_id, current_user)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    is_valid = await access_code_crud.is_access_code_valid(db, booking_id, access_code)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Access code is not valid")

    response = await access_code_crud.send_smart_lock_command(db, booking, "close_lock")

    # Notification for guest
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=booking.user.id,
            message=f"Smart lock secured for '{booking.property.name}'.",
            type="info",
        ),
    )

    return {"message": "Door closed"}


# get temperature from the door
@router.get("/{booking_id}/get_temperature")
async def get_temperature(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(role_required([Role.ADMIN])),
):
    """Get the temperature from the door for a booking."""
    # run the task to check the temperature
    check_temperature_task.delay()
    # booking = await booking_crud.get_booking(db, booking_id, current_user)
    # if not booking:
    #     raise HTTPException(status_code=404, detail="Booking not found")

    # is_valid = await access_code_crud.is_access_code_valid(db, booking_id, access_code)
    # if not is_valid:
    #     raise HTTPException(status_code=403, detail="Access code is not valid")

    # response = await access_code_crud.send_smart_lock_command(db, booking, "get_temperature")
    # return {"temperature": response.payload}


# get temperature stats from the door
@router.get("/{booking_id}/get_temperature_stats")
async def get_temperature_stats(
    booking_id: int,
    access_code: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get the temperature statistics from the door for a booking."""
    # booking = await booking_crud.get_booking(db, booking_id, current_user)
    # if not booking:
    #     raise HTTPException(status_code=404, detail="Booking not found")

    # is_valid = await access_code_crud.is_access_code_valid(db, booking_id, access_code)
    # if not is_valid:
    #     raise HTTPException(status_code=403, detail="Access code is not valid")

    # response = await access_code_crud.send_smart_lock_command(db, booking, "get_temperature_stats")
    # return {"temperature_stats": response.payload}
