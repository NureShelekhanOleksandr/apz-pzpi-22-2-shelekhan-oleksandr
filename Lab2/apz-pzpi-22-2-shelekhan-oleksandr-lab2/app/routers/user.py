from fastapi import APIRouter, Depends, HTTPException, status
from app.crud import user as user_crud
from app.schemas.user import UserCreate, User, UserUpdate, UserBase
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


@router.get("/me", response_model=UserBase)
async def read_current_user(current_user: User = Depends(check_not_blocked)):
    """Retrieve the current authenticated user."""
    return current_user


@router.post("/", response_model=User)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user."""
    if user.role == Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to create an admin user.",
        )
    return await user_crud.create_user(db, user)


@router.post("/admin", response_model=User)
async def create_admin_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required([Role.ADMIN])),
):
    """Create a new admin user."""
    return await user_crud.create_user(db, user)


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_not_blocked),
):
    """Update a user."""
    return await user_crud.update_user(db, user_id, user, current_user)


@router.delete("/{user_id}", response_model=User)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_not_blocked),
):
    """Delete a user."""
    return await user_crud.delete_user(db, user_id, current_user)


@router.put("/{user_id}/block", response_model=User)
async def block_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required([Role.ADMIN])),
):
    """Block a user."""
    return await user_crud.block_user(db, user_id)


@router.put("/{user_id}/unblock", response_model=User)
async def unblock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required([Role.ADMIN])),
):
    """Unblock a user."""
    return await user_crud.unblock_user(db, user_id)


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
