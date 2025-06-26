from pydantic import BaseModel
from typing import Optional, List

# Schema for Category creation
class CategoryCreate(BaseModel):
    name: str
    slug: str
    parent_id: Optional[int] = None
    color: Optional[str] = None
    description: Optional[str] = None

# Schema for Category update - all fields are optional
class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[int] = None
    color: Optional[str] = None
    description: Optional[str] = None

# Base schema for Category, used for reading/returning category data
class CategoryBase(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: Optional[int] = None
    color: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True # Replaces orm_mode = True in Pydantic v2

# Schema for a Category including its subcategories (recursive)
class Category(CategoryBase):
    subcategories: List['Category'] = [] # Recursive definition

# Required for Pydantic v2 to handle recursive models
Category.model_rebuild()


# Schema for Category without subcategories, useful for product listings
class CategorySimple(CategoryBase):
    pass
