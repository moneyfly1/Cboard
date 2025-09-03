from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import User, UserUpdate, UserPasswordChange
from app.schemas.common import ResponseBase
from app.services.user import UserService
from app.utils.security import get_current_user, verify_password, get_password_hash

router = APIRouter()

@router.get("/profile", response_model=User)
def get_user_profile(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户资料"""
    user_service = UserService(db)
    user = user_service.get(current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user

@router.put("/profile", response_model=User)
def update_user_profile(
    user_update: UserUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
) -> Any:
    """更新用户资料"""
    user_service = UserService(db)
    
    # 检查用户是否存在
    user = user_service.get(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新用户资料
    updated_user = user_service.update(current_user.id, user_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新失败"
        )
    
    # 记录用户活动
    if request:
        user_service.log_user_activity(
            user_id=current_user.id,
            activity_type="profile_update",
            description="更新用户资料",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    
    return updated_user

@router.post("/change-password", response_model=ResponseBase)
def change_password(
    password_change: UserPasswordChange,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
) -> Any:
    """修改密码"""
    user_service = UserService(db)
    
    # 检查用户是否存在
    user = user_service.get(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证当前密码
    if not verify_password(password_change.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 更新密码
    success = user_service.update_password(current_user.id, password_change.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码修改失败"
        )
    
    # 记录用户活动
    if request:
        user_service.log_user_activity(
            user_id=current_user.id,
            activity_type="password_change",
            description="修改密码",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    
    return ResponseBase(message="密码修改成功")

@router.get("/login-history", response_model=ResponseBase)
def get_login_history(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取登录历史"""
    user_service = UserService(db)
    
    # 获取用户登录历史
    login_history = user_service.get_login_history(current_user.id)
    
    return ResponseBase(
        data={
            "login_history": login_history
        }
    )

@router.get("/activities", response_model=ResponseBase)
def get_user_activities(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户操作历史"""
    user_service = UserService(db)
    
    # 获取用户操作历史
    activities = user_service.get_user_activities(current_user.id)
    
    return ResponseBase(
        data={
            "activities": activities
        }
    )

@router.get("/subscription-resets", response_model=ResponseBase)
def get_subscription_resets(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取订阅重置记录"""
    user_service = UserService(db)
    
    # 获取用户订阅重置记录
    resets = user_service.get_subscription_resets(current_user.id)
    
    return ResponseBase(
        data={
            "subscription_resets": resets
        }
    )

@router.get("/notification-settings", response_model=ResponseBase)
def get_user_notification_settings(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户通知设置"""
    # 这里应该从数据库获取用户的个人通知设置
    # 暂时返回默认设置
    default_settings = {
        "email_notifications": True,
        "sms_notifications": False,
        "push_notifications": True,
        "marketing_emails": False,
        "security_alerts": True
    }
    
    return ResponseBase(data=default_settings)

@router.put("/notification-settings", response_model=ResponseBase)
def update_user_notification_settings(
    settings: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户通知设置"""
    # 这里应该将设置保存到数据库
    # 暂时返回成功
    return ResponseBase(message="通知设置更新成功")

@router.get("/privacy-settings", response_model=ResponseBase)
def get_user_privacy_settings(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户隐私设置"""
    # 这里应该从数据库获取用户的个人隐私设置
    # 暂时返回默认设置
    default_settings = {
        "profile_visibility": "public",
        "data_sharing": False,
        "analytics_tracking": True,
        "third_party_access": False
    }
    
    return ResponseBase(data=default_settings)

@router.put("/privacy-settings", response_model=ResponseBase)
def update_user_privacy_settings(
    settings: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户隐私设置"""
    # 这里应该将设置保存到数据库
    # 暂时返回成功
    return ResponseBase(message="隐私设置更新成功")

@router.get("/preference-settings", response_model=ResponseBase)
def get_user_preference_settings(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户偏好设置"""
    # 这里应该从数据库获取用户的个人偏好设置
    # 暂时返回默认设置
    default_settings = {
        "theme": "light",
        "language": "zh-CN",
        "timezone": "Asia/Shanghai",
        "date_format": "YYYY-MM-DD",
        "time_format": "24h"
    }
    
    return ResponseBase(data=default_settings)

@router.put("/preference-settings", response_model=ResponseBase)
def update_user_preference_settings(
    settings: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户偏好设置"""
    # 这里应该将设置保存到数据库
    # 暂时返回成功
    return ResponseBase(message="偏好设置更新成功") 