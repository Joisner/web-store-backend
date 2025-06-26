from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import schemas # Use __init__ for schema imports
from app.services import user_service
from app.db.session import get_db
from app.api import dependencies
from app.models.user import User as UserModel # UserModel to avoid conflict with schema.User

router = APIRouter()

# Note: User creation is handled by the /auth/register endpoint.
# This router will focus on reading, updating, and deleting users, typically by admins.

@router.get(
    "/",
    response_model=List[schemas.User],
    dependencies=[Depends(dependencies.get_current_active_user)] # Protect this route
    # dependencies=[Depends(dependencies.get_current_active_superuser)] # Or for superuser only
)
async def read_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200), # Max 200 users per page
    current_user: UserModel = Depends(dependencies.get_current_active_user) # For authorization if needed
):
    """
    Retrieve users.
    Requires authentication. Only admins should typically access this.
    (Further authorization based on current_user.role can be added).
    """
    # Example authorization:
    # if not user_service.is_superuser(current_user):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    users = user_service.get_multi(db, skip=skip, limit=limit)
    return users

@router.get(
    "/{user_id}",
    response_model=schemas.User,
    dependencies=[Depends(dependencies.get_current_active_user)] # Protect
)
async def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user) # For authorization
):
    """
    Get a specific user by ID.
    Requires authentication. User can get their own info, or admin can get any.
    """
    # Example authorization:
    # if user_id != current_user.id and not user_service.is_superuser(current_user):
    #     raise HTTPException(status_code=403, detail="Not enough permissions to view this user")

    user = user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put(
    "/{user_id}",
    response_model=schemas.User,
    dependencies=[Depends(dependencies.get_current_active_user)] # Protect
)
async def update_user_by_id(
    user_id: int,
    user_in: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user) # For authorization
):
    """
    Update a user.
    Requires authentication. User can update their own info, or admin can update any.
    """
    user = user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Example authorization:
    # if user_id != current_user.id and not user_service.is_superuser(current_user):
    #     raise HTTPException(status_code=403, detail="Not enough permissions to update this user")

    # Prevent non-admins from changing roles or critical fields if current_user is not admin
    # if not user_service.is_superuser(current_user):
    #     if user_in.role is not None and user_in.role != user.role:
    #         raise HTTPException(status_code=403, detail="Cannot change user role")
    #     # Add other restricted field checks here

    # Check for email conflict if email is being changed
    if user_in.email and user_in.email != user.email:
        existing_user = user_service.get_by_email(db, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered by another user.")

    updated_user = user_service.update(db, db_obj=user, obj_in=user_in)
    return updated_user


@router.delete(
    "/{user_id}",
    response_model=schemas.User, # O un mensaje de éxito
    dependencies=[Depends(dependencies.get_current_active_user)] # Protegido
    # dependencies=[Depends(dependencies.get_current_active_superuser)] # Solo admin si lo deseas
)
async def deactivate_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user)
):
    """
    Deactivate a user (soft delete).
    Changes user status to 'inactive' instead of deleting from DB.
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate currently logged-in user via this endpoint.")

    user_to_deactivate = user_service.get(db, id=user_id)
    if not user_to_deactivate:
        raise HTTPException(status_code=404, detail="User not found")

    # Cambia el estado a 'inactive'
    updated_user = user_service.update(db, db_obj=user_to_deactivate, obj_in={"status": "inactive"})
    return updated_user


@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(dependencies.get_current_active_user),  # Requiere autenticación
):
    """
    Create a new user with name, email, role, status, and password.
    Requires authentication.
    """
    try:
        user = user_service.create(db, obj_in=user_in)
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error creating user:", e)  # <--- Agrega esta línea para depuración
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user."
        )
        print("Error creating user:", e)  # <--- Agrega esta línea para depuración
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user."
        )
