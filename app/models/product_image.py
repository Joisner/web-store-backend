from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ProductImage(Base):
    __tablename__ = "product_images" # Explicitly define table name

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False)
    alt = Column(String(255), nullable=True)
    display_order = Column(Integer, default=0) # Removed name="order" as it's not problematic here, but good practice to avoid SQL keywords
    is_main = Column(Boolean, default=False)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product", back_populates="images")

    def __repr__(self):
        return f"<ProductImage(id={self.id}, url='{self.url}', product_id={self.product_id})>"
