from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import datetime

class StockHistory(Base):
    __tablename__ = "stock_histories" # Explicitly define table name

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.now, nullable=False) # Changed to .now
    type = Column(SQLAlchemyEnum("adjustment", "sale", "purchase", "return", name="stock_history_type_enum"), nullable=False)
    quantity = Column(Integer, nullable=False) # 'quantity' from Angular, represents the change amount
    previous_stock = Column(Integer, nullable=False)
    new_stock = Column(Integer, nullable=False)
    reason = Column(String(500), nullable=True)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product", back_populates="stock_histories")

    # Changed user_id to user_initiator_id for clarity
    user_initiator_id = Column(Integer, ForeignKey("users.id"), nullable=True, name="user_id")
    user_initiator = relationship("User", back_populates="stock_histories")

    user_name = Column(String(255), nullable=True) # Storing user_name snapshot from Angular model

    def __repr__(self):
        return f"<StockHistory(id={self.id}, product_id={self.product_id}, type='{self.type}', quantity={self.quantity})>"
