from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.schemas.user import User, UserUpdate, UserPasswordChange, ThemeUpdate, PreferenceSettings
from app.schemas.common import ResponseBase
from app.services.user import UserService
from app.services.subscription import SubscriptionService
from app.services.device_manager import DeviceManager
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

@router.get("/dashboard-info", response_model=ResponseBase)
def get_user_dashboard_info(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户仪表盘信息"""
    try:
        
        user_service = UserService(db)
        subscription_service = SubscriptionService(db)
        
        # 获取用户基本信息
        user = user_service.get(current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        
        # 获取用户订阅信息
        subscription = subscription_service.get_by_user_id(current_user.id)
        
        # 计算剩余天数和到期时间
        remaining_days = 0
        expiry_date = "未设置"
        if subscription and subscription.expire_time:
            try:
                expire_date = subscription.expire_time
                
                # 直接使用datetime对象
                if isinstance(expire_date, datetime):
                    remaining_days = (expire_date - datetime.now()).days
                    expiry_date = expire_date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    expiry_date = "未设置"
            except Exception as e:
                import traceback
                traceback.print_exc()
                expiry_date = "未设置"
        
        # 生成订阅地址
        from app.core.config import settings
        base_url = settings.BASE_URL.rstrip('/')
        clash_url = ""
        v2ray_url = ""
        mobile_url = ""
        qrcode_url = ""
        
        # 无论用户是否到期，都生成订阅地址
        if subscription and subscription.subscription_url:
            mobile_url = f"{base_url}/api/v1/subscriptions/ssr/{subscription.subscription_url}"
            clash_url = f"{base_url}/api/v1/subscriptions/clash/{subscription.subscription_url}"
            v2ray_url = f"{base_url}/api/v1/subscriptions/ssr/{subscription.subscription_url}"  # V2Ray使用SSR端点
            
            
            # 生成二维码URL
            import base64
            from urllib.parse import quote
            try:
                if expiry_date and expiry_date != "未设置":
                    qrcode_url = f"sub://{base64.b64encode(mobile_url.encode()).decode()}#{quote(expiry_date)}"
                else:
                    qrcode_url = f"sub://{base64.b64encode(mobile_url.encode()).decode()}"
            except Exception as e:
                qrcode_url = f"sub://{base64.b64encode(mobile_url.encode()).decode()}"
        
        # 计算订阅状态
        subscription_status = "inactive"
        if subscription:
            if remaining_days > 0:
                subscription_status = "active"
            else:
                subscription_status = "expired"
        
        # 获取用户余额（暂时设为0）
        user_balance = "0.00"
        
        # 获取限速信息（暂时设为不限速，后续可以从配置表获取）
        speed_limit = "不限速"
        
        dashboard_info = {
            "username": user.username,
            "email": user.email,
            "membership": "普通会员",  # 可以根据订阅信息判断会员等级
            "expire_time": subscription.expire_time.isoformat() if subscription and subscription.expire_time else None,
            "expiryDate": expiry_date,
            "remaining_days": remaining_days,
            "online_devices": 0,
            "total_devices": 0,
            "balance": user_balance,
            "speed_limit": speed_limit,
            "subscription_url": subscription.subscription_url if subscription else None,
            "subscription_status": subscription_status,
            # 添加订阅地址信息 - 无论是否到期都提供
            "clashUrl": clash_url,
            "v2rayUrl": v2ray_url,
            "mobileUrl": mobile_url,
            "qrcodeUrl": qrcode_url
        }
        
        return ResponseBase(data=dashboard_info)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仪表盘信息失败: {str(e)}"
        )

# 其他必要的API端点
@router.get("/devices", response_model=ResponseBase)
def get_user_devices(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户设备列表"""
    try:
        device_manager = DeviceManager(db)
        devices = device_manager.get_user_devices(current_user.id)
        return ResponseBase(data=devices)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设备列表失败: {str(e)}"
        )

@router.get("/activities", response_model=ResponseBase)
def get_user_activities(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户活动记录"""
    return ResponseBase(data=[])

@router.get("/login-history", response_model=ResponseBase)
def get_user_login_history(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户登录历史"""
    return ResponseBase(data=[])

@router.get("/subscription-resets", response_model=ResponseBase)
def get_user_subscription_resets(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户订阅重置记录"""
    return ResponseBase(data=[])

@router.put("/profile", response_model=User)
def update_user_profile(
    user_update: UserUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
) -> Any:
    """更新用户资料"""
    user_service = UserService(db)
    user = user_service.update(current_user.id, user_update)
    return user

@router.post("/change-password", response_model=ResponseBase)
def change_user_password(
    password_change: UserPasswordChange,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """修改用户密码"""
    user_service = UserService(db)
    user = user_service.get(current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if not verify_password(password_change.old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    user.password = get_password_hash(password_change.new_password)
    db.commit()
    
    return ResponseBase(message="密码修改成功")

@router.put("/theme", response_model=ResponseBase)
def update_user_theme(
    theme_update: ThemeUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户主题设置"""
    user_service = UserService(db)
    user = user_service.get(current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.theme = theme_update.theme
    db.commit()
    
    return ResponseBase(message="主题更新成功")

@router.put("/preference-settings", response_model=ResponseBase)
def update_user_preference_settings(
    settings: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户偏好设置"""
    return ResponseBase(message="偏好设置更新成功")

@router.post("/send-verification-email", response_model=ResponseBase)
def send_verification_email(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """发送验证邮件"""
    return ResponseBase(message="验证邮件发送成功")
