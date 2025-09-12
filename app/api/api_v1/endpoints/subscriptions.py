from datetime import datetime, timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
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
from app.models.subscription import Subscription

def get_device_type_from_os(os_name: str) -> str:
    """根据操作系统名称判断设备类型"""
    if not os_name:
        return "unknown"
    
    os_name_lower = os_name.lower()
    if "ios" in os_name_lower or "iphone" in os_name_lower or "ipad" in os_name_lower:
        return "mobile"
    elif "android" in os_name_lower:
        return "mobile"
    elif "windows" in os_name_lower or "macos" in os_name_lower or "linux" in os_name_lower:
        return "desktop"
    elif "tv" in os_name_lower or "smart" in os_name_lower:
        return "tv"
    else:
        return "unknown"

router = APIRouter()

@router.get("/user-subscription", response_model=ResponseBase)
def get_user_subscription(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户订阅信息"""
    try:
        subscription_service = SubscriptionService(db)
        
        # 获取用户订阅
        subscription = subscription_service.get_by_user_id(current_user.id)
        if not subscription:
            # 如果没有订阅信息，返回默认数据
            return ResponseBase(
                data={
                    "subscription_id": None,
                    "status": "expired",
                    "remainingDays": 0,
                    "expiryDate": "未订阅",
                    "is_expiring": False,
                    "currentDevices": 0,
                    "maxDevices": 0,
                    "is_device_limit_reached": False,
                    "mobileUrl": "",
                    "clashUrl": "",
                    "qrcodeUrl": ""
                }
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
        if subscription.subscription_url:
            ssr_url = f"{base_url}/api/v1/subscriptions/ssr/{subscription.subscription_url}"
            clash_url = f"{base_url}/api/v1/subscriptions/clash/{subscription.subscription_url}"
            v2ray_url = f"{base_url}/api/v1/subscriptions/ssr/{subscription.subscription_url}"  # V2Ray使用SSR端点
            qrcode_url = f"sub://{base64_encode(ssr_url)}#{urlencode(expiry_date)}"
        else:
            ssr_url = ""
            clash_url = ""
            v2ray_url = ""
            qrcode_url = ""
        
        return ResponseBase(
            data={
                "subscription_id": subscription.id,
                "status": "active" if remaining_days > 0 else "expired",
                "remainingDays": remaining_days,
                "expiryDate": expiry_date,
                "is_expiring": is_expiring,
                "currentDevices": current_devices,
                "current_devices": current_devices,
                "online_devices": current_devices,
                "maxDevices": max_devices,
                "is_device_limit_reached": current_devices >= max_devices,
                "mobileUrl": ssr_url,
                "clashUrl": clash_url,
                "v2rayUrl": v2ray_url,
                "qrcodeUrl": qrcode_url
            }
        )
    except Exception as e:
        # 如果发生错误，返回默认数据
        return ResponseBase(
            data={
                "subscription_id": None,
                "status": "expired",
                "remainingDays": 0,
                "expiryDate": "加载失败",
                "is_expiring": False,
                "currentDevices": 0,
                "maxDevices": 0,
                "is_device_limit_reached": False,
                "mobileUrl": "",
                "clashUrl": "",
                "qrcodeUrl": ""
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
    
    # 发送重置通知邮件
    try:
        from app.services.email import EmailService
        from datetime import datetime
        
        if current_user.email:
            email_service = EmailService(db)
            reset_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 发送重置通知邮件
            email_service.send_subscription_reset_notification(
                user_email=current_user.email,
                username=current_user.username,
                new_subscription_url=new_key,
                reset_time=reset_time,
                reset_reason="用户重置"
            )
            print(f"已发送用户重置订阅通知邮件到: {current_user.email}")
    except Exception as e:
        print(f"发送用户重置订阅通知邮件失败: {e}")
    
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
        success = email_service.email_service = EmailService(db)
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
    try:
        subscription_service = SubscriptionService(db)
        
        # 获取用户订阅
        subscription = subscription_service.get_by_user_id(current_user.id)
        if not subscription:
            # 如果没有订阅，返回空设备列表
            return ResponseBase(data={"devices": []})
        
        # 获取设备列表 - 直接查询devices表
        from sqlalchemy import text
        device_query = text("""
            SELECT * FROM devices
            WHERE subscription_id = :subscription_id
            ORDER BY last_access DESC
        """)
        device_rows = db.execute(device_query, {"subscription_id": subscription.id}).fetchall()
        
        device_list = []
        for device_row in device_rows:
            device_data = {
                "id": device_row.id,
                "device_name": device_row.device_name or "未知设备",
                "device_type": device_row.device_type or "unknown",
                "ip_address": device_row.ip_address,
                "user_agent": device_row.user_agent,
                "last_access": device_row.last_access if device_row.last_access else None,
                "is_active": device_row.is_active,
                "created_at": device_row.created_at if device_row.created_at else None
            }
            device_list.append(device_data)
        
        return ResponseBase(data={"devices": device_list})
    except Exception as e:
        # 如果发生错误，返回空设备列表
        return ResponseBase(data={"devices": []})

@router.delete("/devices/{device_id}", response_model=ResponseBase)
def remove_device(
    device_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """移除设备"""
    try:
        subscription_service = SubscriptionService(db)
        
        # 获取用户订阅
        subscription = subscription_service.get_by_user_id(current_user.id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户没有订阅"
            )
        
        # 验证设备是否属于当前用户
        from sqlalchemy import text
        device_query = text("""
            SELECT id FROM devices 
            WHERE id = :device_id AND subscription_id = :subscription_id
        """)
        device = db.execute(device_query, {
            'device_id': device_id,
            'subscription_id': subscription.id
        }).fetchone()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在或无权限操作"
            )
        
        # 删除设备
        result = db.execute(text("""
            DELETE FROM devices WHERE id = :device_id
        """), {'device_id': device_id})
        
        if result.rowcount > 0:
            # 更新订阅的设备计数
            subscription.current_devices = max(0, subscription.current_devices - 1)
            db.commit()
            return ResponseBase(message="设备移除成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除设备失败: {str(e)}"
        )

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
    is_valid = True
    if subscription.expire_time and subscription.expire_time < datetime.utcnow():
        is_valid = False
    
    # 检查用户是否被禁用
    if subscription.user and not subscription.user.is_active:
        is_valid = False
    
    # 检查设备数量是否超限
    devices = subscription_service.get_devices_by_subscription_id(subscription.id)
    if len(devices) > subscription.device_limit:
        is_valid = False
    
    # 记录设备访问
    record_device_access(subscription, request, db)
    
    if is_valid:
        # 返回有效的Clash订阅内容
        clash_content = subscription_service.generate_clash_subscription(subscription)
    else:
        # 返回失效的Clash配置
        clash_content = subscription_service.get_invalid_clash_config()
    
    return ResponseBase(data={"content": clash_content})

@router.get("/{subscription_id}/v2ray")
def get_v2ray_subscription(
    subscription_id: int,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """获取V2Ray订阅内容"""
    subscription_service = SubscriptionService(db)
    
    # 获取订阅信息
    subscription = subscription_service.get(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )
    
    # 检查订阅是否有效
    is_valid = True
    if subscription.expire_time and subscription.expire_time < datetime.utcnow():
        is_valid = False
    
    # 检查用户是否被禁用
    if subscription.user and not subscription.user.is_active:
        is_valid = False
    
    # 检查设备数量是否超限
    devices = subscription_service.get_devices_by_subscription_id(subscription.id)
    if len(devices) > subscription.device_limit:
        is_valid = False
    
    # 记录设备访问
    record_device_access(subscription, request, db)
    
    if is_valid:
        # 返回有效的V2Ray订阅内容
        v2ray_content = subscription_service.generate_v2ray_subscription(subscription)
    else:
        # 返回失效的V2Ray配置
        v2ray_content = subscription_service.get_invalid_v2ray_config()
    
    return ResponseBase(data={"content": v2ray_content})

def base64_encode(text: str) -> str:
    """Base64编码"""
    return base64.b64encode(text.encode()).decode()

def urlencode(text: str) -> str:
    """URL编码"""
    return quote(text)

def record_device_access(subscription, request: Request, db: Session):
    """记录设备访问"""
    from app.services.device_manager import DeviceManager
    
    user_agent = request.headers.get("user-agent", "")
    client_ip = request.client.host if request.client else "unknown"
    
    # 使用新的设备管理系统
    device_manager = DeviceManager(db)
    
    # 检查订阅访问权限并记录设备
    access_result = device_manager.check_subscription_access(
        subscription.subscription_url, 
        user_agent, 
        client_ip
    )
    
    print(f"设备访问检查结果: {access_result}")

@router.put("/user-subscription", response_model=ResponseBase)
def update_user_subscription(
    subscription_data: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户订阅设置"""
    try:
        subscription_service = SubscriptionService(db)
        
        subscription = subscription_service.get_by_user_id(current_user.id)
        if not subscription:
            raise HTTPException(status_code=404, detail="用户没有订阅")
        
        # 更新设备限制
        if "device_limit" in subscription_data:
            new_limit = subscription_data["device_limit"]
            if new_limit < subscription.current_devices:
                raise HTTPException(status_code=400, detail="设备限制不能小于当前设备数量")
            subscription.device_limit = new_limit
        
        # 更新到期时间
        if "expire_time" in subscription_data:
            from datetime import datetime
            try:
                new_expire_time = datetime.fromisoformat(subscription_data["expire_time"])
                subscription.expire_time = new_expire_time
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误")
        
        subscription_service.db.commit()
        
        return ResponseBase(message="订阅设置更新成功")
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"更新订阅设置失败: {str(e)}")

@router.post("/user-subscription/reset-url", response_model=ResponseBase)
def reset_user_subscription_url(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """重置用户订阅地址"""
    try:
        subscription_service = SubscriptionService(db)
        
        subscription = subscription_service.get_by_user_id(current_user.id)
        if not subscription:
            raise HTTPException(status_code=400, detail="用户没有订阅")
        
        # 生成新的订阅URL
        from app.utils.security import generate_subscription_url
        new_url = generate_subscription_url()
        subscription.subscription_url = new_url
        
        # 清理所有设备
        devices = subscription_service.get_devices_by_subscription_id(subscription.id)
        for device in devices:
            subscription_service.db.delete(device)
        
        subscription.current_devices = 0
        subscription_service.db.commit()
        
        # 发送重置通知邮件
        try:
            from app.services.email import EmailService
            from datetime import datetime
            
            if current_user.email:
                email_service = EmailService(db)
                reset_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 发送重置通知邮件
                email_service.send_subscription_reset_notification(
                    user_email=current_user.email,
                    username=current_user.username,
                    new_subscription_url=new_url,
                    reset_time=reset_time,
                    reset_reason="用户重置订阅地址"
                )
                print(f"已发送用户重置订阅地址通知邮件到: {current_user.email}")
        except Exception as e:
            print(f"发送用户重置订阅地址通知邮件失败: {e}")
        
        return ResponseBase(message="订阅地址重置成功", data={"new_subscription_url": new_url})
    except Exception as e:
        return ResponseBase(success=False, message=f"重置订阅地址失败: {str(e)}")


@router.post("/devices/clear", response_model=ResponseBase)
def clear_user_devices(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """清理用户所有设备"""
    try:
        subscription_service = SubscriptionService(db)
        
        subscription = subscription_service.get_by_user_id(current_user.id)
        if not subscription:
            raise HTTPException(status_code=400, detail="用户没有订阅")
        
        # 清理所有设备
        devices = subscription_service.get_devices_by_subscription_id(subscription.id)
        for device in devices:
            subscription_service.db.delete(device)
        
        subscription.current_devices = 0
        subscription_service.db.commit()
        
        return ResponseBase(message="所有设备清理成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"清理设备失败: {str(e)}") 

@router.get("/ssr/{subscription_key}")
def get_ssr_subscription(
    subscription_key: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """获取SSR/V2Ray订阅内容 - 集成设备限制检查"""
    try:
        from app.services.device_manager import DeviceManager
        
        subscription_service = SubscriptionService(db)
        device_manager = DeviceManager(db)
        
        # 获取请求信息
        user_agent = request.headers.get("user-agent", "")
        client_ip = request.client.host if request.client else "unknown"
        
        print(f"订阅访问请求: {subscription_key}, UA: {user_agent}, IP: {client_ip}")
        
        # 检查订阅访问权限（包含设备限制检查）
        access_result = device_manager.check_subscription_access(
            subscription_key, user_agent, client_ip
        )
        
        if not access_result['allowed']:
            print(f"订阅访问被拒绝: {access_result['message']}")
            
            # 所有失效情况都返回失效的V2Ray配置文件
            # 软件订阅应该返回配置文件而不是HTML页面
            invalid_config = subscription_service.get_invalid_v2ray_config()
            return Response(content=invalid_config, media_type="text/plain", status_code=403)
        
        print(f"订阅访问允许: {subscription_key}")
        
        # 返回有效的V2Ray配置
        v2ray_config = subscription_service.get_v2ray_config()
        print("返回V2Ray配置")
        return Response(content=v2ray_config, media_type="text/plain")
        
    except Exception as e:
        print(f"获取SSR订阅失败: {e}")
        import traceback
        traceback.print_exc()
        subscription_service = SubscriptionService(db)
        invalid_config = subscription_service.get_invalid_v2ray_config()
        return Response(content=invalid_config, media_type="text/plain")

@router.get("/clash/{subscription_key}")
def get_clash_subscription(
    subscription_key: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """获取Clash订阅内容 - 集成设备限制检查"""
    try:
        from app.services.device_manager import DeviceManager
        
        subscription_service = SubscriptionService(db)
        device_manager = DeviceManager(db)
        
        # 获取请求信息
        user_agent = request.headers.get("user-agent", "")
        client_ip = request.client.host if request.client else "unknown"
        
        print(f"Clash订阅访问请求: {subscription_key}, UA: {user_agent}, IP: {client_ip}")
        
        # 检查订阅访问权限（包含设备限制检查）
        access_result = device_manager.check_subscription_access(
            subscription_key, user_agent, client_ip
        )
        
        if not access_result['allowed']:
            print(f"订阅访问被拒绝: {access_result['message']}")
            
            # 所有失效情况都返回失效的Clash配置文件
            # 软件订阅应该返回配置文件而不是HTML页面
            invalid_config = subscription_service.get_invalid_clash_config()
            return Response(content=invalid_config, media_type="text/plain", status_code=403)
        
        print(f"订阅访问允许: {subscription_key}")
        
        # 返回有效的Clash配置
        clash_config = subscription_service.get_clash_config()
        print("返回Clash配置")
        return Response(content=clash_config, media_type="text/plain")
        
    except Exception as e:
        print(f"获取Clash订阅失败: {e}")
        subscription_service = SubscriptionService(db)
        invalid_config = subscription_service.get_invalid_clash_config()
        return Response(content=invalid_config, media_type="text/plain") 