from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Numeric
from sqlalchemy.sql import func
from app.core.database import Base

class PaymentConfig(Base):
    __tablename__ = "payment_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # alipay, wechat, paypal, stripe, etc.
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    config = Column(JSON, nullable=True)  # 支付配置参数
    description = Column(Text, nullable=True)
    icon = Column(String(200), nullable=True)  # 支付图标
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<PaymentConfig(id={self.id}, name='{self.name}', type='{self.type}')>"

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False)
    payment_config_id = Column(Integer, nullable=False)
    transaction_id = Column(String(200), nullable=False, unique=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default='CNY')
    status = Column(String(50), default='pending')  # pending, success, failed, cancelled
    payment_method = Column(String(50), nullable=False)
    gateway_response = Column(JSON, nullable=True)  # 支付网关响应
    callback_data = Column(JSON, nullable=True)  # 回调数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<PaymentTransaction(id={self.id}, transaction_id='{self.transaction_id}', status='{self.status}')>"

class PaymentCallback(Base):
    __tablename__ = "payment_callbacks"

    id = Column(Integer, primary_key=True, index=True)
    payment_config_id = Column(Integer, nullable=False)
    transaction_id = Column(String(200), nullable=False)
    callback_type = Column(String(50), nullable=False)  # success, failure, refund
    raw_data = Column(JSON, nullable=True)  # 原始回调数据
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<PaymentCallback(id={self.id}, transaction_id='{self.transaction_id}', type='{self.callback_type}')>" 