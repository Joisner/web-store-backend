# Import all models here to ensure they are registered with SQLAlchemy's metadata
from .user import User
from .category import Category
from .product import Product, ProductVariant
from .product_image import ProductImage
from .stock_history import StockHistory

# This makes it easier to import all models via `from app.models import *`
# or ensure they are all known to Base.metadata
# or ensure they are all known to Base.metadata
