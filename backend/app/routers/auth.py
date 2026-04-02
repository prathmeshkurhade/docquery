from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import create_access_token, hash_password, verify_password
from app.utils.deps import get_current_user, get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.

    Flow:
    1. Check if email already taken
    2. Hash the password (never store plaintext)
    3. Create user in DB
    4. Return user info (without password)
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user with hashed password
    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)  # reload from DB to get id + created_at

    return user


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login and get a JWT token.

    Flow:
    1. Find user by email
    2. Verify password against stored hash
    3. Create JWT token with user_id
    4. Return token
    """
    # Find user
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(request.password, user.hashed_password):
        # Same error for "user not found" and "wrong password"
        # Why? So attackers can't figure out which emails exist
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create token
    token = create_access_token(str(user.id))

    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """
    Get current user info. Requires authentication.

    This is the simplest authenticated endpoint — it just returns
    the user object that get_current_user already fetched.
    """
    return user
