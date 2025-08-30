from .user import User
from .subscription import Subscription, Device
from .order import Order, Package
from .email import EmailQueue
from .node import Node

# 设置关系
from sqlalchemy.orm import relationship

# User关系
User.subscriptions = relationship("Subscription", back_populates="user")
User.orders = relationship("Order", back_populates="user")

# Subscription关系
Subscription.user = relationship("User", back_populates="subscriptions")
Subscription.devices = relationship("Device", back_populates="subscription")

# Device关系
Device.subscription = relationship("Subscription", back_populates="devices")

# Order关系
Order.user = relationship("User", back_populates="orders")
Order.package = relationship("Package", back_populates="orders")

# Package关系
Package.orders = relationship("Order", back_populates="package")

__all__ = [
    "User",
    "Subscription", 
    "Device",
    "Order",
    "Package", 
    "EmailQueue"
] 