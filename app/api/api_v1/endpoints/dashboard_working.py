from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.schemas.common import ResponseBase
from app.services.user import UserService
from app.services.subscription import SubscriptionService
from app.utils.security import get_current_user

router = APIRouter()

@router.get("/dashboard-info", response_model=ResponseBase)
def get_user_dashboard_info_working(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户仪表盘信息 - 工作版本"""
    try:
        print(f"获取用户仪表盘信息，用户ID: {current_user.id}")
        
        user_service = UserService(db)
        subscription_service = SubscriptionService(db)
        
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
        
        # 计算剩余天数和到期时间
        remaining_days = 0
        expiry_date = "未设置"
        if subscription and subscription.expire_time:
            try:
                expire_date = subscription.expire_time
                print(f"原始到期时间: {expire_date}, 类型: {type(expire_date)}")
                
                # 直接使用datetime对象
                if isinstance(expire_date, datetime):
                    remaining_days = (expire_date - datetime.now()).days
                    expiry_date = expire_date.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"解析后的到期时间: {expire_date}, 剩余天数: {remaining_days}")
                else:
                    print("到期时间不是datetime对象")
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
