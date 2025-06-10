from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine

import asyncio

from app.core.config import settings
from app.crud import user as user_crud
from app.schemas.user import UserCreate
from app.models.user import User
from sqlalchemy import select
from app.enums.user_role import Role


async def init_db(session: AsyncSession):
    try:
        user = await session.execute(
            select(User).filter(User.email == settings.FIRST_SUPERUSER_EMAIL)
        )
        if not user.scalar_one_or_none():
            user_data = UserCreate(
                first_name=settings.FIRST_SUPERUSER_FIRST_NAME,
                last_name=settings.FIRST_SUPERUSER_LAST_NAME,
                email=settings.FIRST_SUPERUSER_EMAIL,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                role=Role.ADMIN,
            )
            await user_crud.create_user(session, user_data)
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise



async def init() -> None:
    async with AsyncSession(engine) as session:
        await init_db(session)


async def main() -> None:
    logger.info("Creating initial data")
    await init()
    logger.info("Initial data created")


if __name__ == "__main__":
    asyncio.run(main())
