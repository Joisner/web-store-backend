# Import all schemas here for easier access
from typing import Literal # Imported here if used directly in schemas like user.py

# Token Schemas
from .token import Token, TokenData, RefreshToken

# User Schemas
from .user import User, UserCreate, UserUpdate, UserLogin, UserInDB, UserStatus

# Category Schemas
from .category import Category, CategoryCreate, CategoryUpdate, CategorySimple

# Product Image Schemas
from .product_image import ProductImage, ProductImageCreate  # Elimina ProductImageUpdate si no existe

# Product Variant Schemas
from .product_variant import ProductVariant, ProductVariantCreate, ProductVariantUpdate, VariantType

# Stock History Schemas
from .stock_history import StockHistory, StockHistoryCreate, StockHistoryType

# Product Schemas
from .product import (
    Product,
    ProductCreate,
    ProductUpdate,
    ProductPaginated,
    DiscountSchema,
    CustomerPricingSchema,
    ProductStatus, # This is a Literal type
    ProductVisibility # This is a Literal type
)

# This makes it easier to import schemas from app.schemas.MySchema
# instead of app.schemas.my_module.MySchema

# Re-export Literal types if they are defined in individual schema files
# and you want them available directly from app.schemas
# For example, if ProductStatus is defined in product.py:
# from .product import ProductStatus
