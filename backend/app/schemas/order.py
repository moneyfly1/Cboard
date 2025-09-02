from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class OrderBase(BaseModel):
    user_id: int
    package_id: int
    amount: Decimal

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_method_id: Optional[int] = None
    payment_method_name: Optional[str] = None
    payment_time: Optional[datetime] = None
    payment_transaction_id: Optional[str] = None
    expire_time: Optional[datetime] = None

class OrderInDB(OrderBase):
    id: int
    order_no: str
    status: str
    payment_method_id: Optional[int] = None
    payment_method_name: Optional[str] = None
    payment_time: Optional[datetime] = None
    payment_transaction_id: Optional[str] = None
    expire_time: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Order(OrderInDB):
    pass

class OrderWithPackage(Order):
    package: "Package"  # 使用字符串引用避免循环导入 