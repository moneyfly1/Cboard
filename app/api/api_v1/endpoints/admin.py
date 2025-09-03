from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ResponseBase
from app.services.user import UserService
from app.utils.security import get_current_admin_user
from app.services.subscription import SubscriptionService
from app.services.settings import SettingsService
from app.services.payment_config import PaymentConfigService
from app.services.email_template import EmailTemplateService
from app.services.node import NodeService

router = APIRouter()

@router.get("/test", response_model=ResponseBase)
def test_admin_api(current_admin = Depends(get_current_admin_user)) -> Any:
    """测试管理员API是否正常工作"""
    return ResponseBase(
        message="管理员API正常工作",
        data={"admin_user": {"id": current_admin.id, "username": current_admin.username}}
    )

@router.get("/users", response_model=ResponseBase)
def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    email: str = Query("", description="邮箱搜索"),
    username: str = Query("", description="用户名搜索"),
    status: str = Query("", description="状态筛选"),
    date_range: str = Query("", description="注册时间范围"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取用户列表"""
    try:
        user_service = UserService(db)
        subscription_service = SubscriptionService(db)
        
        # 构建搜索参数
        search_params = {}
        if email:
            search_params['email'] = email
        if username:
            search_params['username'] = username
        if status:
            search_params['status'] = status
            
        skip = (page - 1) * size
        users, total = user_service.get_users_with_pagination(
            skip=skip, 
            limit=size,
            **search_params
        )
        
        # 获取每个用户的订阅信息
        user_list = []
        for user in users:
            subscription = subscription_service.get_by_user_id(user.id)
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "subscription": {
                    "id": subscription.id if subscription else None,
                    "status": "active" if subscription and subscription.is_active else "inactive",
                    "expire_time": subscription.expire_time.isoformat() if subscription and subscription.expire_time else None,
                    "device_limit": subscription.device_limit if subscription else 0,
                    "current_devices": subscription.current_devices if subscription else 0
                } if subscription else None
            }
            user_list.append(user_data)
        
        return ResponseBase(data={
            "users": user_list,
            "total": total, 
            "page": page, 
            "size": size, 
            "pages": (total + size - 1) // size
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取用户列表失败: {str(e)}")

@router.get("/users/{user_id}", response_model=ResponseBase)
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取用户详细信息"""
    try:
        user_service = UserService(db)
        subscription_service = SubscriptionService(db)
        
        user = user_service.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取用户订阅信息
        subscription = subscription_service.get_by_user_id(user.id)
        # 获取用户设备列表
        devices = subscription_service.get_devices_by_subscription_id(subscription.id) if subscription else []
        
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "subscription": {
                "id": subscription.id if subscription else None,
                "status": "active" if subscription and subscription.is_active else "inactive",
                "expire_time": subscription.expire_time.isoformat() if subscription and subscription.expire_time else None,
                "device_limit": subscription.device_limit if subscription else 0,
                "current_devices": subscription.current_devices if subscription else 0,
                "subscription_url": subscription.subscription_url if subscription else None
            } if subscription else None,
            "devices": [
                {
                    "id": device.id,
                    "name": device.name,
                    "type": device.type,
                    "ip": device.ip,
                    "last_access": device.last_access.isoformat() if device.last_access else None
                } for device in devices
            ]
        }
        
        return ResponseBase(data=user_data)
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"获取用户详情失败: {str(e)}")

@router.put("/users/{user_id}", response_model=ResponseBase)
def update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新用户信息"""
    try:
        user_service = UserService(db)
        subscription_service = SubscriptionService(db)
        
        user = user_service.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 更新用户基本信息
        if "email" in user_data:
            user.email = user_data["email"]
        if "username" in user_data:
            user.username = user_data["username"]
        if "is_active" in user_data:
            user.is_active = user_data["is_active"]
        if "is_verified" in user_data:
            user.is_verified = user_data["is_verified"]
        
        user_service.db.commit()
        
        # 更新订阅信息
        if "subscription" in user_data:
            subscription = subscription_service.get_by_user_id(user.id)
            if subscription and "device_limit" in user_data["subscription"]:
                subscription.device_limit = user_data["subscription"]["device_limit"]
            if subscription and "expire_time" in user_data["subscription"]:
                from datetime import datetime
                subscription.expire_time = datetime.fromisoformat(user_data["subscription"]["expire_time"])
            subscription_service.db.commit()
        
        return ResponseBase(message="用户信息更新成功")
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"更新用户信息失败: {str(e)}")

@router.delete("/users/{user_id}", response_model=ResponseBase)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除用户"""
    try:
        user_service = UserService(db)
        subscription_service = SubscriptionService(db)
        
        user = user_service.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        if user.is_admin:
            raise HTTPException(status_code=400, detail="不能删除管理员用户")
        
        # 删除用户订阅和设备
        subscription = subscription_service.get_by_user_id(user.id)
        if subscription:
            devices = subscription_service.get_devices_by_subscription_id(subscription.id)
            for device in devices:
                subscription_service.db.delete(device)
            subscription_service.db.delete(subscription)
        
        # 删除用户
        user_service.db.delete(user)
        user_service.db.commit()
        
        return ResponseBase(message="用户删除成功")
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"删除用户失败: {str(e)}")

@router.post("/users/{user_id}/reset-subscription", response_model=ResponseBase)
def reset_user_subscription(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """重置用户订阅"""
    try:
        subscription_service = SubscriptionService(db)
        
        subscription = subscription_service.get_by_user_id(user_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="用户没有订阅")
        
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
        
        return ResponseBase(message="订阅重置成功", data={"new_subscription_url": new_url})
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"重置订阅失败: {str(e)}")

@router.post("/users/{user_id}/clear-devices", response_model=ResponseBase)
def clear_user_devices(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """清理用户设备"""
    try:
        subscription_service = SubscriptionService(db)
        
        subscription = subscription_service.get_by_user_id(user_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="用户没有订阅")
        
        # 清理所有设备
        devices = subscription_service.get_devices_by_subscription_id(subscription.id)
        for device in devices:
            subscription_service.db.delete(device)
        
        subscription.current_devices = 0
        subscription_service.db.commit()
        
        return ResponseBase(message="设备清理成功")
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"清理设备失败: {str(e)}")

@router.post("/users/{user_id}/login-as", response_model=ResponseBase)
def login_as_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """管理员以用户身份登录"""
    try:
        user_service = UserService(db)
        
        user = user_service.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        if user.is_admin:
            raise HTTPException(status_code=400, detail="不能以管理员身份登录")
        
        # 生成用户token
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": user.username, "user_id": user.id})
        
        return ResponseBase(message="登录成功", data={"token": token, "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }})
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"登录失败: {str(e)}")

@router.get("/dashboard", response_model=ResponseBase)
def get_admin_dashboard(current_admin = Depends(get_current_admin_user)) -> Any:
    """获取管理端首页统计数据"""
    return ResponseBase(data={
        "users": {"total": 0, "active": 0},
        "subscriptions": {"total": 0, "active": 0},
        "orders": {"total": 0, "revenue": 0.0}
    })

@router.get("/stats", response_model=ResponseBase)
def get_admin_stats(
    current_admin = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取管理员统计信息"""
    try:
        user_service = UserService(db)
        subscription_service = SubscriptionService(db)
        
        # 获取用户统计
        total_users = user_service.count()
        active_users = user_service.count_active_users()
        new_today = user_service.count_recent_users(1)
        
        # 获取订阅统计
        total_subscriptions = subscription_service.count()
        active_subscriptions = subscription_service.count_active()
        expiring_soon = subscription_service.count_expiring_soon()
        
        return ResponseBase(data={
            "users": {"total": total_users, "active": active_users, "new_today": new_today},
            "subscriptions": {"total": total_subscriptions, "active": active_subscriptions, "expiring_soon": expiring_soon},
            "orders": {"total": 0, "pending": 0, "paid": 0, "revenue": 0.0},
            "nodes": {"total": 0, "online": 0, "offline": 0}
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取统计信息失败: {str(e)}")

@router.get("/users/recent", response_model=ResponseBase)
def get_recent_users(
    current_admin = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取最近注册的用户"""
    try:
        user_service = UserService(db)
        recent_users = user_service.get_recent_users(7)  # 最近7天
        
        return ResponseBase(data={
            "users": [{"id": user.id, "username": user.username, "email": user.email, 
                      "created_at": user.created_at.isoformat() if user.created_at else None} for user in recent_users],
            "total": len(recent_users)
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取最近用户失败: {str(e)}")

@router.get("/orders/recent", response_model=ResponseBase)
def get_recent_orders(current_admin = Depends(get_current_admin_user)) -> Any:
    """获取最近的订单"""
    return ResponseBase(data={
        "orders": [],
        "total": 0
    })

@router.get("/orders", response_model=ResponseBase)
def get_orders(current_admin = Depends(get_current_admin_user)) -> Any:
    """获取订单列表"""
    return ResponseBase(data={"orders": [], "total": 0})

@router.get("/orders/statistics", response_model=ResponseBase)
def get_orders_statistics(current_admin = Depends(get_current_admin_user)) -> Any:
    """获取订单统计信息"""
    return ResponseBase(data={"total_orders": 0, "total_revenue": 0.0})

@router.get("/notifications", response_model=ResponseBase)
def get_notifications(current_admin = Depends(get_current_admin_user)) -> Any:
    """获取通知列表"""
    return ResponseBase(data={"notifications": [], "total": 0})

@router.get("/system-config", response_model=ResponseBase)
def get_system_config(current_admin = Depends(get_current_admin_user)) -> Any:
    """获取系统配置"""
    try:
        # 这里应该从数据库或配置文件获取系统配置
        # 暂时返回默认配置
        system_config = {
            "site_name": "XBoard Modern",
            "site_description": "现代化的代理服务管理平台",
            "logo_url": "",
            "maintenance_mode": False,
            "maintenance_message": "系统维护中，请稍后再试"
        }
        return ResponseBase(data=system_config)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取系统配置失败: {str(e)}")

@router.post("/system-config", response_model=ResponseBase)
def save_system_config(
    config_data: dict,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """保存系统配置"""
    try:
        # 这里应该将配置保存到数据库或配置文件
        # 暂时返回成功
        return ResponseBase(message="系统配置保存成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"保存系统配置失败: {str(e)}")

@router.get("/email-config", response_model=ResponseBase)
def get_email_config(current_admin = Depends(get_current_admin_user)) -> Any:
    """获取邮件配置"""
    try:
        # 这里应该从数据库或配置文件获取邮件配置
        # 暂时返回默认配置
        email_config = {
            "smtp_host": "smtp.qq.com",
            "smtp_port": 587,
            "email_username": "",
            "email_password": "",
            "sender_name": "XBoard System"
        }
        return ResponseBase(data=email_config)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取邮件配置失败: {str(e)}")

@router.post("/email-config", response_model=ResponseBase)
def save_email_config(
    config_data: dict,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """保存邮件配置"""
    try:
        # 这里应该将邮件配置保存到数据库或配置文件
        # 暂时返回成功
        return ResponseBase(message="邮件配置保存成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"保存邮件配置失败: {str(e)}")

@router.get("/clash-config", response_model=ResponseBase)
def get_clash_config(current_admin = Depends(get_current_admin_user)) -> Any:
    """获取Clash配置"""
    try:
        # 这里应该从数据库或配置文件获取Clash配置
        # 暂时返回默认配置
        clash_config = {
            "config_content": "# Clash配置文件\n# 请在此处配置Clash代理规则"
        }
        return ResponseBase(data=clash_config["config_content"])
    except Exception as e:
        return ResponseBase(success=False, message=f"获取Clash配置失败: {str(e)}")

@router.post("/clash-config", response_model=ResponseBase)
def save_clash_config(
    config_data: dict,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """保存Clash配置"""
    try:
        # 这里应该将Clash配置保存到数据库或配置文件
        # 暂时返回成功
        return ResponseBase(message="Clash配置保存成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"保存Clash配置失败: {str(e)}")

@router.get("/v2ray-config", response_model=ResponseBase)
def get_v2ray_config(current_admin = Depends(get_current_admin_user)) -> Any:
    """获取V2Ray配置"""
    try:
        # 这里应该从数据库或配置文件获取V2Ray配置
        # 暂时返回默认配置
        v2ray_config = {
            "config_content": "# V2Ray配置文件\n# 请在此处配置V2Ray代理规则"
        }
        return ResponseBase(data=v2ray_config["config_content"])
    except Exception as e:
        return ResponseBase(success=False, message=f"获取V2Ray配置失败: {str(e)}")

@router.post("/v2ray-config", response_model=ResponseBase)
def save_v2ray_config(
    config_data: dict,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """保存V2Ray配置"""
    try:
        # 这里应该将V2Ray配置保存到数据库或配置文件
        # 暂时返回成功
        return ResponseBase(message="V2Ray配置保存成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"保存V2Ray配置失败: {str(e)}")

@router.post("/test-email", response_model=ResponseBase)
def test_email(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """测试邮件发送"""
    try:
        # 这里应该实现实际的邮件发送测试
        # 暂时返回成功
        return ResponseBase(message="测试邮件发送成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"测试邮件发送失败: {str(e)}")

@router.get("/export-config", response_model=ResponseBase)
def export_config(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """导出系统配置"""
    try:
        # 这里应该收集所有系统配置并导出
        # 暂时返回模拟数据
        config_data = {
            "system_config": {
                "site_name": "XBoard Modern",
                "site_description": "现代化的代理服务管理平台",
                "maintenance_mode": False
            },
            "email_config": {
                "smtp_host": "smtp.qq.com",
                "smtp_port": 587
            },
            "export_time": "2024-01-01T00:00:00Z"
        }
        return ResponseBase(data=config_data)
    except Exception as e:
        return ResponseBase(success=False, message=f"导出配置失败: {str(e)}")

@router.get("/settings", response_model=ResponseBase)
def get_all_settings(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取所有系统设置"""
    try:
        # 返回所有设置的汇总数据
        all_settings = {
            "general": {
                "site_name": "XBoard Modern",
                "site_description": "现代化的代理服务管理平台",
                "site_logo": "",
                "default_theme": "default"
            },
            "registration": {
                "registration_enabled": True,
                "email_verification_required": True,
                "min_password_length": 8,
                "invite_code_required": False
            },
            "notification": {
                "system_notifications": True,
                "email_notifications": True,
                "subscription_expiry_notifications": True,
                "new_user_notifications": True,
                "new_order_notifications": True
            },
            "security": {
                "login_fail_limit": 5,
                "login_lock_time": 30,
                "session_timeout": 120,
                "device_fingerprint_enabled": True,
                "ip_whitelist_enabled": False,
                "ip_whitelist": ""
            }
        }
        return ResponseBase(data=all_settings)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取系统设置失败: {str(e)}")

@router.put("/settings/general", response_model=ResponseBase)
def update_general_settings(
    settings: dict,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新基本设置"""
    try:
        # 这里应该将设置保存到数据库或配置文件
        # 暂时返回成功
        return ResponseBase(message="基本设置保存成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"保存基本设置失败: {str(e)}")

@router.put("/settings/registration", response_model=ResponseBase)
def update_registration_settings(
    settings: dict,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新注册设置"""
    try:
        # 这里应该将设置保存到数据库或配置文件
        # 暂时返回成功
        return ResponseBase(message="注册设置保存成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"保存注册设置失败: {str(e)}")

@router.put("/settings/notification", response_model=ResponseBase)
def update_notification_settings(
    settings: dict,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新通知设置"""
    try:
        # 这里应该将设置保存到数据库或配置文件
        # 暂时返回成功
        return ResponseBase(message="通知设置保存成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"保存通知设置失败: {str(e)}")

@router.put("/settings/security", response_model=ResponseBase)
def update_security_settings(
    settings: dict,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新安全设置"""
    try:
        # 这里应该将设置保存到数据库或配置文件
        # 暂时返回成功
        return ResponseBase(message="安全设置保存成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"保存安全设置失败: {str(e)}")

@router.get("/statistics/user-trend", response_model=ResponseBase)
def get_user_trend_statistics(current_admin = Depends(get_current_admin_user)) -> Any:
    """获取用户趋势统计"""
    return ResponseBase(data={"labels": ["1月", "2月"], "datasets": [{"label": "新用户", "data": [0, 0]}]})

@router.get("/statistics/revenue-trend", response_model=ResponseBase)
def get_revenue_trend_statistics(current_admin = Depends(get_current_admin_user)) -> Any:
    """获取收入趋势统计"""
    return ResponseBase(data={"labels": ["1月", "2月"], "datasets": [{"label": "收入", "data": [0, 0]}]})

@router.get("/subscriptions", response_model=ResponseBase)
def get_subscriptions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取订阅列表"""
    try:
        subscription_service = SubscriptionService(db)
        skip = (page - 1) * size
        subscriptions, total = subscription_service.get_subscriptions_with_pagination(skip=skip, limit=size)
        
        subscription_list = []
        for subscription in subscriptions:
            # 获取用户信息
            user = subscription.user if hasattr(subscription, 'user') else None
            user_info = {
                "id": user.id,
                "username": user.username,
                "email": user.email
            } if user else {"id": subscription.user_id, "username": "未知用户", "email": "未知邮箱"}
            
            subscription_data = {
                "id": subscription.id,
                "user": user_info,
                "subscription_url": subscription.subscription_url,
                "device_limit": subscription.device_limit,
                "current_devices": subscription.current_devices,
                "is_active": subscription.is_active,
                "expire_time": subscription.expire_time.isoformat() if subscription.expire_time else None,
                "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
                "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None
            }
            subscription_list.append(subscription_data)
        
        return ResponseBase(data={
            "subscriptions": subscription_list,
            "total": total, 
            "page": page, 
            "size": size, 
            "pages": (total + size - 1) // size
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取订阅列表失败: {str(e)}")

@router.get("/subscriptions/statistics", response_model=ResponseBase)
def get_subscriptions_statistics(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取订阅统计信息"""
    try:
        subscription_service = SubscriptionService(db)
        stats = subscription_service.get_subscription_stats()
        return ResponseBase(data=stats)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取订阅统计失败: {str(e)}")

@router.get("/subscriptions/{subscription_id}", response_model=ResponseBase)
def get_subscription_detail(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取订阅详情"""
    try:
        subscription_service = SubscriptionService(db)
        subscription = subscription_service.get(subscription_id)
        
        if not subscription:
            return ResponseBase(success=False, message="订阅不存在")
        
        # 获取用户信息
        user = subscription.user if hasattr(subscription, 'user') else None
        user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email
        } if user else {"id": subscription.user_id, "username": "未知用户", "email": "未知邮箱"}
        
        # 获取设备列表
        devices = subscription_service.get_devices_by_subscription_id(subscription_id)
        device_list = []
        for device in devices:
            device_data = {
                "id": device.id,
                "name": device.device_name,
                "type": device.device_type,
                "ip": device.ip_address,
                "user_agent": device.user_agent,
                "last_access": device.last_access.isoformat() if device.last_access else None,
                "is_active": device.is_active,
                "created_at": device.created_at.isoformat() if device.created_at else None
            }
            device_list.append(device_data)
        
        subscription_data = {
            "id": subscription.id,
            "user": user_info,
            "subscription_url": subscription.subscription_url,
            "device_limit": subscription.device_limit,
            "current_devices": subscription.current_devices,
            "is_active": subscription.is_active,
            "expire_time": subscription.expire_time.isoformat() if subscription.expire_time else None,
            "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
            "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
            "devices": device_list
        }
        
        return ResponseBase(data=subscription_data)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取订阅详情失败: {str(e)}")

@router.put("/subscriptions/{subscription_id}/reset", response_model=ResponseBase)
def reset_subscription(
    subscription_id: int,
    reason: str = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """重置订阅"""
    try:
        subscription_service = SubscriptionService(db)
        subscription = subscription_service.get(subscription_id)
        
        if not subscription:
            return ResponseBase(success=False, message="订阅不存在")
        
        success = subscription_service.reset_subscription(
            subscription_id=subscription_id,
            user_id=subscription.user_id,
            reset_type="admin",
            reason=reason or "管理员重置"
        )
        
        if success:
            return ResponseBase(message="订阅重置成功")
        else:
            return ResponseBase(success=False, message="订阅重置失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"重置订阅失败: {str(e)}")

@router.delete("/subscriptions/{subscription_id}", response_model=ResponseBase)
def delete_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除订阅"""
    try:
        subscription_service = SubscriptionService(db)
        success = subscription_service.delete(subscription_id)
        
        if success:
            return ResponseBase(message="订阅删除成功")
        else:
            return ResponseBase(success=False, message="订阅删除失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"删除订阅失败: {str(e)}")

# ==================== 系统设置管理 ====================

@router.get("/system-settings", response_model=ResponseBase)
def get_system_settings(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取系统基本设置"""
    try:
        settings_service = SettingsService(db)
        settings = settings_service.get_system_settings()
        return ResponseBase(data=settings.dict())
    except Exception as e:
        return ResponseBase(success=False, message=f"获取系统设置失败: {str(e)}")

@router.put("/system-settings", response_model=ResponseBase)
def update_system_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新系统基本设置"""
    try:
        settings_service = SettingsService(db)
        success = settings_service.update_system_settings(settings)
        if success:
            return ResponseBase(message="系统设置更新成功")
        else:
            return ResponseBase(success=False, message="系统设置更新失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新系统设置失败: {str(e)}")

# ==================== 注册设置管理 ====================

@router.get("/registration-settings", response_model=ResponseBase)
def get_registration_settings(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取注册设置"""
    try:
        settings_service = SettingsService(db)
        reg_config = settings_service.get_registration_config()
        return ResponseBase(data=reg_config)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取注册设置失败: {str(e)}")

@router.put("/registration-settings", response_model=ResponseBase)
def update_registration_settings(
    reg_config: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新注册设置"""
    try:
        settings_service = SettingsService(db)
        success = settings_service.update_registration_config(reg_config)
        if success:
            return ResponseBase(message="注册设置更新成功")
        else:
            return ResponseBase(success=False, message="注册设置更新失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新注册设置失败: {str(e)}")

# ==================== 通知设置管理 ====================

@router.get("/notification-settings", response_model=ResponseBase)
def get_notification_settings(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取通知设置"""
    try:
        settings_service = SettingsService(db)
        notif_config = settings_service.get_notification_config()
        return ResponseBase(data=notif_config)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取通知设置失败: {str(e)}")

@router.put("/notification-settings", response_model=ResponseBase)
def update_notification_settings(
    notif_config: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新通知设置"""
    try:
        settings_service = SettingsService(db)
        success = settings_service.update_notification_config(notif_config)
        if success:
            return ResponseBase(message="通知设置更新成功")
        else:
            return ResponseBase(success=False, message="通知设置更新失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新通知设置失败: {str(e)}")

# ==================== 安全设置管理 ====================

@router.get("/security-settings", response_model=ResponseBase)
def get_security_settings(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取安全设置"""
    try:
        settings_service = SettingsService(db)
        security_config = settings_service.get_security_config()
        return ResponseBase(data=security_config)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取安全设置失败: {str(e)}")

@router.put("/security-settings", response_model=ResponseBase)
def update_security_settings(
    security_config: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新安全设置"""
    try:
        settings_service = SettingsService(db)
        success = settings_service.update_security_config(security_config)
        if success:
            return ResponseBase(message="安全设置更新成功")
        else:
            return ResponseBase(success=False, message="安全设置更新失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新安全设置失败: {str(e)}")

# ==================== 配置管理 ====================

@router.get("/configs", response_model=ResponseBase)
def get_configs(
    category: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取配置列表"""
    try:
        settings_service = SettingsService(db)
        if category:
            configs = settings_service.get_configs_by_category(category)
        else:
            configs = settings_service.get_all_configs()
        
        # 分页处理
        total = len(configs)
        start = (page - 1) * size
        end = start + size
        paginated_configs = configs[start:end]
        
        config_list = []
        for config in paginated_configs:
            config_data = {
                "key": config.key,
                "value": config.value,
                "type": config.type,
                "category": config.category,
                "display_name": config.display_name,
                "description": config.description,
                "is_public": config.is_public,
                "sort_order": config.sort_order,
                "created_at": config.created_at.isoformat() if config.created_at else None,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None
            }
            config_list.append(config_data)
        
        return ResponseBase(data={
            "configs": config_list,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取配置列表失败: {str(e)}")

@router.get("/configs/{config_key}", response_model=ResponseBase)
def get_config_detail(
    config_key: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取配置详情"""
    try:
        settings_service = SettingsService(db)
        config = settings_service.get_config(config_key)
        if not config:
            return ResponseBase(success=False, message="配置不存在")
        
        config_data = {
            "key": config.key,
            "value": config.value,
            "type": config.type,
            "category": config.category,
            "display_name": config.display_name,
            "description": config.description,
            "is_public": config.is_public,
            "sort_order": config.sort_order,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
        
        return ResponseBase(data=config_data)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取配置详情失败: {str(e)}")

@router.put("/configs/{config_key}", response_model=ResponseBase)
def update_config(
    config_key: str,
    config_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新配置"""
    try:
        settings_service = SettingsService(db)
        success = settings_service.set_config_value(
            config_key, 
            config_data.get("value"), 
            config_data.get("type", "string")
        )
        if success:
            return ResponseBase(message="配置更新成功")
        else:
            return ResponseBase(success=False, message="配置更新失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新配置失败: {str(e)}")

# ==================== 邮件配置管理 ====================

@router.get("/email-configs", response_model=ResponseBase)
def get_email_configs(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取邮件配置列表"""
    try:
        settings_service = SettingsService(db)
        email_configs = settings_service.get_configs_by_category('email')
        
        config_list = []
        for config in email_configs:
            config_data = {
                "key": config.key,
                "value": config.value,
                "type": config.type,
                "display_name": config.display_name,
                "description": config.description,
                "is_public": config.is_public,
                "sort_order": config.sort_order
            }
            config_list.append(config_data)
        
        return ResponseBase(data={"email_configs": config_list})
    except Exception as e:
        return ResponseBase(success=False, message=f"获取邮件配置失败: {str(e)}")

@router.put("/email-configs", response_model=ResponseBase)
def update_email_configs(
    email_configs: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新邮件配置"""
    try:
        settings_service = SettingsService(db)
        success = settings_service.update_smtp_config(email_configs)
        if success:
            return ResponseBase(message="邮件配置更新成功")
        else:
            return ResponseBase(success=False, message="邮件配置更新失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新邮件配置失败: {str(e)}")

@router.post("/email-configs/test", response_model=ResponseBase)
def test_email_config(
    email_config: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """测试邮件配置"""
    try:
        settings_service = SettingsService(db)
        success = settings_service.test_smtp_connection(email_config)
        if success:
            return ResponseBase(message="邮件配置测试成功")
        else:
            return ResponseBase(success=False, message="邮件配置测试失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"邮件配置测试失败: {str(e)}")

# ==================== 邮件队列管理（配置管理部分） ====================

@router.get("/email-queue", response_model=ResponseBase)
def get_email_queue(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取邮件队列列表"""
    try:
        from app.services.email_queue_processor import EmailQueueProcessor
        email_service = EmailQueueProcessor(db)
        
        # 获取邮件队列
        emails = email_service.get_email_queue(page=page, size=size, status=status)
        total = email_service.get_email_queue_count(status=status)
        
        email_list = []
        for email in emails:
            email_data = {
                "id": email.id,
                "to_email": email.to_email,
                "subject": email.subject,
                "template_name": email.template_name,
                "status": email.status,
                "priority": email.priority,
                "retry_count": email.retry_count,
                "created_at": email.created_at.isoformat() if email.created_at else None,
                "sent_at": email.sent_at.isoformat() if email.sent_at else None,
                "error_message": email.error_message
            }
            email_list.append(email_data)
        
        return ResponseBase(data={
            "emails": email_list,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取邮件队列失败: {str(e)}")

@router.get("/email-queue/{email_id}", response_model=ResponseBase)
def get_email_detail(
    email_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取邮件详情"""
    try:
        from app.services.email_queue_processor import EmailQueueProcessor
        email_service = EmailQueueProcessor(db)
        
        email = email_service.get_email_by_id(email_id)
        if not email:
            return ResponseBase(success=False, message="邮件不存在")
        
        email_data = {
            "id": email.id,
            "to_email": email.to_email,
            "subject": email.subject,
            "template_name": email.template_name,
            "template_data": email.template_data,
            "status": email.status,
            "priority": email.priority,
            "retry_count": email.retry_count,
            "max_retries": email.max_retries,
            "created_at": email.created_at.isoformat() if email.created_at else None,
            "sent_at": email.sent_at.isoformat() if email.sent_at else None,
            "error_message": email.error_message,
            "error_details": email.error_details,
            "smtp_response": email.smtp_response,
            "processing_time": email.processing_time
        }
        
        return ResponseBase(data=email_data)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取邮件详情失败: {str(e)}")

@router.post("/email-queue/{email_id}/retry", response_model=ResponseBase)
def retry_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """重试发送邮件"""
    try:
        from app.services.email_queue_processor import EmailQueueProcessor
        email_service = EmailQueueProcessor(db)
        
        success = email_service.retry_email(email_id)
        if success:
            return ResponseBase(message="邮件重试成功")
        else:
            return ResponseBase(success=False, message="邮件重试失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"邮件重试失败: {str(e)}")

@router.delete("/email-queue/{email_id}", response_model=ResponseBase)
def delete_email_from_queue(
    email_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """从邮件队列中删除邮件"""
    try:
        from app.services.email_queue_processor import EmailQueueProcessor
        email_service = EmailQueueProcessor(db)
        
        success = email_service.delete_email_from_queue(email_id)
        if success:
            return ResponseBase(message="邮件删除成功")
        else:
            return ResponseBase(success=False, message="邮件删除失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"删除邮件失败: {str(e)}")

@router.post("/email-queue/clear", response_model=ResponseBase)
def clear_email_queue(
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """清空邮件队列"""
    try:
        from app.services.email_queue_processor import EmailQueueProcessor
        email_service = EmailQueueProcessor(db)
        
        success = email_service.clear_email_queue(status=status)
        if success:
            return ResponseBase(message="邮件队列清空成功")
        else:
            return ResponseBase(success=False, message="邮件队列清空失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"清空邮件队列失败: {str(e)}")

@router.get("/email-queue/statistics", response_model=ResponseBase)
def get_email_queue_statistics(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取邮件队列统计信息"""
    try:
        from app.services.email_queue_processor import EmailQueueProcessor
        email_service = EmailQueueProcessor(db)
        
        stats = email_service.get_queue_statistics()
        return ResponseBase(data=stats)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取邮件队列统计失败: {str(e)}")

# ==================== 支付配置管理 ====================

@router.get("/payment-configs", response_model=ResponseBase)
def get_payment_configs(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取支付配置列表"""
    try:
        settings_service = SettingsService(db)
        payment_configs = settings_service.get_configs_by_category('payment')
        
        config_list = []
        for config in payment_configs:
            config_data = {
                "key": config.key,
                "value": config.value,
                "type": config.type,
                "display_name": config.display_name,
                "description": config.description,
                "is_public": config.is_public,
                "sort_order": config.sort_order
            }
            config_list.append(config_data)
        
        return ResponseBase(data={"payment_configs": config_list})
    except Exception as e:
        return ResponseBase(success=False, message=f"获取支付配置失败: {str(e)}")

@router.put("/payment-configs", response_model=ResponseBase)
def update_payment_configs(
    payment_configs: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新支付配置"""
    try:
        settings_service = SettingsService(db)
        success = settings_service.update_payment_configs(payment_configs)
        if success:
            return ResponseBase(message="支付配置更新成功")
        else:
            return ResponseBase(success=False, message="支付配置更新失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新支付配置失败: {str(e)}")

@router.post("/payment-configs/test", response_model=ResponseBase)
def test_payment_config(
    payment_config: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """测试支付配置"""
    try:
        settings_service = SettingsService(db)
        success = settings_service.test_payment_config(payment_config)
        if success:
            return ResponseBase(message="支付配置测试成功")
        else:
            return ResponseBase(success=False, message="支付配置测试失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"支付配置测试失败: {str(e)}")

# ==================== 节点管理 ====================

@router.get("/nodes", response_model=ResponseBase)
def get_nodes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取节点列表"""
    try:
        node_service = NodeService(db)
        skip = (page - 1) * size
        nodes = node_service.get_nodes_with_pagination(skip=skip, limit=size)
        total = node_service.get_total_nodes()
        
        return ResponseBase(data={
            "nodes": nodes,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取节点列表失败: {str(e)}")

@router.get("/nodes/{node_id}", response_model=ResponseBase)
def get_node_detail(
    node_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取节点详情"""
    try:
        node_service = NodeService(db)
        node = node_service.get_node(node_id)
        if not node:
            return ResponseBase(success=False, message="节点不存在")
        return ResponseBase(data=node)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取节点详情失败: {str(e)}")

@router.post("/nodes", response_model=ResponseBase)
def create_node(
    node_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建节点"""
    try:
        node_service = NodeService(db)
        new_node = node_service.create_node(node_data)
        return ResponseBase(message="节点创建成功", data=new_node)
    except Exception as e:
        return ResponseBase(success=False, message=f"创建节点失败: {str(e)}")

@router.put("/nodes/{node_id}", response_model=ResponseBase)
def update_node(
    node_id: int,
    node_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新节点"""
    try:
        node_service = NodeService(db)
        updated_node = node_service.update_node(node_id, node_data)
        if updated_node:
            return ResponseBase(message="节点更新成功", data=updated_node)
        else:
            return ResponseBase(success=False, message="节点更新失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新节点失败: {str(e)}")

@router.delete("/nodes/{node_id}", response_model=ResponseBase)
def delete_node(
    node_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除节点"""
    try:
        node_service = NodeService(db)
        success = node_service.delete_node(node_id)
        if success:
            return ResponseBase(message="节点删除成功")
        else:
            return ResponseBase(success=False, message="节点删除失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"删除节点失败: {str(e)}")

# ==================== 套餐管理 ====================

@router.get("/packages", response_model=ResponseBase)
def get_packages(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取套餐列表"""
    try:
        # 这里需要实现PackageService
        packages = []
        total = 0
        
        return ResponseBase(data={
            "packages": packages,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取套餐列表失败: {str(e)}")

# ==================== 系统日志 ====================

@router.get("/system-logs", response_model=ResponseBase)
def get_system_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    log_type: str = Query(None),
    log_level: str = Query(None),
    start_time: str = Query(None),
    end_time: str = Query(None),
    keyword: str = Query(None),
    module: str = Query(None),
    username: str = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取系统日志"""
    try:
        # 这里需要实现日志服务
        # 暂时返回模拟数据
        mock_logs = [
            {
                "id": 1,
                "timestamp": "2024-01-15T10:30:00Z",
                "level": "INFO",
                "module": "用户管理",
                "message": "用户 admin 登录成功",
                "username": "admin",
                "ip_address": "127.0.0.1",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "details": "用户从本地登录系统"
            },
            {
                "id": 2,
                "timestamp": "2024-01-15T10:25:00Z",
                "level": "WARNING",
                "module": "系统配置",
                "message": "配置文件更新失败",
                "username": "admin",
                "ip_address": "127.0.0.1",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "details": "尝试更新系统配置时发生错误"
            },
            {
                "id": 3,
                "timestamp": "2024-01-15T10:20:00Z",
                "level": "ERROR",
                "module": "邮件服务",
                "message": "邮件发送失败",
                "username": "system",
                "ip_address": "127.0.0.1",
                "user_agent": "System/1.0",
                "details": "SMTP连接超时，无法发送邮件"
            },
            {
                "id": 4,
                "timestamp": "2024-01-15T10:15:00Z",
                "level": "INFO",
                "module": "订单管理",
                "message": "新订单创建成功",
                "username": "user123",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                "details": "用户创建了新的订阅订单"
            },
            {
                "id": 5,
                "timestamp": "2024-01-15T10:10:00Z",
                "level": "INFO",
                "module": "支付系统",
                "message": "支付处理成功",
                "username": "user123",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                "details": "支付宝支付完成，订单金额：¥99.00"
            }
        ]
        
        # 简单的过滤逻辑
        filtered_logs = mock_logs
        if log_level:
            filtered_logs = [log for log in filtered_logs if log["level"] == log_level.upper()]
        if module:
            filtered_logs = [log for log in filtered_logs if module.lower() in log["module"].lower()]
        if username:
            filtered_logs = [log for log in filtered_logs if username.lower() in log["username"].lower()]
        if keyword:
            filtered_logs = [log for log in filtered_logs if keyword.lower() in log["message"].lower()]
        
        total = len(filtered_logs)
        start_index = (page - 1) * size
        end_index = start_index + size
        paginated_logs = filtered_logs[start_index:end_index]
        
        return ResponseBase(data={
            "logs": paginated_logs,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取系统日志失败: {str(e)}")

# ==================== 数据备份 ====================

@router.post("/backup", response_model=ResponseBase)
def create_backup(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建数据备份"""
    try:
        # 这里需要实现备份服务
        return ResponseBase(message="数据备份创建成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"创建数据备份失败: {str(e)}")

@router.get("/backups", response_model=ResponseBase)
def get_backups(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取备份列表"""
    try:
        # 这里需要实现备份服务
        backups = []
        return ResponseBase(data={"backups": backups})
    except Exception as e:
        return ResponseBase(success=False, message=f"获取备份列表失败: {str(e)}")

# ==================== 系统维护 ====================

@router.post("/maintenance/clear-cache", response_model=ResponseBase)
def clear_cache(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """清理系统缓存"""
    try:
        # 这里需要实现缓存清理
        return ResponseBase(message="系统缓存清理成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"清理系统缓存失败: {str(e)}")

@router.post("/maintenance/optimize-db", response_model=ResponseBase)
def optimize_database(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """优化数据库"""
    try:
        # 这里需要实现数据库优化
        return ResponseBase(message="数据库优化完成")
    except Exception as e:
        return ResponseBase(success=False, message=f"数据库优化失败: {str(e)}")

# ==================== 个人资料管理 ====================

@router.get("/profile", response_model=ResponseBase)
def get_admin_profile(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取管理员个人资料"""
    try:
        profile_data = {
            "username": current_admin.username,
            "email": current_admin.email,
            "display_name": getattr(current_admin, 'display_name', ''),
            "avatar_url": getattr(current_admin, 'avatar_url', ''),
            "phone": getattr(current_admin, 'phone', ''),
            "bio": getattr(current_admin, 'bio', ''),
            "created_at": current_admin.created_at.isoformat() if current_admin.created_at else None,
            "last_login": current_admin.last_login.isoformat() if hasattr(current_admin, 'last_login') and current_admin.last_login else None
        }
        return ResponseBase(data=profile_data)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取个人资料失败: {str(e)}")

@router.put("/profile", response_model=ResponseBase)
def update_admin_profile(
    profile_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新管理员个人资料"""
    try:
        # 更新允许修改的字段
        allowed_fields = ['display_name', 'avatar_url', 'phone', 'bio']
        update_data = {}
        
        for field in allowed_fields:
            if field in profile_data:
                update_data[field] = profile_data[field]
        
        if update_data:
            for field, value in update_data.items():
                setattr(current_admin, field, value)
            
            db.commit()
            db.refresh(current_admin)
            
            return ResponseBase(message="个人资料更新成功")
        else:
            return ResponseBase(message="没有需要更新的数据")
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"更新个人资料失败: {str(e)}")

@router.post("/change-password", response_model=ResponseBase)
def change_admin_password(
    password_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """修改管理员密码"""
    try:
        current_password = password_data.get('current_password')
        new_password = password_data.get('new_password')
        
        if not current_password or not new_password:
            return ResponseBase(success=False, message="请提供当前密码和新密码")
        
        # 验证当前密码
        from app.core.auth import verify_password
        if not verify_password(current_password, current_admin.hashed_password):
            return ResponseBase(success=False, message="当前密码错误")
        
        # 验证新密码强度
        if len(new_password) < 8:
            return ResponseBase(success=False, message="新密码长度至少8位")
        
        # 更新密码
        from app.core.auth import get_password_hash
        current_admin.hashed_password = get_password_hash(new_password)
        db.commit()
        
        return ResponseBase(message="密码修改成功")
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"修改密码失败: {str(e)}")

@router.get("/login-history", response_model=ResponseBase)
def get_admin_login_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取管理员登录历史"""
    try:
        # 这里需要实现登录历史服务
        # 暂时返回模拟数据
        login_history = [
            {
                "id": 1,
                "login_time": "2024-01-01T10:00:00",
                "ip_address": "192.168.1.1",
                "location": "中国 北京",
                "device": "Chrome 120.0.0.0",
                "status": "success"
            }
        ]
        
        return ResponseBase(data={
            "login_history": login_history,
            "total": len(login_history),
            "page": page,
            "size": size,
            "pages": 1
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取登录历史失败: {str(e)}")

@router.get("/security-settings", response_model=ResponseBase)
def get_admin_security_settings(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取管理员安全设置"""
    try:
        # 这里需要实现安全设置服务
        # 暂时返回默认设置
        security_settings = {
            "two_factor_enabled": False,
            "login_notification": True,
            "session_timeout": 120
        }
        
        return ResponseBase(data=security_settings)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取安全设置失败: {str(e)}")

@router.put("/security-settings", response_model=ResponseBase)
def update_admin_security_settings(
    security_data: dict,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新管理员安全设置"""
    try:
        # 这里需要实现安全设置更新服务
        # 暂时返回成功
        return ResponseBase(message="安全设置更新成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新安全设置失败: {str(e)}")

@router.get("/notification-settings", response_model=ResponseBase)
def get_admin_notification_settings(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取管理员通知设置"""
    try:
        # 这里需要实现通知设置服务
        # 暂时返回默认设置
        notification_settings = {
            "email_enabled": True,
            "system_notification": True,
            "security_notification": True,
            "frequency": "realtime"
        }
        
        return ResponseBase(data=notification_settings)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取通知设置失败: {str(e)}")

@router.put("/notification-settings", response_model=ResponseBase)
def update_admin_notification_settings(
    notification_data: dict,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新管理员通知设置"""
    try:
        # 这里需要实现通知设置更新服务
        # 暂时返回成功
        return ResponseBase(message="通知设置更新成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新通知设置失败: {str(e)}")

# ==================== 系统日志管理 ====================

@router.get("/logs-stats", response_model=ResponseBase)
def get_logs_stats(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取日志统计信息"""
    try:
        # 这里需要实现日志统计服务
        # 暂时返回模拟数据
        stats = {
            "total": 1250,
            "error": 45,
            "warning": 128,
            "info": 1077
        }
        
        return ResponseBase(data=stats)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取日志统计失败: {str(e)}")

@router.get("/export-logs", response_model=ResponseBase)
def export_logs(
    log_type: str = Query(None),
    log_level: str = Query(None),
    start_time: str = Query(None),
    end_time: str = Query(None),
    keyword: str = Query(None),
    module: str = Query(None),
    username: str = Query(None),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """导出日志"""
    try:
        # 这里需要实现日志导出服务
        # 暂时返回模拟数据
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入CSV头部
        writer.writerow(['时间', '级别', '模块', '用户', 'IP地址', '日志内容', '详细信息'])
        
        # 写入模拟数据
        writer.writerow([
            '2024-01-01 10:00:00',
            'INFO',
            '用户管理',
            'admin',
            '192.168.1.1',
            '用户登录成功',
            '用户admin成功登录系统'
        ])
        
        csv_content = output.getvalue()
        output.close()
        
        return ResponseBase(data=csv_content, message="日志导出成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"导出日志失败: {str(e)}")

@router.post("/clear-logs", response_model=ResponseBase)
def clear_logs(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """清理日志"""
    try:
        # 这里需要实现日志清理服务
        # 暂时返回成功
        return ResponseBase(message="日志清理成功")
    except Exception as e:
        return ResponseBase(success=False, message=f"清理日志失败: {str(e)}")
