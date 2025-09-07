from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_url = Column(String(100), unique=True, index=True, nullable=False)
    device_limit = Column(Integer, default=3)
    current_devices = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expire_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="subscriptions")
    devices = relationship("Device", back_populates="subscription")
    resets = relationship("SubscriptionReset", back_populates="subscription")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, url='{self.subscription_url}')>"
class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    device_fingerprint = Column(String(255), nullable=False)
    device_name = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    last_access = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    subscription = relationship("Subscription", back_populates="devices")
    
    def __repr__(self):
        return f"<Device(id={self.id}, subscription_id={self.subscription_id}, fingerprint='{self.device_fingerprint}')>" 
