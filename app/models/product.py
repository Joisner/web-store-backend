from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey,
    JSON, Enum as SQLAlchemyEnum
)
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import datetime

class Product(Base):
    __tablename__ = "products" # Explicitly define table name

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    barcode = Column(String(100), nullable=True, index=True)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False) # Corrected ForeignKey
    category = relationship("Category", back_populates="products")

    tags = Column(JSON, nullable=True)

    base_price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=True)
    cost_price = Column(Float, nullable=True)

    stock = Column(Integer, default=0)
    reserved_stock = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=0)
    track_inventory = Column(Boolean, default=True)
    allow_backorder = Column(Boolean, default=False)

    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    keywords = Column(JSON, nullable=True)
    og_image = Column(String(255), nullable=True)

    status = Column(SQLAlchemyEnum("active", "inactive", "draft", name="product_status_enum"), default="draft", nullable=False)
    visibility = Column(SQLAlchemyEnum("public", "private", "catalog", name="product_visibility_enum"), default="private", nullable=False)
    featured = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.now) # Changed to .now
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now) # Changed to .now

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    last_modified_by_user = relationship("User", foreign_keys=[last_modified_by_user_id])

    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    stock_histories = relationship("StockHistory", back_populates="product", cascade="all, delete-orphan")

    discounts_json = Column(JSON, name="discounts", nullable=True)
    customer_pricing_json = Column(JSON, name="customer_pricing", nullable=True)


    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"
