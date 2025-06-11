from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.booking import BookingCreate, Booking, BookingUpdate, PersonalizedOffer
from app.crud import booking as booking_crud
from app.crud import notification as notification_crud
from app.core.database import get_db
from app.dependencies import get_current_user, role_required, check_not_blocked
from app.enums.user_role import Role
from typing import List
from app.email_utils import send_email_task
from app.reports import generate_owner_report, generate_booking_report
from app.models.user import User
from app.enums.booking_status import BookingStatus
from app.schemas.notification import NotificationCreate

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
    report_path = await generate_booking_report(
        db, message=message, booking=new_booking
    )
    send_email_task.delay(
        email_to=owner.email,
        subject="New Booking",
        body=f"Your property {property.name} has been booked.",
        attachment_path=report_path,
    )
    # Create notification for owner
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=owner.id,
            message=f"Your property '{property.name}' has been booked.",
            type="info",
        ),
    )
    # Create notification for guest
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=current_user.id,
            message=f"Your booking for '{property.name}' has been created!",
            type="success",
        ),
    )
    # Fetch the booking again with all relationships loaded
    booking_with_payment = await booking_crud.get_booking(
        db, new_booking.id, current_user
    )
    return booking_with_payment


@router.get("/", response_model=List[Booking])
async def read_bookings(
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    # Fetch all bookings for the current user
    return await booking_crud.get_bookings(db, current_user)


@router.get("/owner", response_model=List[Booking])
async def get_bookings_for_owner(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required([Role.OWNER])),
):
    return await booking_crud.get_owner_bookings(db, current_user.id)


@router.get("/{booking_id}", response_model=Booking)
async def read_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Fetch a booking by ID for the current user
    return await booking_crud.get_booking(db, booking_id, current_user)


@router.put("/{booking_id}", response_model=Booking)
async def update_booking_details(
    booking_id: int,
    booking: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _: User = Depends(check_not_blocked),
):
    updated_booking = await booking_crud.update_booking(
        db, booking_id, booking, current_user
    )
    # Notification for guest
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=current_user.id,
            message=f"Your booking for '{updated_booking.property.name}' has been updated.",
            type="info",
        ),
    )
    # Notification for owner
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=updated_booking.property.owner.id,
            message=f"A guest updated their booking for '{updated_booking.property.name}'.",
            type="info",
        ),
    )
    return updated_booking


@router.delete("/{booking_id}", response_model=Booking)
async def delete_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _: User = Depends(check_not_blocked),
):
    deleted_booking = await booking_crud.delete_booking(db, booking_id, current_user)
    # Notification for guest
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=current_user.id,
            message=f"Your booking for '{deleted_booking.property.name}' has been cancelled.",
            type="info",
        ),
    )
    # Notification for owner
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=deleted_booking.property.owner.id,
            message=f"A booking for your property '{deleted_booking.property.name}' was cancelled by the guest.",
            type="warning",
        ),
    )
    return deleted_booking


@router.post("/send-owner-report", response_model=dict)
async def send_owner_report(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(role_required([Role.OWNER])),
):
    # Generate and send a report to the owner
    report_path = await generate_owner_report(db, current_user)
    send_email_task.delay(
        current_user.email,
        "Your Booking Report",
        "Please find the attached report.",
        report_path,
    )
    return {"message": "Report sent successfully"}


@router.post("/{booking_id}/approve", response_model=Booking)
async def approve_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required([Role.OWNER])),
):
    """Approve a booking request."""
    # Get the booking
    booking = await booking_crud.get_booking(db, booking_id, current_user)

    # Check if the current user is the owner of the property
    if booking.property.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You are not authorized to approve this booking."
        )

    # Update the booking status to confirmed
    updated_booking = await booking_crud.update_booking(
        db, booking_id, BookingUpdate(status=BookingStatus.CONFIRMED), current_user
    )

    # Send email notification to the user
    message = f"Your booking for {booking.property.name} has been approved!"
    report_path = await generate_booking_report(
        db, message=message, booking=updated_booking
    )
    send_email_task.delay(
        email_to=booking.user.email,
        subject="Booking Approved",
        body=f"Your booking for {booking.property.name} has been approved!",
        attachment_path=report_path,
    )
    # Notification for guest
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=booking.user.id,
            message=f"Your booking for '{booking.property.name}' has been approved by the owner!",
            type="success",
        ),
    )
    # Notification for owner
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=current_user.id,
            message=f"You have approved a booking for '{booking.property.name}'.",
            type="success",
        ),
    )
    return updated_booking


@router.post("/{booking_id}/payment", response_model=Booking)
async def process_booking_payment(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Process payment logic here
    booking = await booking_crud.get_booking(db, booking_id, current_user)

    # Assume payment is successful
    updated_booking = await booking_crud.update_booking(
        db, booking_id, BookingUpdate(status=BookingStatus.PAID), current_user
    )

    # Reload the updated booking with all relationships
    updated_booking = await booking_crud.get_booking(db, booking_id, current_user)

    # Notification for guest
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=current_user.id,
            message=f"Your payment for '{updated_booking.property.name}' was successful. Booking confirmed!",
            type="success",
        ),
    )
    # Notification for owner
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=updated_booking.property.owner.id,
            message=f"Payment received for booking at '{updated_booking.property.name}'.",
            type="success",
        ),
    )
    # Notification for payment creation
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=current_user.id,
            message=f"Payment for '{updated_booking.property.name}' has been created.",
            type="info",
        ),
    )
    return updated_booking


@router.post("/{booking_id}/reject", response_model=Booking)
async def reject_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required([Role.OWNER])),
):
    booking = await booking_crud.get_booking(db, booking_id, current_user)
    if booking.property.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You are not authorized to reject this booking."
        )
    updated_booking = await booking_crud.update_booking(
        db, booking_id, BookingUpdate(status=BookingStatus.REJECTED), current_user
    )
    # Notification for guest
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=booking.user.id,
            message=f"Your booking for '{booking.property.name}' was rejected by the owner.",
            type="error",
        ),
    )
    # Notification for owner
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=current_user.id,
            message=f"You have rejected a booking for '{booking.property.name}'.",
            type="info",
        ),
    )
    return updated_booking


@router.get("/admin/all", response_model=List[Booking])
async def get_all_bookings_for_admin(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required([Role.ADMIN])),
):
    """Get all bookings in the system (admin only)."""
    return await booking_crud.get_all_bookings(db)
