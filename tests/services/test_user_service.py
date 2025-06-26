import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services import user_service
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User
from app.core.security import verify_password

def test_create_user(db: Session, faker_instance):
    email = faker_instance.email()
    password = faker_instance.password(length=10)
    name = faker_instance.name()
    user_in = UserCreate(email=email, password=password, name=name)

    created_user = user_service.create(db, obj_in=user_in)

    assert created_user is not None
    assert created_user.email == email
    assert created_user.name == name
    assert hasattr(created_user, "hashed_password")
    assert verify_password(password, created_user.hashed_password)
    assert created_user.role == "Usuario" # Default role
    assert created_user.status == "active" # Default status

    # Verify in DB
    user_from_db = db.query(User).filter(User.id == created_user.id).first()
    assert user_from_db is not None
    assert user_from_db.email == email

def test_create_user_duplicate_email(db: Session, faker_instance):
    email = faker_instance.email()
    password = faker_instance.password()
    user_in_1 = UserCreate(email=email, password=password, name=faker_instance.name())
    user_service.create(db, obj_in=user_in_1) # Create first user

    user_in_2 = UserCreate(email=email, password="anotherpassword", name="Another Name")
    with pytest.raises(HTTPException) as exc_info:
        user_service.create(db, obj_in=user_in_2)

    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail.lower()


def test_get_user_by_email(db: Session, faker_instance):
    email = faker_instance.email()
    user_in = UserCreate(email=email, password=faker_instance.password(), name=faker_instance.name())
    created_user = user_service.create(db, obj_in=user_in)

    retrieved_user = user_service.get_by_email(db, email=email)
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == email

    non_existent_user = user_service.get_by_email(db, email="nonexistent@example.com")
    assert non_existent_user is None


def test_authenticate_user(db: Session, faker_instance):
    email = faker_instance.email()
    password = "StrongPassword123!"
    user_in = UserCreate(email=email, password=password, name=faker_instance.name())
    user_service.create(db, obj_in=user_in)

    # Correct credentials
    authenticated_user = user_service.authenticate(db, email=email, password=password)
    assert authenticated_user is not None
    assert authenticated_user.email == email

    # Incorrect password
    wrong_pass_user = user_service.authenticate(db, email=email, password="wrongpassword")
    assert wrong_pass_user is None

    # Non-existent user
    non_existent_auth_user = user_service.authenticate(db, email="nobody@example.com", password="anypassword")
    assert non_existent_auth_user is None


def test_update_user(db: Session, faker_instance):
    email = faker_instance.email()
    password = faker_instance.password()
    user_in = UserCreate(email=email, password=password, name="Original Name")
    db_user = user_service.create(db, obj_in=user_in)

    update_data = UserUpdate(name="Updated Name", role="Editor", status="inactive")
    updated_user = user_service.update(db, db_obj=db_user, obj_in=update_data)

    assert updated_user.name == "Updated Name"
    assert updated_user.role == "Editor"
    assert updated_user.status == "inactive"
    assert updated_user.email == email # Email not changed in this update

    # Test password update
    new_password = "newSecurePassword321"
    update_pass_data = UserUpdate(password=new_password)
    user_after_pass_update = user_service.update(db, db_obj=updated_user, obj_in=update_pass_data)

    assert verify_password(new_password, user_after_pass_update.hashed_password)
    # Ensure old password no longer works
    assert not verify_password(password, user_after_pass_update.hashed_password)


def test_is_active(faker_instance):
    active_user = User(email=faker_instance.email(), name=faker_instance.name(), hashed_password="dummy", status="active")
    inactive_user = User(email=faker_instance.email(), name=faker_instance.name(), hashed_password="dummy", status="inactive")

    assert user_service.is_active(active_user) is True
    assert user_service.is_active(inactive_user) is False

# TODO: Add tests for other user_service methods if they are added, e.g.,
# - change_password
# - activate_user / deactivate_user
# - get_multi with filters (e.g., by role, by status)
# - remove user (CRUDBase.remove is used, but could test specific user deletion scenarios)
