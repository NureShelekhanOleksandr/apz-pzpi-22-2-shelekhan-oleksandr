import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.property import Property
from app.models.user import User
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.core.security import get_password_hash


async def load_json_data(file_path: str):
    """Load JSON data from a file."""
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


async def seed_users(db: AsyncSession, users_data):
    """Seed the User table with data from JSON."""
    try:
        users = []
        for user in users_data:
            user["password"] = get_password_hash(user["password"])
            users.append(User(**user))
        db.add_all(users)
        await db.commit()
        print("Users seeded successfully.")
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"Error seeding users: {e}")


async def seed_properties(db: AsyncSession, properties_data):
    """Seed the Property table with data from JSON."""
    try:
        properties = [Property(**property) for property in properties_data]
        db.add_all(properties)
        await db.commit()
        print("Properties seeded successfully.")
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"Error seeding properties: {e}")


async def seed_bookings(db: AsyncSession, bookings_data):
    """Seed the Booking table with data from JSON."""
    try:
        bookings = []
        for booking in bookings_data:
            start_date = datetime.fromisoformat(booking["start_date"])
            end_date = datetime.fromisoformat(booking["end_date"])
            booking.pop("start_date")
            booking.pop("end_date")

            bookings.append(
                Booking(
                    **booking,
                    start_date=start_date,
                    end_date=end_date,
                )
            )
        db.add_all(bookings)
        await db.commit()
        print("Bookings seeded successfully.")
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"Error seeding bookings: {e}")


async def seed_payments(db: AsyncSession, payments_data):
    """Seed the Payment table with data from JSON."""
    try:
        payments = [Payment(**payment) for payment in payments_data]
        db.add_all(payments)
        await db.commit()
        print("Payments seeded successfully.")
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"Error seeding payments: {e}")


async def seed_all(file_path: str):
    """Load data from JSON and seed all tables step by step."""
    try:
        data = await load_json_data(file_path)
        async with AsyncSession(engine) as db:
            await seed_users(db, data["users"])
            await seed_properties(db, data["properties"])
            await seed_bookings(db, data["bookings"])
            await seed_payments(db, data["payments"])
        print("Database seeding completed successfully.")
    except Exception as e:
        print(f"Error during seeding: {e}")


if __name__ == "__main__":
    asyncio.run(seed_all("test_data.json"))
