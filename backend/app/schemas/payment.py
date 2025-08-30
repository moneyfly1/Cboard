from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PaymentMethod(str, Enum):
    ALIPAY = "alipay"
    WECHAT = "wechat"
    PAYPAL = "paypal"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentConfigBase(BaseModel):
    method: PaymentMethod
    is_enabled: bool = True
    config_data: dict = {}

class PaymentConfigCreate(PaymentConfigBase):
    pass

class PaymentConfigUpdate(PaymentConfigBase):
    pass

class PaymentConfig(PaymentConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaymentTransactionBase(BaseModel):
    order_id: int
    amount: float = Field(..., gt=0)
    currency: str = "CNY"
    method: PaymentMethod
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_id: Optional[str] = None
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None

class PaymentTransactionCreate(PaymentTransactionBase):
    pass

class PaymentTransactionUpdate(PaymentTransactionBase):
    pass

class PaymentTransaction(PaymentTransactionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaymentCallback(BaseModel):
    transaction_id: str
    status: PaymentStatus
    amount: float
    signature: Optional[str] = None
    callback_data: dict = {}

class PaymentRequest(BaseModel):
    order_id: int
    method: PaymentMethod
    return_url: Optional[str] = None

class PaymentResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None
    transaction_id: Optional[str] = None

class PaymentStats(BaseModel):
    total_transactions: int
    total_amount: float
    success_rate: float
    method_stats: dict
    daily_stats: List[dict] 