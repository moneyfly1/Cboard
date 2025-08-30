from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class PackageBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    duration_days: int
    device_limit: int = 3

class PackageCreate(PackageBase):
    pass

class PackageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    duration_days: Optional[int] = None
    device_limit: Optional[int] = None
    is_active: Optional[bool] = None

class PackageInDB(PackageBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Package(PackageInDB):
    pass

class OrderBase(BaseModel):
    user_id: int
    package_id: int
    amount: Decimal

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_method: Optional[str] = None
    payment_time: Optional[datetime] = None
    expire_time: Optional[datetime] = None

class OrderInDB(OrderBase):
    id: int
    order_no: str
    status: str
    payment_method: Optional[str] = None
    payment_time: Optional[datetime] = None
    expire_time: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Order(OrderInDB):
    pass

class OrderWithPackage(Order):
    package: Package 