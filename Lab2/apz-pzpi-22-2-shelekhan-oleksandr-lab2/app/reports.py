from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.booking import get_owner_bookings, get_bookings
from app.schemas.user import User
from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from fastapi import HTTPException
from decimal import Decimal

async def generate_owner_report(db: AsyncSession, owner: User) -> str:
    # Fetch bookings for the owner
    bookings = await get_owner_bookings(db, owner.id)

    if not bookings:
        raise HTTPException(status_code=404, detail="No bookings found for the owner.")

    # Set up the Jinja2 environment
    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("owner_report.html")

    # Calculate additional metrics
    total_revenue = sum(Decimal(booking.property.price) for booking in bookings)
    average_price = (total_revenue / Decimal(len(bookings))).quantize(Decimal('0.01')) if bookings else Decimal('0.00')
    highest_price = max(Decimal(booking.property.price) for booking in bookings) if bookings else Decimal('0.00')
    lowest_price = min(Decimal(booking.property.price) for booking in bookings) if bookings else Decimal('0.00')

    # Prepare data for the template
    report_data = {
        "owner": {"first_name": owner.first_name, "last_name": owner.last_name},
        "generated_on": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "total_bookings": len(bookings),
        "total_revenue": total_revenue,
        "average_price": average_price,
        "highest_price": highest_price,
        "lowest_price": lowest_price,
        "bookings": [
            {
                "property_name": booking.property.name,
                "property_id": booking.property.id,
                "location": booking.property.location,
                "rooms": booking.property.rooms,
                "price": booking.property.price,
                "booking_id": booking.id,
                "start_date": booking.start_date,
                "end_date": booking.end_date,
                "status": booking.status.value,
            }
            for booking in bookings
        ],
    }

    # Render the HTML content
    html_content = template.render(report_data)

    # Convert HTML content to PDF
    if not os.path.exists("reports"):
        os.makedirs("reports")
    pdf_file_path = f"reports/owner_report_{owner.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    HTML(string=html_content).write_pdf(pdf_file_path)

    return pdf_file_path


async def generate_booking_report(db: AsyncSession, message: str, booking) -> str:
    # Set up the Jinja2 environment
    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("booking_report.html")

    # Prepare data for the template
    report_data = {
        "booking": booking,
        "property_name": booking.property.name,
        "property_id": booking.property_id,
        "location": booking.property.location,
        "rooms": booking.property.rooms,
        "price": booking.property.price,
        "booking_id": booking.id,
        "start_date": booking.start_date,
        "end_date": booking.end_date,
        "status": booking.status.value,
        "message": message,
        "owner": {
            "first_name": booking.property.owner.first_name,
            "last_name": booking.property.owner.last_name
        },
        "user": {
            "first_name": booking.user.first_name,
            "last_name": booking.user.last_name,
            "email": booking.user.email
        },
        "generated_on": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Render the HTML content
    html_content = template.render(report_data)

    # Convert HTML content to PDF
    if not os.path.exists("reports"):
        os.makedirs("reports")
    pdf_file_path = f"reports/booking_report_{booking.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    HTML(string=html_content).write_pdf(pdf_file_path)

    return pdf_file_path


async def generate_user_activity_report(db: AsyncSession, user: User) -> str:
    # Fetch bookings for the user
    bookings = await get_bookings(db, user)

    if not bookings:
        raise HTTPException(status_code=404, detail="No bookings found for the user.")

    # Set up the Jinja2 environment
    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("user_activity_report.html")

    # Calculate additional metrics
    total_revenue = sum(Decimal(booking.property.price) for booking in bookings)
    average_price = (total_revenue / Decimal(len(bookings))).quantize(Decimal('0.01')) if bookings else Decimal('0.00')
    highest_price = max(Decimal(booking.property.price) for booking in bookings) if bookings else Decimal('0.00')
    lowest_price = min(Decimal(booking.property.price) for booking in bookings) if bookings else Decimal('0.00')

    # Prepare data for the template
    report_data = {
        "user": {"first_name": user.first_name, "last_name": user.last_name},
        "generated_on": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "total_bookings": len(bookings),
        "total_revenue": total_revenue,
        "average_price": average_price,
        "highest_price": highest_price,
        "lowest_price": lowest_price,
        "bookings": [
            {
                "booking_id": booking.id,
                "property_name": booking.property.name,
                "start_date": booking.start_date,
                "end_date": booking.end_date,
                "price": booking.property.price,
                "status": booking.status.value,
            }
            for booking in bookings
        ],
    }

    # Render the HTML content
    html_content = template.render(report_data)

    # Convert HTML content to PDF
    if not os.path.exists("reports"):
        os.makedirs("reports")
    pdf_file_path = f"reports/user_activity_report_{user.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    HTML(string=html_content).write_pdf(pdf_file_path)

    return pdf_file_path