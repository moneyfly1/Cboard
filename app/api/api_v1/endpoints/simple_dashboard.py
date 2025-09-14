from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.schemas.common import ResponseBase
from app.services.user import UserService
from app.services.subscription import SubscriptionService
from app.services.device_manager import DeviceManager
from app.utils.security import get_current_user

router = APIRouter()

@router.get("/simple-dashboard", response_model=ResponseBase)
def get_simple_dashboard(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """简化的仪表盘信息"""
    try:
        print(f"获取简化仪表盘信息，用户ID: {current_user.id}")
        
        user_service = UserService(db)
        subscription_service = SubscriptionService(db)
        
        # 获取用户基本信息
        user = user_service.get(current_user.id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取用户订阅信息
        subscription = subscription_service.get_by_user_id(current_user.id)
        
        # 计算到期时间
        expiry_date = "未设置"
        remaining_days = 0
        if subscription and subscription.expire_time:
            expire_date = subscription.expire_time
            if isinstance(expire_date, datetime):
                remaining_days = (expire_date - datetime.now()).days
                expiry_date = expire_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # 生成订阅地址
        from app.core.config import settings
        base_url = settings.BASE_URL.rstrip('/')
        clash_url = ""
        v2ray_url = ""
        mobile_url = ""
        
        if subscription and subscription.subscription_url:
            mobile_url = f"{base_url}/api/v1/subscriptions/ssr/{subscription.subscription_url}"
            clash_url = f"{base_url}/api/v1/subscriptions/clash/{subscription.subscription_url}"
            v2ray_url = f"{base_url}/api/v1/subscriptions/ssr/{subscription.subscription_url}"
        
        # 计算订阅状态
        subscription_status = "inactive"
        if subscription and remaining_days > 0:
            subscription_status = "active"
        
        dashboard_info = {
            "username": user.username,
            "email": user.email,
            "membership": "普通会员",
            "expire_time": subscription.expire_time.isoformat() if subscription and subscription.expire_time else None,
            "expiryDate": expiry_date,
            "remaining_days": remaining_days,
            "online_devices": 0,
            "total_devices": 0,
            "balance": "0.00",
            "speed_limit": "不限速",
            "subscription_url": subscription.subscription_url if subscription else None,
            "subscription_status": subscription_status,
            "clashUrl": clash_url,
            "v2rayUrl": v2ray_url,
            "mobileUrl": mobile_url,
            "qrcodeUrl": ""
        }
        
        print(f"返回简化仪表盘信息: {dashboard_info}")
        return ResponseBase(data=dashboard_info)
        
    except Exception as e:
        print(f"获取简化仪表盘信息失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取仪表盘信息失败: {str(e)}")
