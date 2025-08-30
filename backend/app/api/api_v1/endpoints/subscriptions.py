from datetime import datetime, timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import secrets
import string
import base64
from urllib.parse import quote

from app.core.config import settings
from app.core.database import get_db
from app.schemas.subscription import SubscriptionInDB, DeviceInDB
from app.schemas.common import ResponseBase
from app.services.subscription import SubscriptionService
from app.services.user import UserService
from app.utils.security import get_current_user, generate_subscription_url
from app.services.email import EmailService
from app.utils.device import generate_device_fingerprint, detect_device_type, extract_device_name

router = APIRouter()

@router.get("/user-subscription", response_model=ResponseBase)
def get_user_subscription(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户订阅信息"""
    subscription_service = SubscriptionService(db)
    
    # 获取用户订阅
    subscription = subscription_service.get_by_user_id(current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到订阅信息"
        )
    
    # 计算剩余天数
    now = datetime.utcnow()
    if subscription.expire_time:
        remaining_days = max(0, (subscription.expire_time - now).days)
        is_expiring = remaining_days <= 7
        expiry_date = subscription.expire_time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        remaining_days = 0
        is_expiring = False
        expiry_date = "未设置"
    
    # 获取设备数量
    devices = subscription_service.get_devices_by_subscription_id(subscription.id)
    current_devices = len(devices)
    max_devices = subscription.device_limit
    
    # 生成订阅URL
    base_url = settings.BASE_URL.rstrip('/')
    ssr_url = f"{base_url}/api/v1/subscriptions/{subscription.id}/ssr"
    clash_url = f"{base_url}/api/v1/subscriptions/{subscription.id}/clash"
    qrcode_url = f"sub://{base64_encode(ssr_url)}#{urlencode(expiry_date)}"
    
    return ResponseBase(
        data={
            "subscription_id": subscription.id,
            "remaining_days": remaining_days,
            "expiry_date": expiry_date,
            "is_expiring": is_expiring,
            "current_devices": current_devices,
            "max_devices": max_devices,
            "is_device_limit_reached": current_devices >= max_devices,
            "ssr_url": ssr_url,
            "clash_url": clash_url,
            "qrcode_url": qrcode_url
        }
    )

@router.post("/reset-subscription", response_model=ResponseBase)
def reset_subscription(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """重置订阅地址"""
    subscription_service = SubscriptionService(db)
    
    # 获取用户订阅
    subscription = subscription_service.get_by_user_id(current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到订阅信息"
        )
    
    # 删除所有设备记录
    subscription_service.delete_devices_by_subscription_id(subscription.id)
    
    # 生成新的订阅密钥
    new_key = generate_subscription_url()
    subscription_service.update_subscription_key(subscription.id, new_key)
    
    return ResponseBase(message="订阅地址重置成功")

@router.post("/send-subscription-email", response_model=ResponseBase)
def send_subscription_email_endpoint(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """发送订阅邮件"""
    subscription_service = SubscriptionService(db)
    
    # 获取用户订阅
    subscription = subscription_service.get_by_user_id(current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到订阅信息"
        )
    
    # 生成订阅URL
    base_url = settings.BASE_URL.rstrip('/')
    ssr_url = f"{base_url}/api/v1/subscriptions/{subscription.id}/ssr"
    clash_url = f"{base_url}/api/v1/subscriptions/{subscription.id}/clash"
    
    # 发送邮件
    try:
        email_service = EmailService(db)
        subscription_data = {
            'id': subscription.id,
            'package_name': subscription.package.name if subscription.package else '未知套餐',
            'expires_at': subscription.expire_time.strftime('%Y-%m-%d %H:%M:%S') if subscription.expire_time else '未知',
            'status': subscription.status,
            'ssr_url': ssr_url,
            'clash_url': clash_url
        }
        success = email_service.send_subscription_email(current_user.email, subscription_data)
        if success:
            return ResponseBase(message="订阅邮件发送成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="邮件发送失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"邮件发送失败: {str(e)}"
        )

@router.get("/devices", response_model=ResponseBase)
def get_user_devices(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户设备列表"""
    subscription_service = SubscriptionService(db)
    
    # 获取用户订阅
    subscription = subscription_service.get_by_user_id(current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到订阅信息"
        )
    
    # 获取设备列表
    devices = subscription_service.get_devices_by_subscription_id(subscription.id)
    
    device_list = []
    for device in devices:
        device_list.append({
            "id": device.id,
            "name": device.name,
            "type": device.type,
            "ip": device.ip,
            "last_access": device.last_access.strftime('%Y-%m-%d %H:%M:%S') if device.last_access else None
        })
    
    return ResponseBase(data={"devices": device_list})

@router.delete("/devices/{device_id}", response_model=ResponseBase)
def remove_device(
    device_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """移除设备"""
    subscription_service = SubscriptionService(db)
    
    # 获取设备
    device = subscription_service.get_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 检查设备是否属于当前用户
    subscription = subscription_service.get(device.subscription_id)
    if not subscription or subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此设备"
        )
    
    # 删除设备
    subscription_service.delete_device(device_id)
    
    return ResponseBase(message="设备移除成功")

# 订阅内容端点（用于客户端访问）
@router.get("/{subscription_id}/ssr")
def get_ssr_subscription(
    subscription_id: int,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """获取SSR订阅内容"""
    subscription_service = SubscriptionService(db)
    
    # 获取订阅信息
    subscription = subscription_service.get(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )
    
    # 检查订阅是否有效
    if subscription.expire_time and subscription.expire_time < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="订阅已过期"
        )
    
    # 记录设备访问
    record_device_access(subscription, request, db)
    
    # 返回SSR订阅内容
    ssr_content = subscription_service.generate_ssr_subscription(subscription)
    return ResponseBase(data={"content": ssr_content})

@router.get("/{subscription_id}/clash")
def get_clash_subscription(
    subscription_id: int,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """获取Clash订阅内容"""
    subscription_service = SubscriptionService(db)
    
    # 获取订阅信息
    subscription = subscription_service.get(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )
    
    # 检查订阅是否有效
    if subscription.expire_time and subscription.expire_time < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="订阅已过期"
        )
    
    # 记录设备访问
    record_device_access(subscription, request, db)
    
    # 返回Clash订阅内容
    clash_content = subscription_service.generate_clash_subscription(subscription)
    return ResponseBase(data={"content": clash_content})

def base64_encode(text: str) -> str:
    """Base64编码"""
    return base64.b64encode(text.encode()).decode()

def urlencode(text: str) -> str:
    """URL编码"""
    return quote(text)

def record_device_access(subscription, request: Request, db: Session):
    """记录设备访问"""
    subscription_service = SubscriptionService(db)
    
    user_agent = request.headers.get("user-agent", "")
    client_ip = request.client.host if request.client else "unknown"
    
    # 生成设备指纹
    fingerprint = generate_device_fingerprint(user_agent, client_ip)
    device_type = detect_device_type(user_agent)
    device_name = extract_device_name(user_agent)
    
    # 记录设备访问
    subscription_service.record_device_access(
        subscription_id=subscription.id,
        device_info={
            "fingerprint": fingerprint,
            "name": device_name,
            "type": device_type,
            "ip": client_ip,
            "user_agent": user_agent
        }
    ) 