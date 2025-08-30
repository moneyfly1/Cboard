from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

class NotificationType(str, Enum):
    SYSTEM = "system"
    ANNOUNCEMENT = "announcement"
    MAINTENANCE = "maintenance"
    UPDATE = "update"
    ACTIVITY = "activity"
    SUBSCRIPTION = "subscription"
    PAYMENT = "payment"

class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"

class NotificationBase(BaseModel):
    title: str
    content: str
    type: NotificationType = NotificationType.SYSTEM
    status: NotificationStatus = NotificationStatus.UNREAD

class NotificationCreate(NotificationBase):
    user_id: Optional[int] = None
    send_email: bool = False

class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[NotificationType] = None
    status: Optional[NotificationStatus] = None

class NotificationInDB(NotificationBase):
    id: int
    user_id: Optional[int]
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Notification(NotificationInDB):
    """Notification schema alias for backward compatibility"""
    pass

class NotificationList(BaseModel):
    notifications: List[NotificationInDB]
    total: int
    unread_count: int

class NotificationBroadcast(BaseModel):
    title: str
    content: str
    type: NotificationType = NotificationType.ANNOUNCEMENT
    send_email: bool = False
    target_users: Optional[List[int]] = None  # None表示发送给所有用户

class EmailTemplateBase(BaseModel):
    name: str
    subject: str
    content: str
    variables: Optional[str] = None

class EmailTemplateCreate(EmailTemplateBase):
    pass

class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[str] = None
    is_active: Optional[bool] = None

class EmailTemplateInDB(EmailTemplateBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EmailTemplatePreview(BaseModel):
    template_name: str
    variables: dict = {} 