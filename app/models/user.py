from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import datetime

class User(Base):
    __tablename__ = "users" # Explicitly define table name

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="Usuario") # e.g., "Administrador", "Editor", "Usuario"
    status = Column(SQLAlchemyEnum("active", "inactive", name="user_status_enum"), default="active")
    created_at = Column(DateTime, default=datetime.datetime.now) # Changed to .now for non-UTC if preferred
    avatar = Column(String(255), nullable=True)

    # Relationships
    # Products created by this user (example, if Product model has 'created_by_user_id')
    # products_created = relationship("Product", foreign_keys="[Product.created_by_user_id]", back_populates="created_by_user")

    # Stock history entries made by this user
    stock_histories = relationship("StockHistory", back_populates="user_initiator")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"
