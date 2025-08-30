from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class NotificationBase(BaseModel):
    title: str
    content: str
    type: str = "system"

class NotificationCreate(NotificationBase):
    user_id: Optional[int] = None

class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    is_read: Optional[bool] = None

class NotificationInDB(NotificationBase):
    id: int
    user_id: Optional[int]
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True

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