from fastapi import APIRouter, Depends, HTTPException, status
from app.crud import user as user_crud
from app.crud import notification as notification_crud
from app.schemas.user import UserCreate, User, UserUpdate, UserBase
from app.schemas.notification import NotificationCreate
from app.core.database import get_db
from app.dependencies import role_required, get_current_user, check_not_blocked
from sqlalchemy.ext.asyncio import AsyncSession
from app.enums.user_role import Role
from app.reports import generate_user_activity_report
from app.email_utils import send_email_task

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/{user_id}/activity_report", response_model=str)
async def get_user_activity_report(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required([Role.ADMIN])),
):
    """Generate and send user activity report to admin."""
    # Fetch the user from the database
    user = await user_crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate the report
    report_path = await generate_user_activity_report(db, user)

    # Send the report to the admin's email
    admin_email = current_user.email
    subject = f"User Activity Report for {user.first_name} {user.last_name}"
    body = f"Please find attached the activity report for user {user.first_name} {user.last_name}."
    send_email_task.delay(admin_email, subject, body, report_path)

    return "Report has been sent to your email."


@router.get("/me", response_model=User)
async def read_current_user(current_user: User = Depends(check_not_blocked)):
    """Retrieve the current authenticated user."""
    return current_user


@router.post("/", response_model=User)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user."""
    # Prevent creation of admin users
    if user.role == Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to create an admin user.",
        )

    new_user = await user_crud.create_user(db, user)

    # Welcome notification for new user
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=new_user.id,
            message=f"Welcome to Smart Booking, {new_user.first_name}! Your account has been created successfully.",
            type="success",
        ),
    )

    return new_user


@router.post("/admin", response_model=User)
async def create_admin_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required([Role.ADMIN])),
):
    """Create a new admin user."""
    new_admin = await user_crud.create_user(db, user)

    # Notification for new admin
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=new_admin.id,
            message=f"Welcome to Smart Booking Admin, {new_admin.first_name}! Your admin account has been created.",
            type="success",
        ),
    )

    return new_admin


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_not_blocked),
):
    """Update a user."""
    # Update user details in the database
    updated_user = await user_crud.update_user(db, user_id, user, current_user)

    # Notification for profile update
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=updated_user.id,
            message="Your profile has been successfully updated.",
            type="info",
        ),
    )

    return updated_user


@router.delete("/{user_id}", response_model=User)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_not_blocked),
):
    """Delete a user."""
    # Delete user from the database
    deleted_user = await user_crud.delete_user(db, user_id, current_user)

    # Note: We can't send notification to deleted user, but we could notify admins
    # if needed in the future

    return deleted_user


@router.put("/{user_id}/block", response_model=User)
async def block_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required([Role.ADMIN])),
):
    """Block a user."""
    blocked_user = await user_crud.block_user(db, user_id)

    # Notification for blocked user
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=blocked_user.id,
            message="Your account has been temporarily blocked. Please contact support for assistance.",
            type="error",
        ),
    )

    return blocked_user


@router.put("/{user_id}/unblock", response_model=User)
async def unblock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required([Role.ADMIN])),
):
    """Unblock a user."""
    unblocked_user = await user_crud.unblock_user(db, user_id)

    # Notification for unblocked user
    await notification_crud.create_notification(
        db,
        NotificationCreate(
            user_id=unblocked_user.id,
            message="Your account has been unblocked. Welcome back to Smart Booking!",
            type="success",
        ),
    )

    return unblocked_user


@router.get("/{user_id}/activity_report", response_model=str)
async def get_user_activity_report(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required([Role.ADMIN])),
):
    """Generate and send user activity report to admin."""
    user = await user_crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    report_path = await generate_user_activity_report(db, user)
    return report_path
