from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings

# --- Password Hashing ---
# bcrypt: slow on purpose — if someone steals your DB, they can't brute-force passwords


def hash_password(password: str) -> str:
    """
    "mypassword123" → "$2b$12$LJ3m4ys9Rn..." (60 chars, irreversible)

    Bcrypt adds a random salt automatically, so hashing the same password
    twice gives DIFFERENT hashes. This prevents rainbow table attacks.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Takes the plaintext password the user just typed in login,
    and the hash from the database. Returns True if they match.

    It does NOT decrypt the hash (that's impossible with bcrypt).
    It hashes the plain password with the same salt and compares.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# --- JWT Tokens ---

def create_access_token(user_id: str) -> str:
    """
    Creates a JWT token containing:
    - sub: the user's ID (who this token belongs to)
    - exp: when it expires (default 24 hours from now)
    - iat: when it was issued

    The token is SIGNED with JWT_SECRET, not encrypted.
    Anyone can decode and read the payload (don't put secrets in it).
    But only our server can CREATE valid tokens (because only we know the secret).
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)

    payload = {
        "sub": user_id,       # subject — who is this token for
        "exp": expire,        # expiration — after this, token is rejected
        "iat": now,           # issued at — when was this created
    }

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Takes a JWT token string, verifies the signature, checks expiration.
    Returns the payload dict if valid, None if invalid/expired.

    This is called on EVERY authenticated request:
    Request comes in → extract token from header → decode → get user_id → fetch user
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None
