from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.booking import BookingCreate, Booking, BookingUpdate, PersonalizedOffer
from app.crud import booking as booking_crud
from app.core.database import get_db
from app.dependencies import get_current_user, role_required, check_not_blocked
from app.enums.user_role import Role
from typing import List
from app.email_utils import send_email_task
from app.reports import generate_owner_report, generate_booking_report
from app.models.user import User

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
)


@router.get("/personalized-offers", response_model=List[PersonalizedOffer])
async def get_personalized_offers(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(role_required([Role.USER])),
    _: User = Depends(check_not_blocked),
):
    # Fetch personalized offers for the current user
    return await booking_crud.get_personalized_offers(db, current_user)


@router.post("/", response_model=Booking)
async def create_new_booking(
    booking: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(role_required([Role.USER])),
    _: User = Depends(check_not_blocked),
):
    # Create a new booking
    new_booking = await booking_crud.create_booking(db, booking, current_user)
    owner = new_booking.property.owner
    property = new_booking.property
    message = f"Your property {property.name} has been booked."
    report_path = await generate_booking_report(db, message=message, booking=new_booking)
    send_email_task.delay(
        email_to=owner.email,
        subject="New Booking",
        body=f"Your property {property.name} has been booked.",
        attachment_path=report_path,
    )
    return new_booking


@router.get("/", response_model=List[Booking])
async def read_bookings(
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    return await booking_crud.get_bookings(db, current_user)


@router.get("/{booking_id}", response_model=Booking)
async def read_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await booking_crud.get_booking(db, booking_id, current_user)


@router.put("/{booking_id}", response_model=Booking)
async def update_booking_details(
    booking_id: int,
    booking: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _: User = Depends(check_not_blocked),
):
    # Update booking details
    updated_booking = await booking_crud.update_booking(db, booking_id, booking, current_user)
    owner = updated_booking.property.owner
    property = updated_booking.property
    message = f"Your property {property.name} booking has been updated."
    report_path = await generate_booking_report(db, message=message, booking=updated_booking)
    send_email_task.delay(
        email_to=owner.email,
        subject="Booking Updated",
        body=f"Your property {property.name} booking has been updated.",
        attachment_path=report_path,
    )
    return updated_booking


@router.delete("/{booking_id}", response_model=Booking)
async def delete_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _: User = Depends(check_not_blocked),
):
    # Delete a booking
    deleted_booking = await booking_crud.delete_booking(db, booking_id, current_user)
    owner = deleted_booking.property.owner
    property = deleted_booking.property
    message = f"Your property {property.name} booking has been canceled."
    report_path = await generate_booking_report(db, message=message, booking=deleted_booking)
    send_email_task.delay(
        email_to=owner.email,
        subject="Booking Canceled",
        body=f"Your property {property.name} booking has been canceled.",
        attachment_path=report_path,
    )
    return deleted_booking


@router.post("/send-owner-report", response_model=dict)
async def send_owner_report(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(role_required([Role.OWNER])),
):
    report_path = await generate_owner_report(db, current_user)
    send_email_task.delay(current_user.email, "Your Booking Report", "Please find the attached report.", report_path)
    return {"message": "Report sent successfully"}
