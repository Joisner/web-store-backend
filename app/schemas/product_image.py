from pydantic import BaseModel, HttpUrl
from typing import Optional

class ProductImageBase(BaseModel):
    url: HttpUrl
    alt: Optional[str] = None
    display_order: Optional[int] = 0
    is_main: Optional[bool] = False

class ProductImageCreate(ProductImageBase):
    pass

class ProductImageUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    alt: Optional[str] = None
    display_order: Optional[int] = None
    is_main: Optional[bool] = None

class ProductImage(ProductImageBase):
    id: int
    product_id: int # Ensure this is present if you need to expose it

    class Config:
        from_attributes = True
