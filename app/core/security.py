from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.token import TokenData # Assuming TokenData schema is defined

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"} # Add a type claim for refresh tokens
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def decode_token(token: str) -> Optional[TokenData]:
    """
    Decodes a JWT token and returns the payload as TokenData.
    Returns None if decoding fails or token is invalid/expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Validate payload against TokenData schema (optional but good practice)
        # This ensures 'sub' field exists, etc.
        token_data = TokenData(**payload)
        return token_data
    except (JWTError, ValidationError):
        # Could log the error here
        return None

# Example usage (for testing or other modules):
if __name__ == "__main__":
    # Hash a password
    password = "testpassword"
    hashed_pass = get_password_hash(password)
    print(f"Original: {password}, Hashed: {hashed_pass}")

    # Verify a password
    is_correct = verify_password(password, hashed_pass)
    print(f"Password verification correct: {is_correct}")
    is_incorrect = verify_password("wrongpassword", hashed_pass)
    print(f"Password verification incorrect: {is_incorrect}")

    # Create an access token
    user_id = "user123"
    access_token = create_access_token(subject=user_id)
    print(f"Access Token for {user_id}: {access_token}")

    # Decode a token
    decoded_payload = decode_token(access_token)
    if decoded_payload:
        print(f"Decoded Token Subject: {decoded_payload.sub}")
    else:
        print("Token decoding failed.")

    # Create a refresh token
    refresh_token = create_refresh_token(subject=user_id)
    print(f"Refresh Token for {user_id}: {refresh_token}")

    decoded_refresh_payload = decode_token(refresh_token)
    if decoded_refresh_payload:
        print(f"Decoded Refresh Token Subject: {decoded_refresh_payload.sub}, Type: {decoded_refresh_payload.type if hasattr(decoded_refresh_payload, 'type') else 'N/A'}") # Added type check for safety
    else:
        print("Refresh token decoding failed.")

    # Test expired token (manual simulation by setting short expiry)
    short_expiry_token = create_access_token(subject="test_expiry", expires_delta=timedelta(seconds=1))
    import time
    time.sleep(2) # Wait for token to expire
    decoded_expired_payload = decode_token(short_expiry_token)
    if decoded_expired_payload:
        print(f"Decoded Expired Token (should not happen): {decoded_expired_payload.sub}")
    else:
        print("Expired token decoding failed as expected.")
