from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate

class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, notification_id: int) -> Optional[Notification]:
        """根据ID获取通知"""
        return self.db.query(Notification).filter(Notification.id == notification_id).first()

    def get_user_notifications(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        unread_only: bool = False
    ) -> Tuple[List[Notification], int]:
        """获取用户通知"""
        query = self.db.query(Notification).filter(
            Notification.user_id == user_id
        )
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        total = query.count()
        notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
        
        return notifications, total

    def get_system_notifications(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Notification], int]:
        """获取系统通知"""
        query = self.db.query(Notification).filter(
            Notification.user_id.is_(None)
        )
        
        total = query.count()
        notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
        
        return notifications, total

    def create(self, notification_in: NotificationCreate) -> Notification:
        """创建通知"""
        notification = Notification(
            user_id=notification_in.user_id,
            title=notification_in.title,
            content=notification_in.content,
            type=notification_in.type
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def create_system_notification(self, title: str, content: str, notification_type: str = "system") -> Notification:
        """创建系统通知"""
        return self.create(NotificationCreate(
            title=title,
            content=content,
            type=notification_type
        ))

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """标记通知为已读"""
        notification = self.db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ).first()
        
        if not notification:
            return False
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        self.db.commit()
        return True

    def mark_all_as_read(self, user_id: int) -> int:
        """标记用户所有通知为已读"""
        result = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow()
        })
        
        self.db.commit()
        return result

    def delete(self, notification_id: int) -> bool:
        """删除通知"""
        notification = self.get(notification_id)
        if not notification:
            return False
        
        self.db.delete(notification)
        self.db.commit()
        return True

    def get_unread_count(self, user_id: int) -> int:
        """获取用户未读通知数量"""
        return self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        ).count()
