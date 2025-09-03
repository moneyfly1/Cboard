from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.notification import Notification, EmailTemplate
from app.schemas.notification import NotificationCreate, NotificationUpdate, EmailTemplateCreate, EmailTemplateUpdate

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

class EmailTemplateService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, template_id: int) -> Optional[EmailTemplate]:
        """根据ID获取邮件模板"""
        return self.db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()

    def get_by_name(self, name: str) -> Optional[EmailTemplate]:
        """根据名称获取邮件模板"""
        return self.db.query(EmailTemplate).filter(EmailTemplate.name == name).first()

    def get_all_templates(self) -> List[EmailTemplate]:
        """获取所有邮件模板"""
        return self.db.query(EmailTemplate).order_by(EmailTemplate.id.desc()).all()

    def get_active_templates(self) -> List[EmailTemplate]:
        """获取活跃的邮件模板"""
        return self.db.query(EmailTemplate).filter(EmailTemplate.is_active == True).all()

    def create(self, template_in: EmailTemplateCreate) -> EmailTemplate:
        """创建邮件模板"""
        template = EmailTemplate(
            name=template_in.name,
            subject=template_in.subject,
            content=template_in.content,
            variables=template_in.variables
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def update(self, template_id: int, template_in: EmailTemplateUpdate) -> Optional[EmailTemplate]:
        """更新邮件模板"""
        template = self.get(template_id)
        if not template:
            return None
        
        update_data = template_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(template, field, value)
        
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete(self, template_id: int) -> bool:
        """删除邮件模板"""
        template = self.get(template_id)
        if not template:
            return False
        
        self.db.delete(template)
        self.db.commit()
        return True

    def render_template(self, template_name: str, variables: dict) -> Tuple[str, str]:
        """渲染邮件模板"""
        template = self.get_by_name(template_name)
        if not template:
            raise ValueError(f"模板 {template_name} 不存在")
        
        subject = template.subject
        content = template.content
        
        # 简单的变量替换
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, str(value))
            content = content.replace(placeholder, str(value))
        
        return subject, content 