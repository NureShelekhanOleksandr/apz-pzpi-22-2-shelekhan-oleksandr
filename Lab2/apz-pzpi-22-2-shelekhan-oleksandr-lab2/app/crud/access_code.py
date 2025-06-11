from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.access_code import AccessCode
from app.models.booking import Booking
from datetime import datetime
from fastapi import HTTPException
import secrets
from app.iot import SmartLock
import json
from app.crud import access_logs as access_logs_crud


def generate_access_code():
    return secrets.token_hex(8)


async def create_access_code(
    booking_id: int, valid_from: datetime, valid_until: datetime, db: AsyncSession
):
    """Create a new access code."""
    code = generate_access_code()
    access_code = AccessCode(
        booking_id=booking_id, code=code, valid_from=valid_from, valid_until=valid_until
    )
    db.add(access_code)
    await db.commit()
    await db.refresh(access_code)
    return access_code


async def get_access_code(db: AsyncSession, booking_id: int):
    """Get an access code by booking ID."""
    result = await db.execute(
        select(AccessCode).filter(AccessCode.booking_id == booking_id)
    )
    return result.scalar_one_or_none()


async def delete_access_code(db: AsyncSession, booking_id: int):
    """Delete an access code by booking ID."""
    access_code = await get_access_code(db, booking_id)
    if not access_code:
        raise HTTPException(status_code=404, detail="Access code not found")

    delete_query = (
        delete(AccessCode)
        .where(AccessCode.booking_id == booking_id)
        .returning(AccessCode)
    )
    result = await db.execute(delete_query)
    deleted_access_code = result.scalar_one()
    await db.commit()
    return deleted_access_code


async def is_access_code_valid(db: AsyncSession, booking_id: int, code: str):
    """Check if an access code is valid."""
    access_code = await get_access_code(db, booking_id)
    if not access_code:
        return False
    if access_code.code != code:
        return False
    now = datetime.now()
    if access_code.valid_from > now or access_code.valid_until < now:
        return False
    return True


async def send_smart_lock_command(db: AsyncSession, booking_id: int, command: str):
    """Send a command to the smart lock using booking ID."""
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    access_code = await get_access_code(db, booking_id)
    if not access_code:
        raise HTTPException(status_code=404, detail="Access code not found")
    
    device_id = booking.property.smart_lock_id.split(":")[0]
    encryption_key = booking.property.smart_lock_id.split(":")[1].encode()

    smart_lock = SmartLock(device_id, encryption_key)
    response = await smart_lock.send_command(command)

    await access_logs_crud.create_access_log(
        db=db,
        access_code_id=access_code.id,
        command=command,
        response_status=str(response.status),
        response_message=json.dumps(response.payload),
    )

    return response


async def send_smart_lock_command_admin(db: AsyncSession, lock_id: str, command: str):
    """Send a command to the smart lock without booking."""
    device_id = lock_id.split(":")[0]
    encryption_key = lock_id.split(":")[1].encode()

    smart_lock = SmartLock(device_id, encryption_key)
    response = await smart_lock.send_command(command)

    await access_logs_crud.create_access_log(
        db=db,
        access_code_id=None,
        command=command,
        response_status=str(response.status),
        response_message=json.dumps(response.payload),
    )

    return response
