from fastapi import APIRouter, Depends, HTTPException
from app.crud import user as user_crud
from app.core.database import get_db
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    tags=["login"],
)


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """Authenticate a user and return an access token."""
    user = await user_crud.authenticate_user(db, form_data.username, form_data.password)
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

