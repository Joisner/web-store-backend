from pydantic import BaseModel, HttpUrl, conint, confloat
from typing import Optional, List, Any, Dict, Literal
from datetime import datetime
from .category import CategorySimple as ProductCategorySchema # Use simple category for product
from .product_image import ProductImageCreate, ProductImageUpdate, ProductImage as ProductImageSchema
from .product_variant import ProductVariantCreate, ProductVariantUpdate, ProductVariant as ProductVariantSchema
# StockHistory schemas are usually for internal use or specific endpoints, not directly embedded in full Product GET
# from .stock_history import StockHistory as StockHistorySchema

# Enums matching the model definitions
ProductStatus = Literal["active", "inactive", "draft"]
ProductVisibility = Literal["public", "private", "catalog"]

# Schemas for JSON fields (Discounts, CustomerPricing)
# These are based on the Angular interfaces.
class DiscountSchema(BaseModel):
    id: Optional[int] = None # Might be managed by frontend or not stored if simple
    type: Literal["percentage", "fixed"]
    value: confloat(gt=0) # type: ignore
    start_date: Optional[datetime] = None # Changed from string to datetime
    end_date: Optional[datetime] = None   # Changed from string to datetime
    is_active: Optional[bool] = True
    min_quantity: Optional[conint(ge=1)] = None # type: ignore

class CustomerPricingSchema(BaseModel):
    customer_type: Literal["retail", "wholesale", "vip"]
    price: confloat(gt=0) # type: ignore
    min_quantity: conint(ge=1) # type: ignore


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    sku: str
    barcode: Optional[str] = None
    category_id: int

    tags: Optional[List[str]] = []

    base_price: confloat(ge=0) # type: ignore
    sale_price: Optional[confloat(ge=0)] = None # type: ignore
    cost_price: Optional[confloat(ge=0)] = None # type: ignore

    stock: conint(ge=0) = 0 # type: ignore
    reserved_stock: Optional[conint(ge=0)] = 0 # type: ignore
    low_stock_threshold: Optional[conint(ge=0)] = 0 # type: ignore
    track_inventory: bool = True
    allow_backorder: bool = False

    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: str # Should be unique, usually auto-generated from name if not provided
    keywords: Optional[List[str]] = []
    og_image: Optional[HttpUrl] = None

    status: ProductStatus = "draft"
    visibility: ProductVisibility = "private"
    featured: bool = False

    # JSON fields
    discounts_json: Optional[List[DiscountSchema]] = []
    customer_pricing_json: Optional[List[CustomerPricingSchema]] = []


class ProductCreate(ProductBase):
    # For creation, we might want to accept image and variant data directly
    images: Optional[List[ProductImageCreate]] = []
    variants: Optional[List[ProductVariantCreate]] = []
    # created_by_user_id will be set by the service based on current user

class ProductUpdate(BaseModel):
    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None

    tags: Optional[List[str]] = None

    base_price: Optional[confloat(ge=0)] = None # type: ignore 
    sale_price: Optional[confloat(ge=0)] = None # type: ignore
    cost_price: Optional[confloat(ge=0)] = None # type: ignore

    stock: Optional[conint(ge=0)] = None # type: ignore
    reserved_stock: Optional[conint(ge=0)] = None # type: ignore
    low_stock_threshold: Optional[conint(ge=0)] = None # type: ignore
    track_inventory: Optional[bool] = None
    allow_backorder: Optional[bool] = None

    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    keywords: Optional[List[str]] = None
    og_image: Optional[HttpUrl] = None

    status: Optional[ProductStatus] = None
    visibility: Optional[ProductVisibility] = None
    featured: Optional[bool] = None

    discounts_json: Optional[List[DiscountSchema]] = None
    customer_pricing_json: Optional[List[CustomerPricingSchema]] = None

    # For updating images/variants, it's often better to have separate endpoints
    # e.g., POST /products/{id}/images, PUT /products/{id}/variants/{variant_id}
    # However, if simple replacement is okay for variants/images:
    # images: Optional[List[Union[ProductImageUpdate, ProductImageCreate]]] = None
    # variants: Optional[List[Union[ProductVariantUpdate, ProductVariantCreate]]] = None


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[int] = None
    last_modified_by_user_id: Optional[int] = None

    category: ProductCategorySchema # Embed category details
    images: List[ProductImageSchema] = []
    variants: List[ProductVariantSchema] = []
    # stock_histories: List[StockHistorySchema] = [] # Typically not included in main product GET

    class Config:
        from_attributes = True


# For paginated product lists
class ProductPaginated(BaseModel):
    total: int
    items: List[Product]
    page: int
    size: int
    # pages: int # Optional: total pages

Product.model_rebuild() # If there are forward refs that need resolving, like with Category
