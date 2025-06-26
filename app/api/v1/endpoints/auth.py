from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # For standard form login
from sqlalchemy.orm import Session

from app import schemas # Import all schemas from the __init__
from app.services import user_service # Import the instantiated service
from app.core import security # For token creation and password hashing
from app.core.config import settings
from app.db.session import get_db
from app.api import dependencies # For getting current user

router = APIRouter()

@router.post("/login/access-token", response_model=schemas.Token)
async def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends() # Standard OAuth2 form
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Uses email as username.
    """
    user = user_service.authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # Correct status for failed login
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user_service.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = security.create_refresh_token(
        subject=user.email, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }

@router.post("/token/refresh", response_model=schemas.Token)
async def refresh_access_token(
    refresh_token_data: schemas.RefreshToken, # Expect a JSON body with "refresh_token"
    db: Session = Depends(get_db)
):
    """
    Refresh an access token using a refresh token.
    """
    token_payload = security.decode_token(refresh_token_data.refresh_token)
    if not token_payload or token_payload.sub is None: # or getattr(token_payload, 'type', None) != 'refresh': # Optional: check type claim
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_service.get_by_email(db, email=token_payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token, user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user_service.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = security.create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        # Optionally, you could issue a new refresh token here as well
        # "refresh_token": security.create_refresh_token(subject=user.email)
    }


@router.post("/register", response_model=schemas.User)
async def register_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Create new user.
    """
    # The user_service.create method already handles checking for existing email
    # and raises HTTPException if user exists.
    try:
        new_user = user_service.create(db, obj_in=user_in)
        return new_user
    except HTTPException as e:
        # Re-raise the HTTPException from the service layer
        raise e
    except Exception as e:
        # Catch any other unexpected errors during user creation
        # Log error e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user registration."
        )

@router.get("/me", response_model=schemas.User)
async def read_users_me(
    current_user: schemas.User = Depends(dependencies.get_current_active_user)
):
    """
    Get current user.
    """
    return current_user

@router.post("/change-password", summary="Change password for current user")
def change_password(
    new_password: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(dependencies.get_current_active_user),
):
    if not new_password or len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters."
        )
    user_service.update(
        db,
        db_obj=current_user,
        obj_in={"password": new_password}
    )
    return {"msg": "Password updated successfully"}
