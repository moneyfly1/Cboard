from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.notification import NotificationCreate, NotificationUpdate, EmailTemplateCreate, EmailTemplateUpdate
from app.schemas.common import ResponseBase, PaginationParams
from app.services.notification import NotificationService
from app.services.email_template import EmailTemplateService
from app.utils.security import get_current_user, get_current_admin_user

router = APIRouter()

# ==================== 用户通知 ====================

@router.get("/user-notifications", response_model=ResponseBase)
def get_user_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """获取用户通知列表"""
    notification_service = NotificationService(db)
    
    skip = (page - 1) * size
    notifications, total = notification_service.get_user_notifications(
        user_id=current_user.id,
        skip=skip,
        limit=size,
        unread_only=unread_only
    )
    
    return ResponseBase(
        data={
            "notifications": [
                {
                    "id": notif.id,
                    "title": notif.title,
                    "content": notif.content,
                    "type": notif.type,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at.isoformat(),
                    "read_at": notif.read_at.isoformat() if notif.read_at else None
                }
                for notif in notifications
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    )

@router.get("/unread-count", response_model=ResponseBase)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """获取未读通知数量"""
    notification_service = NotificationService(db)
    count = notification_service.get_unread_count(current_user.id)
    
    return ResponseBase(data={"count": count})

@router.post("/{notification_id}/read", response_model=ResponseBase)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """标记通知为已读"""
    notification_service = NotificationService(db)
    
    success = notification_service.mark_as_read(notification_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )
    
    return ResponseBase(message="标记成功")

@router.post("/mark-all-read", response_model=ResponseBase)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """标记所有通知为已读"""
    notification_service = NotificationService(db)
    
    count = notification_service.mark_all_as_read(current_user.id)
    
    return ResponseBase(
        message=f"已标记 {count} 条通知为已读",
        data={"count": count}
    )

# ==================== 管理端通知 ====================

@router.get("/admin/notifications", response_model=ResponseBase)
def get_admin_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    notification_type: str = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取通知列表（管理端）"""
    notification_service = NotificationService(db)
    
    skip = (page - 1) * size
    notifications, total = notification_service.get_system_notifications(skip, size)
    
    # 按类型筛选
    if notification_type:
        notifications = [n for n in notifications if n.type == notification_type]
        total = len(notifications)
    
    return ResponseBase(
        data={
            "notifications": [
                {
                    "id": notif.id,
                    "title": notif.title,
                    "content": notif.content,
                    "type": notif.type,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at.isoformat(),
                    "read_at": notif.read_at.isoformat() if notif.read_at else None
                }
                for notif in notifications
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    )

@router.post("/admin/notifications", response_model=ResponseBase)
def create_notification(
    notification_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建通知"""
    notification_service = NotificationService(db)
    
    notification = notification_service.create(NotificationCreate(**notification_data))
    
    return ResponseBase(
        message="通知创建成功",
        data={"notification_id": notification.id}
    )

@router.post("/admin/notifications/broadcast", response_model=ResponseBase)
def broadcast_notification(
    notification_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """广播通知给所有用户"""
    from app.services.user import UserService
    
    notification_service = NotificationService(db)
    user_service = UserService(db)
    
    # 获取所有用户
    users = user_service.get_multi()
    
    created_count = 0
    for user in users:
        try:
            notification_service.create(NotificationCreate(
                user_id=user.id,
                title=notification_data["title"],
                content=notification_data["content"],
                type=notification_data.get("type", "system")
            ))
            created_count += 1
        except Exception as e:
            continue
    
    return ResponseBase(
        message=f"广播通知成功，已发送给 {created_count} 个用户",
        data={"sent_count": created_count}
    )

@router.delete("/admin/notifications/{notification_id}", response_model=ResponseBase)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除通知"""
    notification_service = NotificationService(db)
    
    success = notification_service.delete(notification_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )
    
    return ResponseBase(message="通知删除成功")

# ==================== 邮件模板管理 ====================

@router.get("/admin/email-templates", response_model=ResponseBase)
def get_email_templates(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取邮件模板列表"""
    template_service = EmailTemplateService(db)
    templates = template_service.get_all_templates()
    
    return ResponseBase(
        data={
            "templates": [
                {
                    "id": template.id,
                    "name": template.name,
                    "subject": template.subject,
                    "content": template.content,
                    "variables": template.variables,
                    "is_active": template.is_active,
                    "created_at": template.created_at.isoformat(),
                    "updated_at": template.updated_at.isoformat() if template.updated_at else None
                }
                for template in templates
            ]
        }
    )

@router.post("/admin/email-templates", response_model=ResponseBase)
def create_email_template(
    template_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建邮件模板"""
    template_service = EmailTemplateService(db)
    
    template = template_service.create(EmailTemplateCreate(**template_data))
    
    return ResponseBase(
        message="邮件模板创建成功",
        data={"template_id": template.id}
    )

@router.put("/admin/email-templates/{template_id}", response_model=ResponseBase)
def update_email_template(
    template_id: int,
    template_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新邮件模板"""
    template_service = EmailTemplateService(db)
    
    template = template_service.update(template_id, EmailTemplateUpdate(**template_data))
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮件模板不存在"
        )
    
    return ResponseBase(message="邮件模板更新成功")

@router.delete("/admin/email-templates/{template_id}", response_model=ResponseBase)
def delete_email_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除邮件模板"""
    template_service = EmailTemplateService(db)
    
    success = template_service.delete(template_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮件模板不存在"
        )
    
    return ResponseBase(message="邮件模板删除成功")

@router.post("/admin/email-templates/{template_name}/preview", response_model=ResponseBase)
def preview_email_template(
    template_name: str,
    variables: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """预览邮件模板"""
    template_service = EmailTemplateService(db)
    
    try:
        subject, content = template_service.render_template(template_name, variables)
        
        return ResponseBase(
            data={
                "subject": subject,
                "content": content
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        ) 