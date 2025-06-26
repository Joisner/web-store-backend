from pydantic import BaseModel
from typing import Optional, Literal

# Literal type for variant types, matching the model
VariantType = Literal["size", "color", "material", "style"]

class ProductVariantBase(BaseModel):
    name: str # e.g., "Color", "Size"
    type: VariantType
    value: str # e.g., "Red", "XL"
    sku: Optional[str] = None # Can be auto-generated or provided
    price_override: Optional[float] = None # If set, overrides product price for this variant
    stock: int = 0
    image: Optional[str] = None # URL to variant-specific image

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariantUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[VariantType] = None
    value: Optional[str] = None
    sku: Optional[str] = None
    price_override: Optional[float] = None
    stock: Optional[int] = None
    image: Optional[str] = None

class ProductVariant(ProductVariantBase):
    id: int
    product_id: int # Ensure this is present

    class Config:
        from_attributes = True
