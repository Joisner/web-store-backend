from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenData
from app.services.user_service import user_service

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)

def get_current_user_token(token: str = Depends(reusable_oauth2)) -> Optional[TokenData]:
    """
    Decodes the JWT token.
    Raises HTTPException if token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenData(**payload)
        return token_data
    except (JWTError, ValidationError) as e:
        # Log the error e
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

def get_current_user(
    db: Session = Depends(get_db), token_data: TokenData = Depends(get_current_user_token)
) -> User:
    """
    Get the current user from the database based on the token's subject (email).
    Raises HTTPException if user not found.
    """
    if token_data.sub is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token subject is missing",
        )
    user = user_service.get_by_email(db, email=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    Raises HTTPException if the user is inactive.
    """
    if not user_service.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Dependency for superuser/admin (example)
# def get_current_active_superuser(
#     current_user: User = Depends(get_current_active_user),
# ) -> User:
#     """
#     Get the current active superuser.
#     Raises HTTPException if the user is not a superuser.
#     """
#     if not user_service.is_superuser(current_user):
#         raise HTTPException(
#             status_code=403, detail="The user doesn't have enough privileges"
#         )
#     return current_user

# Dependency for optional user (if token is provided, get user, else None)
async def get_optional_current_user(
    db: Session = Depends(get_db), token: Optional[str] = Depends(reusable_oauth2)
) -> Optional[User]:
    if not token:
        return None
    try:
        token_data = get_current_user_token(token) # This itself can raise HTTPException
        if token_data and token_data.sub:
            user = user_service.get_by_email(db, email=token_data.sub)
            return user
    except HTTPException as e:
        # If token is invalid (e.g. expired, malformed), treat as no user
        if e.status_code == status.HTTP_403_FORBIDDEN or e.status_code == status.HTTP_401_UNAUTHORIZED : # Adjust as per get_current_user_token's exceptions
             return None
        raise # Re-raise other HTTPExceptions (e.g. user not found if token was valid but user deleted)
    return None
