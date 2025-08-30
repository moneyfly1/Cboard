from .user import User
from .subscription import Subscription, Device
from .order import Order, Package
from .email import EmailQueue, EmailTemplate
from .node import Node
from .payment import PaymentTransaction, PaymentConfig, PaymentCallback
from .notification import Notification
from .config import SystemConfig, Announcement, ThemeConfig

# 设置关系
from sqlalchemy.orm import relationship

# User关系
User.subscriptions = relationship("Subscription", back_populates="user")
User.orders = relationship("Order", back_populates="user")
User.payments = relationship("PaymentTransaction", back_populates="user")
User.notifications = relationship("Notification", back_populates="user")

# Subscription关系
Subscription.user = relationship("User", back_populates="subscriptions")
Subscription.devices = relationship("Device", back_populates="subscription")

# Device关系
Device.subscription = relationship("Subscription", back_populates="devices")

# Order关系
Order.user = relationship("User", back_populates="orders")
Order.package = relationship("Package", back_populates="orders")
Order.payments = relationship("PaymentTransaction", back_populates="order")

# Package关系
Package.orders = relationship("Order", back_populates="package")

# Payment关系
PaymentTransaction.user = relationship("User", back_populates="payments")
PaymentTransaction.order = relationship("Order", back_populates="payments")

# Notification关系
Notification.user = relationship("User", back_populates="notifications")

__all__ = [
    "User",
    "Subscription", 
    "Device",
    "Order",
    "Package", 
    "EmailQueue",
    "EmailTemplate",
    "Node",
    "PaymentTransaction",
    "PaymentConfig",
    "PaymentCallback",
    "Notification",
    "SystemConfig",
    "Announcement",
    "ThemeConfig"
] 