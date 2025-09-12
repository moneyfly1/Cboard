from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.schemas.user import User, UserUpdate, UserPasswordChange
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

@router.get("/dashboard-info", response_model=ResponseBase)
def get_user_dashboard_info(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户仪表盘信息"""
    try:
        print(f"获取用户仪表盘信息，用户ID: {current_user.id}")
        
        user_service = UserService(db)
        subscription_service = SubscriptionService(db)
        device_manager = DeviceManager(db)
        
        # 获取用户基本信息
        user = user_service.get(current_user.id)
        if not user:
            print(f"用户不存在: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        print(f"找到用户: {user.username}, 邮箱: {user.email}")
        
        # 获取用户订阅信息
        subscription = subscription_service.get_by_user_id(current_user.id)
        if subscription:
            print(f"找到订阅: ID={subscription.id}, URL={subscription.subscription_url}, 到期时间={subscription.expire_time}")
        else:
            print("用户没有订阅信息")
        
        # 获取用户设备数量
        devices = device_manager.get_user_devices(current_user.id)
        online_devices = len([d for d in devices if d.get('is_allowed', True)])
        total_devices = len(devices)
        print(f"用户设备数量: 总数={total_devices}, 在线={online_devices}")
        
        # 计算剩余天数和到期时间
        remaining_days = 0
        expiry_date = "未设置"
        if subscription and subscription.expire_time:
            try:
                expire_date = subscription.expire_time
                print(f"原始到期时间: {expire_date}, 类型: {type(expire_date)}")
                
                if isinstance(expire_date, str):
                    # 处理字符串格式的日期
                    if expire_date and expire_date != '0':
                        expire_date = datetime.fromisoformat(expire_date.replace('Z', '+00:00'))
                    else:
                        expire_date = None
                elif isinstance(expire_date, (int, float)):
                    # 处理数字格式的日期
                    if expire_date > 0:
                        expire_date = datetime.fromtimestamp(expire_date)
                    else:
                        expire_date = None
                else:
                    expire_date = None
                
                if expire_date:
                    remaining_days = (expire_date - datetime.utcnow()).days
                    expiry_date = expire_date.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"解析后的到期时间: {expire_date}, 剩余天数: {remaining_days}")
                else:
                    print("到期时间无效或为0")
            except Exception as e:
                print(f"处理到期时间时出错: {e}")
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
            
            print(f"生成的订阅地址:")
            print(f"  Clash: {clash_url}")
            print(f"  Shadowrocket: {mobile_url}")
            print(f"  V2Ray: {v2ray_url}")
            
            # 生成二维码URL
            import base64
            from urllib.parse import quote
            try:
                if expiry_date and expiry_date != "未设置":
                    qrcode_url = f"sub://{base64.b64encode(mobile_url.encode()).decode()}#{quote(expiry_date)}"
                else:
                    qrcode_url = f"sub://{base64.b64encode(mobile_url.encode()).decode()}"
                print(f"  二维码: {qrcode_url}")
            except Exception as e:
                print(f"生成二维码URL时出错: {e}")
                qrcode_url = f"sub://{base64.b64encode(mobile_url.encode()).decode()}"
        else:
            print("用户没有订阅URL，无法生成订阅地址")
        
        # 计算订阅状态
        subscription_status = "inactive"
        if subscription:
            if subscription.is_active and remaining_days > 0:
                subscription_status = "active"
            elif subscription.is_active and remaining_days <= 0:
                subscription_status = "expired"
            else:
                subscription_status = "inactive"
        
        # 获取用户余额（暂时设为0，后续可以从钱包表获取）
        user_balance = "0.00"
        
        # 获取限速信息（暂时设为不限速，后续可以从配置表获取）
        speed_limit = "不限速"
        
        dashboard_info = {
            "username": user.username,
            "email": user.email,
            "membership": "普通会员",  # 可以根据订阅信息判断会员等级
            "expire_time": subscription.expire_time if subscription else None,
            "expiryDate": expiry_date,
            "remaining_days": remaining_days,
            "online_devices": online_devices,
            "total_devices": total_devices,
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
        
        print(f"返回仪表盘信息: {dashboard_info}")
        return ResponseBase(data=dashboard_info)
        
    except Exception as e:
        print(f"获取仪表盘信息失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仪表盘信息失败: {str(e)}"
        )

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

@router.post("/daily-checkin", response_model=ResponseBase)
def daily_checkin(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """每日签到"""
    try:
        # 检查今天是否已经签到
        today = datetime.utcnow().date()
        checkin_record = db.execute("""
            SELECT * FROM user_activities 
            WHERE user_id = :user_id 
            AND action = 'daily_checkin' 
            AND DATE(created_at) = :today
        """, {'user_id': current_user.id, 'today': today}).fetchone()
        
        if checkin_record:
            return ResponseBase(message="今日已签到，请明天再来！")
        
        # 记录签到
        db.execute("""
            INSERT INTO user_activities (user_id, action, description, created_at)
            VALUES (:user_id, 'daily_checkin', '每日签到', :now)
        """, {'user_id': current_user.id, 'now': datetime.utcnow()})
        
        db.commit()
        
        return ResponseBase(message="签到成功！获得积分奖励")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"签到失败: {str(e)}"
        )

# 删除重复的验证邮件发送功能，统一使用 auth.py 中的 resend_verification 端点 