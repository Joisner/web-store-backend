from pydantic import BaseModel, conint
from typing import Optional, Literal
from datetime import datetime

StockHistoryType = Literal["adjustment", "sale", "purchase", "return"]

class StockHistoryBase(BaseModel):
    type: StockHistoryType
    quantity: int # Represents the change in stock, can be positive or negative
    previous_stock: int
    new_stock: int
    reason: Optional[str] = None
    user_name: Optional[str] = None # Snapshot of user name who performed action

class StockHistoryCreate(StockHistoryBase):
    product_id: int
    user_initiator_id: Optional[int] = None # Link to user who initiated
    date: Optional[datetime] = None # Will default to now in the model if not provided

class StockHistory(StockHistoryBase):
    id: int
    product_id: int
    user_initiator_id: Optional[int] = None
    date: datetime

    class Config:
        from_attributes = True
