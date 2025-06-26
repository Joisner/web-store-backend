from pydantic import BaseModel
from typing import Optional

class ProductImageBase(BaseModel):
    url: str  # <-- Debe ser str, NO HttpUrl ni AnyUrl
    alt: Optional[str] = None
    display_order: Optional[int] = 0
    is_main: bool

class ProductImageCreate(ProductImageBase):
    pass

class ProductImage(BaseModel):
    id: int
    url: str
    alt: Optional[str] = None
    display_order: Optional[int] = 0
    is_main: bool
    product_id: int

    model_config = {
        "from_attributes": True
    }

class ProductImageUpdate(ProductImageCreate):
    pass
    product_id: int # Ensure this is present if you need to expose it

    class Config:
        from_attributes = True
