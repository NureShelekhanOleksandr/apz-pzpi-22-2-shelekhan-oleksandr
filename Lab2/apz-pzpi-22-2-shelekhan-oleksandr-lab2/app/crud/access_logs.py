from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.access_code import AccessCode
from app.models.access_log import AccessLog
from datetime import datetime
from fastapi import HTTPException


async def create_access_log(
    db: AsyncSession,
    command: str,
    response_status: str,
    response_message: str = None,
    access_code_id: int = None,
):
    """Create an access log."""
    access_log = AccessLog(
        access_code_id=access_code_id,
        command=command,
        response_status=response_status,
        response_message=response_message,
    )
    db.add(access_log)
    await db.commit()
    return access_log


async def get_access_logs(db: AsyncSession, access_code_id: int):
    """Get access logs for an access code."""
    stmt = select(AccessLog).where(AccessLog.access_code_id == access_code_id)
    result = await db.execute(stmt)
    return result.scalars().all()