from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserInDB
from app.core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        # Check if user already exists
        existing_user = self.get_by_email(db, email=obj_in.email)
        if existing_user:
            # Consider raising a more specific exception or returning a specific response
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists in the system.",
            )

        hashed_password = get_password_hash(obj_in.password)

        # Create a dictionary for user creation, excluding the plain password
        user_data = obj_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = hashed_password

        # Use the base class create method with the modified data
        # db_obj = self.model(**user_data) # This is what super().create does internally
        # return super().create(db, obj_in=db_obj) # This is not right, super().create expects CreateSchemaType

        # Correct approach:
        db_user = User(
            email=obj_in.email,
            hashed_password=hashed_password,
            name=obj_in.name,
            role=obj_in.role,
            status=obj_in.status,
            avatar=obj_in.avatar
            # created_at is handled by default in the model
        )

        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except Exception as e:
            db.rollback()
            # Log error e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create user."
            )


    def update(
        self,
        db: Session,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"] # Remove plain password from update_data
            update_data["hashed_password"] = hashed_password # Add hashed password

        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(
        self, db: Session, *, email: str, password: str
    ) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        # Validar que el hash no sea vacío o None
        if not user.hashed_password:
            return None
        try:
            if not verify_password(password, user.hashed_password):
                return None
        except Exception:
            # Si el hash no es válido, también retorna None
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.status == "active"

    # Example: Check if user is a superuser/admin (based on role)
    # def is_superuser(self, user: User) -> bool:
    #     return user.role == "Administrador" # Or whatever your admin role is named

    # You can add more user-specific methods here, e.g.,
    # - Change user password
    # - Activate/deactivate user
    # - Get all users with a specific role

user_service = CRUDUser(User)

# Exponer authenticate como función de módulo para compatibilidad con imports existentes
authenticate = user_service.authenticate
is_active = user_service.is_active
get_multi = user_service.get_multi
create = user_service.create
get = user_service.get
update = user_service.update
