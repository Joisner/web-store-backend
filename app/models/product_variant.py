from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ProductVariant(Base):
    __tablename__ = "product_variants" # Explicitly define table name

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(SQLAlchemyEnum("size", "color", "material", "style", name="variant_type_enum"), nullable=False)
    value = Column(String(100), nullable=False)
    sku = Column(String(150), nullable=True, unique=True) # Changed from sku_suffix to full sku for clarity, can be product_sku + suffix
    price_override = Column(Float, nullable=True) # If set, overrides product.sale_price or product.base_price for this variant
    stock = Column(Integer, default=0, nullable=False)
    image = Column(String(2048), nullable=True) # Renamed from image_url for consistency

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product", back_populates="variants")

    def __repr__(self):
        return f"<ProductVariant(id={self.id}, name='{self.name}', value='{self.value}', product_id={self.product_id})>"
