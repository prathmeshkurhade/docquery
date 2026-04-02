import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """What the user sends to POST /auth/register"""
    email: str          # we validate format manually (EmailStr needs email-validator pkg)
    password: str       # plaintext — we hash it before storing


class LoginRequest(BaseModel):
    """What the user sends to POST /auth/login"""
    email: str
    password: str


class TokenResponse(BaseModel):
    """What we return after login — the JWT token"""
    access_token: str
    token_type: str = "bearer"   # tells the client to send it as "Bearer <token>"


class UserResponse(BaseModel):
    """What we return when the client asks 'who am I?' — never includes password"""
    id: uuid.UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
    # from_attributes=True lets Pydantic read from SQLAlchemy objects
    # e.g. UserResponse.model_validate(user_db_object) just works
