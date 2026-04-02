from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.user import User
from app.services.auth import decode_access_token

# This tells FastAPI to look for "Authorization: Bearer <token>" header
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.

    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_db)):

    How it works:
    1. Request comes in → FastAPI calls get_db()
    2. get_db() opens a session from the pool
    3. Your route uses the session
    4. After your route returns → "finally" closes the session back to the pool

    "yield" makes this a generator — code before yield runs at start,
    code after yield runs at end (like a context manager).
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts + validates the JWT and returns the user.

    Usage in a route:
        async def my_route(user: User = Depends(get_current_user)):

    The chain:
    1. Client sends: Authorization: Bearer eyJhbGciOi...
    2. HTTPBearer extracts the token string
    3. We decode it → get user_id
    4. We fetch the user from DB
    5. Route receives the full User object

    If anything fails → 401 Unauthorized
    """
    # Decode the JWT
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Get user_id from token payload
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
