from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime

# Enum for user status, matching the model
UserStatus = Literal["active", "inactive"]

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    name: Optional[str] = Field(None, example="John Doe")
    role: Optional[str] = Field("Usuario", example="Administrador") # Default role
    status: Optional[UserStatus] = "active"
    avatar: Optional[str] = Field(None, example="https://example.com/avatar.png")

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="aSecurePassword123")

# Properties to receive via API on update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, example="user@example.com")
    name: Optional[str] = Field(None, example="John Doe")
    password: Optional[str] = Field(None, min_length=8, example="aNewSecurePassword123")
    role: Optional[str] = Field(None, example="Editor")
    status: Optional[UserStatus] = None
    avatar: Optional[str] = Field(None, example="https://example.com/new_avatar.png")


# Properties stored in DB (hashed_password instead of password)
class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    # hashed_password: str # This should not be exposed in API responses directly

    class Config:
        from_attributes = True

# Additional properties to return to API (excluding sensitive data like hashed_password)
class User(UserInDBBase):
    pass # Inherits all fields from UserInDBBase, effectively what we return


# Schema for user login
class UserLogin(BaseModel):
    username: EmailStr # Using email as username
    password: str

# Schema for user stored in DB, including hashed_password (for internal use)
class UserInDB(UserInDBBase):
    hashed_password: str
