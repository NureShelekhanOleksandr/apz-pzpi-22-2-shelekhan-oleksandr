from app.core.database import AsyncSession
from app.models import User, Property, Booking, Payment, AccessCode, AccessLog
from app.core.database import engine
from sqlalchemy import text

async def delete_all_data():
    try:
        async with AsyncSession(engine) as session:
            await session.execute(text("SET session_replication_role = 'replica'"))
            await session.execute(User.__table__.delete())
            await session.execute(Property.__table__.delete())
            await session.execute(Booking.__table__.delete())
            await session.execute(Payment.__table__.delete())
            await session.execute(AccessCode.__table__.delete())
            await session.execute(AccessLog.__table__.delete())
            await session.execute(text("SET session_replication_role = 'origin'"))
            await session.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE properties_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE bookings_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE payments_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE access_codes_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE access_logs_id_seq RESTART WITH 1"))
            await session.commit()
    finally:
        await session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(delete_all_data())
