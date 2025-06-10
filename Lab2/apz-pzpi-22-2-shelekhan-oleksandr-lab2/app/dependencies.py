from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.database import get_db
from app.core.security import decode_access_token
from app.crud import user as user_crud
from app.models.user import User
from app.enums.user_role import Role
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """Retrieve the current authenticated user."""
    payload = decode_access_token(token)
    id: str = payload.get("sub")
    if not id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    user = await user_crud.get_user(db, int(id))
    return user


async def check_not_blocked(current_user: User = Depends(get_current_user)):
    """Check if the current user is blocked."""
    if current_user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is blocked. Please contact support.",
        )
    return current_user


def role_required(required_roles: List[Role]):
    """Check if the user's role matches the required roles."""

    def role_dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            required_roles_str = ", ".join([role.value for role in required_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have the required role to access this resource. Required roles: {required_roles_str}",
            )
        return current_user

    return role_dependency