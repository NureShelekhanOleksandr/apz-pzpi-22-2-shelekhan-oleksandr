from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate, User
from sqlalchemy import select, delete
from app.core.security import get_password_hash, verify_password
from fastapi import HTTPException
from app.enums.user_role import Role


async def create_user(db: AsyncSession, user: UserCreate):
    """Create a new user.
    
    Hashes the user's password and creates a new user record in the database.
    
    Args:
        db (AsyncSession): The database session.
        user (UserCreate): The user data to create.
    
    Returns:
        UserModel: The created user.
    """
    user.password = get_password_hash(user.password)
    new_user = UserModel(**user.model_dump())
    db.add(new_user)
    await db.commit()
    return new_user


async def update_user(
    db: AsyncSession, user_id: int, user: UserUpdate, current_user: User
):
    """Update a user.
    
    Updates the user record in the database if the current user has permission.
    
    Args:
        db (AsyncSession): The database session.
        user_id (int): The ID of the user to update.
        user (UserUpdate): The updated user data.
        current_user (User): The current authenticated user.
    
    Returns:
        UserModel: The updated user.
    
    Raises:
        HTTPException: If the user is not found or the current user does not have permission.
    """
    if user_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=403, detail="You are not allowed to update this user."
        )
    query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(query)
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.password:
        user.password = get_password_hash(user.password)
    for key, value in user.model_dump(exclude_none=True).items():
        setattr(db_user, key, value)
    await db.commit()
    return db_user


async def delete_user(db: AsyncSession, user_id: int, current_user: User):
    """Delete a user.
    
    Deletes the user record from the database if the current user has permission.
    
    Args:
        db (AsyncSession): The database session.
        user_id (int): The ID of the user to delete.
        current_user (User): The current authenticated user.
    
    Returns:
        UserModel: The deleted user.
    
    Raises:
        HTTPException: If the user is not found or the current user does not have permission.
    """
    if user_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=403, detail="You are not allowed to delete this user."
        )
    query = delete(UserModel).where(UserModel.id == user_id).returning(UserModel)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_user(db: AsyncSession, user_id: int):
    """Retrieve a user by ID.
    
    Retrieves the user record from the database by user ID.
    
    Args:
        db (AsyncSession): The database session.
        user_id (int): The ID of the user to retrieve.
    
    Returns:
        UserModel: The retrieved user.
    
    Raises:
        HTTPException: If the user is not found.
    """
    query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str):
    """Authenticate a user by email and password.
    
    Authenticates the user by verifying the email and password.
    
    Args:
        db (AsyncSession): The database session.
        email (str): The user's email.
        password (str): The user's password.
    
    Returns:
        UserModel: The authenticated user.
    
    Raises:
        HTTPException: If the user is not found or the password is incorrect.
    """
    query = select(UserModel).where(UserModel.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    return user


async def block_user(db: AsyncSession, user_id: int):
    """Block a user.
    
    Blocks the user by setting the is_blocked attribute to True.
    
    Args:
        db (AsyncSession): The database session.
        user_id (int): The ID of the user to block.
    
    Returns:
        UserModel: The blocked user.
    
    Raises:
        HTTPException: If the user is not found.
    """
    query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_blocked = True
    await db.commit()
    return user


async def unblock_user(db: AsyncSession, user_id: int):
    """Unblock a user.
    
    Unblocks the user by setting the is_blocked attribute to False.
    
    Args:
        db (AsyncSession): The database session.
        user_id (int): The ID of the user to unblock.
    
    Returns:
        UserModel: The unblocked user.
    
    Raises:
        HTTPException: If the user is not found.
    """
    query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_blocked = False
    await db.commit()
    return user
