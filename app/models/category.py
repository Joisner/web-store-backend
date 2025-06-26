from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Category(Base):
    __tablename__ = "categories" # Explicitly define table name

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True) # Self-referential, corrected table name
    color = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    parent = relationship("Category", remote_side=[id], back_populates="subcategories") # Corrected back_populates
    subcategories = relationship("Category", back_populates="parent") # For easier querying of children

    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', slug='{self.slug}')>"

