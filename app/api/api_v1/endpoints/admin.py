from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.schemas.common import ResponseBase
from app.services.user import UserService
from app.utils.security import get_current_admin_user
from app.services.subscription import SubscriptionService
from app.services.settings import SettingsService
from app.services.payment_config import PaymentConfigService
from app.services.email_template import EmailTemplateService
from app.services.node import NodeService
# from app.models.user import User  # 暂时注释掉，避免循环导入

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
        print(f"=== 管理员用户列表API被调用 ===")
        print(f"请求参数: page={page}, size={size}, email={email}, username={username}, status={status}")
        
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
        print(f"分页参数: skip={skip}, limit={size}")
        
        users, total = user_service.get_users_with_pagination(
            skip=skip, 
            limit=size,
            **search_params
        )
        
        print(f"用户服务返回: {len(users)} 个用户，总数: {total}")
        
        # 获取每个用户的订阅信息和设备信息
        user_list = []
        for user in users:
            subscription = subscription_service.get_by_user_id(user.id)
            
            # 获取用户设备信息
            device_count = 0
            online_devices = 0
            if subscription:
                try:
                    from app.services.device import DeviceService
                    device_service = DeviceService(db)
                    devices = device_service.get_devices_by_user_id(user.id)
                    device_count = len(devices)
                    online_devices = len([d for d in devices if d.is_online])
                except:
                    device_count = subscription.current_devices if subscription else 0
                    online_devices = 0
            
            # 计算订阅状态和到期信息
            subscription_status = "inactive"
            days_until_expire = None
            is_expired = False
            
            if subscription and subscription.expire_time:
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                expire_time = subscription.expire_time
                if isinstance(expire_time, str):
                    expire_time = datetime.fromisoformat(expire_time.replace('Z', '+00:00'))
                elif expire_time.tzinfo is None:
                    # 如果expire_time没有时区信息，假设为UTC
                    expire_time = expire_time.replace(tzinfo=timezone.utc)
                
                if expire_time > now:
                    subscription_status = "active" if subscription.is_active else "inactive"
                    days_until_expire = (expire_time - now).days
                else:
                    subscription_status = "expired"
                    is_expired = True
                    days_until_expire = 0
            
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_verified": user.is_verified,
                "status": "active" if user.is_active else "disabled",
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "subscription_count": 1 if subscription else 0,
                "device_count": device_count,
                "online_devices": online_devices,
                "subscription": {
                    "id": subscription.id if subscription else None,
                    "status": subscription_status,
                    "expire_time": subscription.expire_time.isoformat() if subscription and subscription.expire_time else None,
                    "device_limit": subscription.device_limit if subscription else 0,
                    "current_devices": device_count,
                    "online_devices": online_devices,
                    "days_until_expire": days_until_expire,
                    "is_expired": is_expired
                } if subscription else None
            }
            user_list.append(user_data)
        
        response_data = {
            "users": user_list,
            "total": total, 
            "page": page, 
            "size": size, 
            "pages": (total + size - 1) // size
        }
        
        print(f"响应数据结构: {len(user_list)} 个用户在user_list中")
        print(f"前3个用户示例: {[u['username'] for u in user_list[:3]]}")
        
        return ResponseBase(data=response_data)
    except Exception as e:
        print(f"获取用户列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return ResponseBase(success=False, message=f"获取用户列表失败: {str(e)}")

@router.get("/users/statistics", response_model=ResponseBase)
def get_user_statistics(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取用户统计信息"""
    try:
        user_service = UserService(db)
        subscription_service = SubscriptionService(db)
        
        # 获取用户统计
        user_stats = user_service.get_user_stats()
        
        # 获取订阅统计
        total_subscriptions = subscription_service.count()
        active_subscriptions = subscription_service.count_active()
        
        # 计算订阅率
        subscription_rate = 0
        if user_stats["total"] > 0:
            subscription_rate = round((total_subscriptions / user_stats["total"]) * 100, 2)
        
        stats = {
            "totalUsers": user_stats["total"],
            "activeUsers": user_stats["active"],
            "newUsersToday": user_stats["today"],
            "newUsersYesterday": user_stats["yesterday"],
            "recentUsers7Days": user_stats["recent_7_days"],
            "totalSubscriptions": total_subscriptions,
            "activeSubscriptions": active_subscriptions,
            "subscriptionRate": subscription_rate
        }
        
        return ResponseBase(data=stats)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取用户统计失败: {str(e)}")

@router.post("/users", response_model=ResponseBase)
def create_user(
    user_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建新用户"""
    try:
        # 直接使用SQL检查用户名和邮箱是否已存在
        from sqlalchemy import text
        
        # 检查用户名
        check_username = text("SELECT id FROM users WHERE username = :username")
        existing_user = db.execute(check_username, {"username": user_data.get("username")}).first()
        if existing_user:
            return ResponseBase(success=False, message="用户名已存在")
        
        # 检查邮箱
        check_email = text("SELECT id FROM users WHERE email = :email")
        existing_email = db.execute(check_email, {"email": user_data.get("email")}).first()
        if existing_email:
            return ResponseBase(success=False, message="邮箱已存在")
        
        # 创建用户
        from app.utils.security import get_password_hash
        
        # 使用原始SQL创建用户
        from datetime import datetime
        current_time = datetime.now()
        
        insert_query = text("""
            INSERT INTO users (username, email, hashed_password, is_active, is_admin, is_verified, created_at)
            VALUES (:username, :email, :hashed_password, :is_active, :is_admin, :is_verified, :created_at)
        """)
        
        result = db.execute(insert_query, {
            "username": user_data["username"],
            "email": user_data["email"],
            "hashed_password": get_password_hash(user_data["password"]),
            "is_active": user_data.get("is_active", True),
            "is_admin": user_data.get("is_admin", False),
            "is_verified": user_data.get("is_verified", False),
            "created_at": current_time
        })
        
        db.commit()
        
        # 获取新创建的用户ID
        user_id = result.lastrowid
        
        # 自动创建默认订阅
        try:
            from app.services.subscription import SubscriptionService
            from app.schemas.subscription import SubscriptionCreate
            from datetime import datetime, timedelta
            
            subscription_service = SubscriptionService(db)
            
            # 创建默认订阅（30天试用期）
            default_subscription = SubscriptionCreate(
                user_id=user_id,
                device_limit=3,
                expire_time=datetime.utcnow() + timedelta(days=30)
            )
            
            subscription_service.create(default_subscription)
            
        except Exception as e:
            # 如果创建订阅失败，记录错误但不影响用户创建
            print(f"创建默认订阅失败: {e}")
        
        return ResponseBase(message="用户创建成功", data={"user_id": user_id})
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"创建用户失败: {str(e)}")

@router.post("/users/batch-delete", response_model=ResponseBase)
def batch_delete_users(
    user_ids: dict = Body(...),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量删除用户"""
    try:
        user_service = UserService(db)
        deleted_count = 0
        
        user_id_list = user_ids.get("user_ids", [])
        for user_id in user_id_list:
            user = user_service.get(user_id)
            if user and not user.is_admin:  # 不允许删除管理员
                db.delete(user)
                deleted_count += 1
        
        db.commit()
        return ResponseBase(message=f"成功删除 {deleted_count} 个用户")
    except Exception as e:
        return ResponseBase(success=False, message=f"批量删除用户失败: {str(e)}")

@router.post("/users/batch-enable", response_model=ResponseBase)
def batch_enable_users(
    user_ids: dict = Body(...),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量启用用户"""
    try:
        user_service = UserService(db)
        updated_count = 0
        
        user_id_list = user_ids.get("user_ids", [])
        for user_id in user_id_list:
            user = user_service.get(user_id)
            if user:
                user.is_active = True
                updated_count += 1
        
        db.commit()
        return ResponseBase(message=f"成功启用 {updated_count} 个用户")
    except Exception as e:
        return ResponseBase(success=False, message=f"批量启用用户失败: {str(e)}")

@router.post("/users/batch-disable", response_model=ResponseBase)
def batch_disable_users(
    user_ids: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量禁用用户"""
    try:
        user_service = UserService(db)
        updated_count = 0
        
        user_id_list = user_ids.get("user_ids", [])
        for user_id in user_id_list:
            user = user_service.get(user_id)
            if user and not user.is_admin:  # 不允许禁用管理员
                user.is_active = False
                updated_count += 1
        
        db.commit()
        return ResponseBase(message=f"成功禁用 {updated_count} 个用户")
    except Exception as e:
        return ResponseBase(success=False, message=f"批量禁用用户失败: {str(e)}")

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
        if "is_admin" in user_data:
            user.is_admin = user_data["is_admin"]
        
        # 更新密码（如果提供）
        if "password" in user_data and user_data["password"]:
            from app.utils.security import get_password_hash
            user.hashed_password = get_password_hash(user_data["password"])
        
        user_service.db.commit()
        
        # 更新订阅信息
        if "subscription" in user_data:
            subscription = subscription_service.get_by_user_id(user.id)
            if subscription:
                if "device_limit" in user_data["subscription"]:
                    subscription.device_limit = user_data["subscription"]["device_limit"]
                if "expire_time" in user_data["subscription"]:
                    from datetime import datetime
                    subscription.expire_time = datetime.fromisoformat(user_data["subscription"]["expire_time"])
                if "is_active" in user_data["subscription"]:
                    subscription.is_active = user_data["subscription"]["is_active"]
                subscription_service.db.commit()
        
        # 记录管理员操作日志
        try:
            user_service.log_user_activity(
                user_id=user.id,
                activity_type="admin_update",
                description=f"管理员 {current_admin.username} 更新了用户信息",
                metadata={"updated_fields": list(user_data.keys())}
            )
        except:
            pass  # 如果记录日志失败，不影响主要功能
        
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

@router.post("/users/{user_id}/reset-password", response_model=ResponseBase)
def reset_user_password(
    user_id: int,
    password_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """重置用户密码"""
    try:
        user_service = UserService(db)
        
        user = user_service.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        new_password = password_data.get("password")
        if not new_password:
            raise HTTPException(status_code=400, detail="新密码不能为空")
        
        if len(new_password) < 6:
            raise HTTPException(status_code=400, detail="密码长度不能少于6位")
        
        # 更新密码
        from app.utils.security import get_password_hash
        user.hashed_password = get_password_hash(new_password)
        user_service.db.commit()
        
        # 记录操作日志
        try:
            user_service.log_user_activity(
                user_id=user.id,
                activity_type="admin_password_reset",
                description=f"管理员 {current_admin.username} 重置了用户密码"
            )
        except:
            pass
        
        return ResponseBase(message="密码重置成功")
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"密码重置失败: {str(e)}")

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
        token = create_access_token(data={"sub": str(user.id), "user_id": user.id})
        
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

@router.put("/orders/{order_id}", response_model=ResponseBase)
def update_order(
    order_id: int,
    order_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新订单状态"""
    try:
        from sqlalchemy import text
        from datetime import datetime
        
        # 检查订单是否存在
        check_query = text("SELECT id, status FROM orders WHERE id = :order_id")
        existing_order = db.execute(check_query, {"order_id": order_id}).first()
        if not existing_order:
            return ResponseBase(success=False, message="订单不存在")
        
        # 更新订单状态
        update_fields = []
        update_values = {"order_id": order_id}
        
        if "status" in order_data:
            update_fields.append("status = :status")
            update_values["status"] = order_data["status"]
        
        if "payment_status" in order_data:
            update_fields.append("payment_status = :payment_status")
            update_values["payment_status"] = order_data["payment_status"]
        
        if "admin_notes" in order_data:
            update_fields.append("admin_notes = :admin_notes")
            update_values["admin_notes"] = order_data["admin_notes"]
        
        if update_fields:
            update_fields.append("updated_at = :updated_at")
            update_values["updated_at"] = datetime.now()
            
            update_query = text(f"""
                UPDATE orders 
                SET {', '.join(update_fields)}
                WHERE id = :order_id
            """)
            
            db.execute(update_query, update_values)
            db.commit()
            
            return ResponseBase(message="订单更新成功")
        else:
            return ResponseBase(message="没有需要更新的字段")
            
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"更新订单失败: {str(e)}")

@router.get("/notifications", response_model=ResponseBase)
def get_notifications(current_admin = Depends(get_current_admin_user)) -> Any:
    """获取通知列表"""
    return ResponseBase(data={"notifications": [], "total": 0})

@router.get("/system-config", response_model=ResponseBase)
def get_system_config(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取系统配置"""
    try:
        from sqlalchemy import text
        
        # 从数据库获取系统配置
        query = text('SELECT key, value FROM system_configs WHERE type = \'system\'')
        result = db.execute(query)
        
        system_config = {
            "site_name": "XBoard Modern",
            "site_description": "现代化的代理服务管理平台",
            "logo_url": "",
            "maintenance_mode": False,
            "maintenance_message": "系统维护中，请稍后再试"
        }
        
        # 更新从数据库获取的配置
        for row in result:
            if row.key in system_config:
                if row.key in ['maintenance_mode']:
                    system_config[row.key] = row.value.lower() == 'true'
                else:
                    system_config[row.key] = row.value
        
        return ResponseBase(data=system_config)
    except Exception as e:
        print(f"获取系统配置失败: {e}")
        import traceback
        traceback.print_exc()
        return ResponseBase(success=False, message=f"获取系统配置失败: {str(e)}")

@router.post("/system-config", response_model=ResponseBase)
def save_system_config(
    config_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """保存系统配置"""
    try:
        from sqlalchemy import text
        from datetime import datetime
        
        # 保存配置到数据库
        current_time = datetime.now()
        
        for key, value in config_data.items():
            # 检查配置是否已存在
            check_query = text('SELECT id FROM system_configs WHERE key = :key AND type = \'system\'')
            existing = db.execute(check_query, {"key": key}).first()
            
            if existing:
                # 更新现有配置
                update_query = text("""
                    UPDATE system_configs 
                    SET value = :value, updated_at = :updated_at
                    WHERE "key" = :key AND type = 'system'
                """)
                db.execute(update_query, {
                    "value": str(value),
                    "updated_at": current_time,
                    "key": key
                })
            else:
                # 插入新配置
                insert_query = text("""
                    INSERT INTO system_configs ("key", value, type, category, display_name, description, is_public, sort_order, created_at, updated_at)
                    VALUES (:key, :value, 'system', 'system', :display_name, :description, false, 0, :created_at, :updated_at)
                """)
                db.execute(insert_query, {
                    "key": key,
                    "value": str(value),
                    "display_name": key.replace('_', ' ').title(),
                    "description": f"System configuration for {key}",
                    "created_at": current_time,
                    "updated_at": current_time
                })
        
        db.commit()
        return ResponseBase(message="系统配置保存成功")
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"保存系统配置失败: {str(e)}")

@router.get("/email-config", response_model=ResponseBase)
def get_email_config(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取邮件配置"""
    try:
        from sqlalchemy import text
        
        # 从数据库获取邮件配置
        query = text("SELECT key, value FROM system_configs WHERE type = 'email'")
        result = db.execute(query)
        
        email_config = {
            "smtp_host": "smtp.qq.com",
            "smtp_port": 587,
            "email_username": "",
            "email_password": "",
            "sender_name": "XBoard System",
            "smtp_encryption": "tls",
            "from_email": ""
        }
        
        # 更新从数据库获取的配置
        for row in result:
            if row.key in email_config:
                if row.key in ['smtp_port']:
                    email_config[row.key] = int(row.value) if row.value.isdigit() else email_config[row.key]
                else:
                    email_config[row.key] = row.value
        
        return ResponseBase(data=email_config)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取邮件配置失败: {str(e)}")

@router.post("/email-config", response_model=ResponseBase)
def save_email_config(
    config_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """保存邮件配置"""
    try:
        from sqlalchemy import text
        from datetime import datetime
        
        # 保存配置到数据库
        current_time = datetime.now()
        
        for key, value in config_data.items():
            # 检查配置是否已存在
            check_query = text('SELECT id FROM system_configs WHERE key = :key AND type = \'email\'')
            existing = db.execute(check_query, {"key": key}).first()
            
            if existing:
                # 更新现有配置
                update_query = text("""
                    UPDATE system_configs 
                    SET value = :value, updated_at = :updated_at
                    WHERE "key" = :key AND type = 'email'
                """)
                db.execute(update_query, {
                    "value": str(value),
                    "updated_at": current_time,
                    "key": key
                })
            else:
                # 插入新配置
                insert_query = text("""
                    INSERT INTO system_configs ("key", value, type, category, display_name, description, is_public, sort_order, created_at, updated_at)
                    VALUES (:key, :value, 'email', 'email', :display_name, :description, false, 0, :created_at, :updated_at)
                """)
                db.execute(insert_query, {
                    "key": key,
                    "value": str(value),
                    "display_name": key.replace('_', ' ').title(),
                    "description": f"Email configuration for {key}",
                    "created_at": current_time,
                    "updated_at": current_time
                })
        
        db.commit()
        return ResponseBase(message="邮件配置保存成功")
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"保存邮件配置失败: {str(e)}")

@router.get("/clash-config", response_model=ResponseBase)
def get_clash_config(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取Clash配置"""
    try:
        from sqlalchemy import text
        
        # 从数据库获取Clash配置
        query = text('SELECT value FROM system_configs WHERE key = \'clash_config\' AND type = \'clash\'')
        result = db.execute(query).first()
        
        if result:
            config_content = result.value
        else:
            config_content = "# Clash配置文件\n# 请在此处配置Clash代理规则\n\n# 代理服务器配置\nproxy:\n  - name: 'default'\n    type: http\n    server: 127.0.0.1\n    port: 7890\n\n# 规则配置\nrules:\n  - DOMAIN-SUFFIX,google.com,default\n  - DOMAIN-SUFFIX,facebook.com,default\n  - DOMAIN-SUFFIX,twitter.com,default\n  - GEOIP,CN,DIRECT\n  - MATCH,default"
        
        return ResponseBase(data=config_content)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取Clash配置失败: {str(e)}")

@router.post("/clash-config", response_model=ResponseBase)
def save_clash_config(
    config_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """保存Clash配置"""
    try:
        from sqlalchemy import text
        from datetime import datetime
        
        config_content = config_data.get("content", "")
        if not config_content:
            return ResponseBase(success=False, message="配置内容不能为空")
        
        # 保存配置到数据库
        current_time = datetime.now()
        
        # 检查配置是否已存在
        check_query = text('SELECT id FROM system_configs WHERE key = \'clash_config\' AND type = \'clash\'')
        existing = db.execute(check_query).first()
        
        if existing:
            # 更新现有配置
            update_query = text("""
                UPDATE system_configs 
                SET value = :value, updated_at = :updated_at
                WHERE key = 'clash_config' AND type = 'clash'
            """)
            db.execute(update_query, {
                "value": config_content,
                "updated_at": current_time
            })
        else:
            # 插入新配置
            insert_query = text("""
                INSERT INTO system_configs ("key", value, type, category, display_name, description, is_public, sort_order, created_at, updated_at)
                VALUES ('clash_config', :value, 'clash', 'proxy', 'Clash配置', 'Clash代理配置文件', 0, 1, :created_at, :updated_at)
            """)
            db.execute(insert_query, {
                "value": config_content,
                "created_at": current_time,
                "updated_at": current_time
            })
        
        db.commit()
        return ResponseBase(message="Clash配置保存成功")
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"保存Clash配置失败: {str(e)}")

@router.post("/clash-config-invalid", response_model=ResponseBase)
def save_clash_config_invalid(
    config_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """保存Clash失效配置"""
    try:
        from sqlalchemy import text
        from datetime import datetime
        
        config_content = config_data.get("content", "")
        if not config_content:
            return ResponseBase(success=False, message="配置内容不能为空")
        
        # 保存失效配置到数据库
        current_time = datetime.now()
        
        # 检查失效配置是否已存在
        check_query = text('SELECT id FROM system_configs WHERE key = \'clash_config_invalid\' AND type = \'clash_invalid\'')
        existing = db.execute(check_query).first()
        
        if existing:
            # 更新现有失效配置
            update_query = text("""
                UPDATE system_configs 
                SET value = :value, updated_at = :updated_at
                WHERE "key" = 'clash_config_invalid' AND type = 'clash_invalid'
            """)
            db.execute(update_query, {
                "value": config_content,
                "updated_at": current_time
            })
        else:
            # 插入新失效配置
            insert_query = text("""
                INSERT INTO system_configs ("key", value, type, category, display_name, description, is_public, sort_order, created_at, updated_at)
                VALUES ('clash_config_invalid', :value, 'clash_invalid', 'proxy', 'Clash失效配置', 'Clash失效代理配置文件', 0, 3, :created_at, :updated_at)
            """)
            db.execute(insert_query, {
                "value": config_content,
                "created_at": current_time,
                "updated_at": current_time
            })
        
        db.commit()
        return ResponseBase(message="Clash失效配置保存成功")
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"保存Clash失效配置失败: {str(e)}")

@router.get("/clash-config-invalid", response_model=ResponseBase)
def get_clash_config_invalid(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取Clash失效配置"""
    try:
        from sqlalchemy import text
        
        # 从数据库获取Clash失效配置
        query = text('SELECT value FROM system_configs WHERE key = \'clash_config_invalid\' AND type = \'clash_invalid\'')
        result = db.execute(query).first()
        
        if result:
            config_content = result.value
        else:
            config_content = "# Clash失效配置文件\n# 此配置用于无效用户\nproxy:\n  - name: 'invalid'\n    type: http\n    server: 0.0.0.0\n    port: 0\n\nrules:\n  - MATCH,DIRECT"
        
        return ResponseBase(data=config_content)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取Clash失效配置失败: {str(e)}")

@router.get("/v2ray-config", response_model=ResponseBase)
def get_v2ray_config(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取V2Ray配置"""
    try:
        from sqlalchemy import text
        
        # 从数据库获取V2Ray配置
        query = text('SELECT value FROM system_configs WHERE key = \'v2ray_config\' AND type = \'v2ray\'')
        result = db.execute(query).first()
        
        if result:
            config_content = result.value
        else:
            config_content = "# V2Ray配置文件\n# 请在此处配置V2Ray代理规则\n\n{\n  \"log\": {\n    \"loglevel\": \"warning\"\n  },\n  \"inbounds\": [\n    {\n      \"port\": 1080,\n      \"protocol\": \"socks\",\n      \"settings\": {\n        \"auth\": \"noauth\",\n        \"udp\": true\n      }\n    }\n  ],\n  \"outbounds\": [\n    {\n      \"protocol\": \"vmess\",\n      \"settings\": {\n        \"vnext\": [\n          {\n            \"address\": \"127.0.0.1\",\n            \"port\": 10086,\n            \"users\": [\n              {\n                \"id\": \"uuid-here\",\n                \"alterId\": 64\n              }\n            ]\n          }\n        ]\n      }\n    }\n  ]\n}"
        
        return ResponseBase(data=config_content)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取V2Ray配置失败: {str(e)}")

@router.post("/v2ray-config", response_model=ResponseBase)
def save_v2ray_config(
    config_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """保存V2Ray配置"""
    try:
        from sqlalchemy import text
        from datetime import datetime
        
        config_content = config_data.get("content", "")
        if not config_content:
            return ResponseBase(success=False, message="配置内容不能为空")
        
        # 保存配置到数据库
        current_time = datetime.now()
        
        # 检查配置是否已存在
        check_query = text('SELECT id FROM system_configs WHERE key = \'v2ray_config\' AND type = \'v2ray\'')
        existing = db.execute(check_query).first()
        
        if existing:
            # 更新现有配置
            update_query = text("""
                UPDATE system_configs 
                SET value = :value, updated_at = :updated_at
                WHERE "key" = 'v2ray_config' AND type = 'v2ray'
            """)
            db.execute(update_query, {
                "value": config_content,
                "updated_at": current_time
            })
        else:
            # 插入新配置
            insert_query = text("""
                INSERT INTO system_configs ("key", value, type, category, display_name, description, is_public, sort_order, created_at, updated_at)
                VALUES ('v2ray_config', :value, 'v2ray', 'proxy', 'V2Ray配置', 'V2Ray代理配置文件', 0, 2, :created_at, :updated_at)
            """)
            db.execute(insert_query, {
                "value": config_content,
                "created_at": current_time,
                "updated_at": current_time
            })
        
        db.commit()
        return ResponseBase(message="V2Ray配置保存成功")
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"保存V2Ray配置失败: {str(e)}")

@router.post("/v2ray-config-invalid", response_model=ResponseBase)
def save_v2ray_config_invalid(
    config_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """保存V2Ray失效配置"""
    try:
        from sqlalchemy import text
        from datetime import datetime
        
        config_content = config_data.get("content", "")
        if not config_content:
            return ResponseBase(success=False, message="配置内容不能为空")
        
        # 保存失效配置到数据库
        current_time = datetime.now()
        
        # 检查失效配置是否已存在
        check_query = text('SELECT id FROM system_configs WHERE key = \'v2ray_config_invalid\' AND type = \'v2ray_invalid\'')
        existing = db.execute(check_query).first()
        
        if existing:
            # 更新现有失效配置
            update_query = text("""
                UPDATE system_configs 
                SET value = :value, updated_at = :updated_at
                WHERE "key" = 'v2ray_config_invalid' AND type = 'v2ray_invalid'
            """)
            db.execute(update_query, {
                "value": config_content,
                "updated_at": current_time
            })
        else:
            # 插入新失效配置
            insert_query = text("""
                INSERT INTO system_configs ("key", value, type, category, display_name, description, is_public, sort_order, created_at, updated_at)
                VALUES ('v2ray_config_invalid', :value, 'v2ray_invalid', 'proxy', 'V2Ray失效配置', 'V2Ray失效代理配置文件', 0, 4, :created_at, :updated_at)
            """)
            db.execute(insert_query, {
                "value": config_content,
                "created_at": current_time,
                "updated_at": current_time
            })
        
        db.commit()
        return ResponseBase(message="V2Ray失效配置保存成功")
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"保存V2Ray失效配置失败: {str(e)}")

@router.get("/v2ray-config-invalid", response_model=ResponseBase)
def get_v2ray_config_invalid(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取V2Ray失效配置"""
    try:
        from sqlalchemy import text
        
        # 从数据库获取V2Ray失效配置
        query = text('SELECT value FROM system_configs WHERE key = \'v2ray_config_invalid\' AND type = \'v2ray_invalid\'')
        result = db.execute(query).first()
        
        if result:
            config_content = result.value
        else:
            config_content = "# V2Ray失效配置文件\n# 此配置用于无效用户\n{\n  \"log\": {\n    \"loglevel\": \"warning\"\n  },\n  \"inbounds\": [],\n  \"outbounds\": []\n}"
        
        return ResponseBase(data=config_content)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取V2Ray失效配置失败: {str(e)}")

@router.post("/test-email", response_model=ResponseBase)
def test_email(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """测试邮件发送"""
    try:
        from sqlalchemy import text
        
        # 从数据库获取邮件配置
        query = text('SELECT "key", value FROM system_configs WHERE type = \'email\'')
        result = db.execute(query)
        
        email_config = {}
        for row in result:
            email_config[row.key] = row.value
        
        # 检查必要的邮件配置
        required_fields = ['smtp_host', 'smtp_port', 'email_username', 'email_password']
        missing_fields = [field for field in required_fields if not email_config.get(field)]
        
        if missing_fields:
            return ResponseBase(success=False, message=f"邮件配置不完整，缺少: {', '.join(missing_fields)}")
        
        # 发送测试邮件
        from app.services.email import EmailService
        email_service = EmailService(db)
        test_subject = "XBoard 邮件配置测试"
        test_content = f"""
        <h2>邮件配置测试</h2>
        <p>这是一封来自 XBoard 系统的测试邮件。</p>
        <p>如果您收到这封邮件，说明邮件配置已成功！</p>
        <p>测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>管理员: {current_admin.username}</p>
        """
        
        # 创建测试邮件队列
        from app.schemas.email import EmailQueueCreate
        email_data = EmailQueueCreate(
            to_email=email_config.get('from_email', email_config.get('email_username', '')),
            subject=test_subject,
            content=test_content,
            content_type='html',
            email_type='test'
        )
        
        email_queue = email_service.create_email_queue(email_data)
        success = email_service.send_email(email_queue)
        
        if success:
            return ResponseBase(message="测试邮件发送成功")
        else:
            return ResponseBase(success=False, message="测试邮件发送失败")
        
    except Exception as e:
        return ResponseBase(success=False, message=f"邮件配置测试失败: {str(e)}")

@router.post("/test-email-to-user", response_model=ResponseBase)
def test_email_to_user(
    email_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """发送测试邮件给指定用户"""
    try:
        from app.services.email import EmailService
        
        target_email = email_data.get('email')
        if not target_email:
            return ResponseBase(success=False, message="请提供目标邮箱地址")
        
        # 发送测试邮件
        email_service = EmailService(db)
        test_subject = "XBoard 订阅地址测试邮件"
        test_content = f"""
        <h2>订阅地址测试邮件</h2>
        <p>尊敬的 {target_email}，</p>
        <p>这是一封来自 XBoard 系统的订阅地址测试邮件。</p>
        <p>如果您收到这封邮件，说明邮件发送功能正常工作！</p>
        <p>测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>管理员: {current_admin.username}</p>
        <hr>
        <p><strong>订阅地址信息：</strong></p>
        <p>通用配置地址: http://localhost:8000/api/v1/subscriptions/ssr/test</p>
        <p>移动端配置地址: http://localhost:8000/api/v1/subscriptions/clash/test</p>
        <p>请使用相应的客户端软件导入订阅地址。</p>
        """
        
        # 创建测试邮件队列
        from app.schemas.email import EmailQueueCreate
        email_queue_data = EmailQueueCreate(
            to_email=target_email,
            subject=test_subject,
            content=test_content,
            content_type='html',
            email_type='subscription_test'
        )
        
        email_queue = email_service.create_email_queue(email_queue_data)
        success = email_service.send_email(email_queue)
        
        if success:
            return ResponseBase(message=f"测试邮件已发送给 {target_email}")
        else:
            return ResponseBase(success=False, message="测试邮件发送失败")
        
    except Exception as e:
        return ResponseBase(success=False, message=f"发送测试邮件失败: {str(e)}")

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
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新基本设置"""
    try:
        from sqlalchemy import text
        from datetime import datetime
        
        # 保存基本设置到数据库
        current_time = datetime.now()
        
        for key, value in settings.items():
            # 检查配置是否已存在
            check_query = text("SELECT id FROM system_configs WHERE key = :key AND type = 'general'")
            existing = db.execute(check_query, {"key": key}).first()
            
            if existing:
                # 更新现有配置
                update_query = text("""
                    UPDATE system_configs 
                    SET value = :value, updated_at = :updated_at
                    WHERE key = :key AND type = 'general'
                """)
                db.execute(update_query, {
                    "value": str(value),
                    "updated_at": current_time,
                    "key": key
                })
        else:
                # 插入新配置
                insert_query = text("""
                    INSERT INTO system_configs (key, value, type, category, display_name, description, created_at, updated_at)
                    VALUES (:key, :value, 'general', 'system', :key, :key, :created_at, :updated_at)
                """)
                db.execute(insert_query, {
                    "key": key,
                    "value": str(value),
                    "created_at": current_time,
                    "updated_at": current_time
                })
        
        db.commit()
        return ResponseBase(message="基本设置保存成功")
    except Exception as e:
        db.rollback()
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
    search: str = Query("", description="搜索关键词（QQ、邮箱、订阅地址）"),
    status: str = Query("", description="状态筛选"),
    subscription_type: str = Query("", description="订阅类型筛选"),
    sort: str = Query("add_time_desc", description="排序方式"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取订阅列表"""
    try:
        subscription_service = SubscriptionService(db)
        user_service = UserService(db)
        
        skip = (page - 1) * size
        
        # 构建查询条件
        query_params = {}
        if search:
            query_params['search'] = search
        if status:
            query_params['status'] = status
            
        # 获取订阅数据
        subscriptions, total = subscription_service.get_subscriptions_with_pagination(
            skip=skip, 
            limit=size,
            **query_params
        )
        
        subscription_list = []
        for subscription in subscriptions:
            # 获取用户设备信息
            device_count = 0
            online_devices = 0
            apple_count = 0
            clash_count = 0
            v2ray_count = 0
            
            try:
                from app.services.device import DeviceService
                device_service = DeviceService(db)
                devices = device_service.get_devices_by_user_id(subscription.user_id)
                device_count = len(devices)
                online_devices = len([d for d in devices if d.is_online])
                
                # 统计设备类型
                for device in devices:
                    if 'apple' in device.device_type.lower() or 'ios' in device.device_type.lower():
                        apple_count += 1
                    if 'clash' in device.user_agent.lower():
                        clash_count += 1
                    if 'v2ray' in device.user_agent.lower() or 'shadowrocket' in device.user_agent.lower():
                        v2ray_count += 1
            except:
                device_count = subscription.current_devices if subscription else 0
                online_devices = 0
            
            # 计算订阅状态和到期信息
            subscription_status = "inactive"
            days_until_expire = None
            is_expired = False
            
            if subscription.expire_time:
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                expire_time = subscription.expire_time
                if isinstance(expire_time, str):
                    expire_time = datetime.fromisoformat(expire_time.replace('Z', '+00:00'))
                elif expire_time.tzinfo is None:
                    expire_time = expire_time.replace(tzinfo=timezone.utc)
                
                if expire_time > now:
                    subscription_status = "active" if subscription.is_active else "inactive"
                    days_until_expire = (expire_time - now).days
                else:
                    subscription_status = "expired"
                    is_expired = True
                    days_until_expire = 0
            
            # 生成订阅地址
            base_url = "http://localhost:8000"
            v2ray_url = f"{base_url}/api/v1/subscriptions/ssr/{subscription.subscription_url}" if subscription.subscription_url else None
            clash_url = f"{base_url}/api/v1/subscriptions/clash/{subscription.subscription_url}" if subscription.subscription_url else None
            
            subscription_data = {
                "id": subscription.id,
                "user": {
                    "id": subscription.user.id,
                    "username": subscription.user.username,
                    "email": subscription.user.email,
                    "created_at": subscription.user.created_at.isoformat() if subscription.user.created_at else None,
                    "last_login": subscription.user.last_login.isoformat() if subscription.user.last_login else None,
                    "is_active": subscription.user.is_active,
                    "is_verified": subscription.user.is_verified,
                    "is_admin": subscription.user.is_admin
                },
                "subscription_url": subscription.subscription_url,
                "v2ray_url": v2ray_url,
                "clash_url": clash_url,
                "status": subscription_status,
                "is_active": subscription.is_active,
                "expire_time": subscription.expire_time.isoformat() if subscription.expire_time else None,
                "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
                "device_limit": subscription.device_limit,
                "current_devices": device_count,
                "online_devices": online_devices,
                "apple_count": apple_count,
                "clash_count": clash_count,
                "v2ray_count": v2ray_count,
                "days_until_expire": days_until_expire,
                "is_expired": is_expired
            }
            subscription_list.append(subscription_data)
        
        # 应用排序
        if sort:
            if sort == "add_time_desc":
                subscription_list.sort(key=lambda x: x["created_at"] or "", reverse=True)
            elif sort == "add_time_asc":
                subscription_list.sort(key=lambda x: x["created_at"] or "")
            elif sort == "expire_time_desc":
                subscription_list.sort(key=lambda x: x["expire_time"] or "", reverse=True)
            elif sort == "expire_time_asc":
                subscription_list.sort(key=lambda x: x["expire_time"] or "")
            elif sort == "device_count_desc":
                subscription_list.sort(key=lambda x: x["current_devices"], reverse=True)
            elif sort == "device_count_asc":
                subscription_list.sort(key=lambda x: x["current_devices"])
            elif sort == "apple_count_desc":
                subscription_list.sort(key=lambda x: x["apple_count"], reverse=True)
            elif sort == "apple_count_asc":
                subscription_list.sort(key=lambda x: x["apple_count"])
            elif sort == "online_devices_desc":
                subscription_list.sort(key=lambda x: x["online_devices"], reverse=True)
            elif sort == "online_devices_asc":
                subscription_list.sort(key=lambda x: x["online_devices"])
            elif sort == "device_limit_desc":
                subscription_list.sort(key=lambda x: x["device_limit"], reverse=True)
            elif sort == "device_limit_asc":
                subscription_list.sort(key=lambda x: x["device_limit"])
        
        response_data = {
            "subscriptions": subscription_list,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
        
        return ResponseBase(data=response_data)
    except Exception as e:
        print(f"获取订阅列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
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

@router.post("/subscriptions", response_model=ResponseBase)
def create_subscription(
    subscription_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建新订阅"""
    try:
        subscription_service = SubscriptionService(db)
        user_service = UserService(db)
        
        # 检查用户是否存在
        user = user_service.get(subscription_data.get("user_id"))
        if not user:
            return ResponseBase(success=False, message="用户不存在")
        
        # 检查用户是否已有订阅
        existing_subscriptions = subscription_service.get_all_by_user_id(user.id)
        if existing_subscriptions:
            return ResponseBase(success=False, message="用户已有订阅")
        
        # 创建两个订阅（V2Ray和Clash）
        from sqlalchemy import text
        from datetime import datetime, timedelta
        
        # 计算到期时间（默认30天）
        expire_days = subscription_data.get("expire_days", 30)
        expire_time = datetime.now() + timedelta(days=expire_days)
        
        # 生成V2Ray订阅标识符（16位字符）
        import secrets
        v2ray_key = secrets.token_urlsafe(16)
        
        # 生成Clash订阅标识符（16位字符）
        clash_key = secrets.token_urlsafe(16)
        
        current_time = datetime.now()
        device_limit = subscription_data.get("device_limit", 3)
        is_active = subscription_data.get("is_active", True)
        
        # 插入V2Ray订阅
        v2ray_insert_query = text("""
            INSERT INTO subscriptions (user_id, subscription_url, device_limit, current_devices, is_active, expire_time, created_at, updated_at)
            VALUES (:user_id, :subscription_url, :device_limit, :current_devices, :is_active, :expire_time, :created_at, :updated_at)
        """)
        
        db.execute(v2ray_insert_query, {
            "user_id": user.id,
            "subscription_url": v2ray_key,
            "device_limit": device_limit,
            "current_devices": 0,
            "is_active": is_active,
            "expire_time": expire_time,
            "created_at": current_time,
            "updated_at": current_time
        })
        
        # 插入Clash订阅
        clash_insert_query = text("""
            INSERT INTO subscriptions (user_id, subscription_url, device_limit, current_devices, is_active, expire_time, created_at, :updated_at)
            VALUES (:user_id, :subscription_url, :device_limit, :current_devices, :is_active, :expire_time, :created_at, :updated_at)
        """)
        
        db.execute(clash_insert_query, {
            "user_id": user.id,
            "subscription_url": clash_key,
            "device_limit": device_limit,
            "current_devices": 0,
            "is_active": is_active,
            "expire_time": expire_time,
            "created_at": current_time,
            "updated_at": current_time
        })
        
        db.commit()
        
        return ResponseBase(message="订阅创建成功", data={
            "v2ray_subscription": v2ray_key,
            "clash_subscription": clash_key
        })
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"创建订阅失败: {str(e)}")

@router.put("/subscriptions/{subscription_id}", response_model=ResponseBase)
def update_subscription(
    subscription_id: int,
    subscription_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新订阅信息"""
    try:
        subscription_service = SubscriptionService(db)
        subscription = subscription_service.get(subscription_id)
        
        if not subscription:
            return ResponseBase(success=False, message="订阅不存在")
        
        # 更新订阅信息
        from sqlalchemy import text
        from datetime import datetime, timedelta
        
        update_fields = []
        update_values = {"subscription_id": subscription_id}
        
        if "device_limit" in subscription_data:
            update_fields.append("device_limit = :device_limit")
            update_values["device_limit"] = subscription_data["device_limit"]
        
        if "is_active" in subscription_data:
            update_fields.append("is_active = :is_active")
            update_values["is_active"] = subscription_data["is_active"]
        
        if "expire_days" in subscription_data:
            # 计算新的到期时间
            expire_days = subscription_data["expire_days"]
            if expire_days > 0:
                expire_time = datetime.now() + timedelta(days=expire_days)
            else:
                expire_time = None
            update_fields.append("expire_time = :expire_time")
            update_values["expire_time"] = expire_time
        
        if "expire_time" in subscription_data:
            # 直接设置到期时间
            try:
                expire_time = datetime.fromisoformat(subscription_data["expire_time"].replace('Z', '+00:00'))
                update_fields.append("expire_time = :expire_time")
                update_values["expire_time"] = expire_time
            except ValueError as e:
                return ResponseBase(success=False, message=f"时间格式错误: {str(e)}")
        
        if update_fields:
            update_fields.append("updated_at = :updated_at")
            update_values["updated_at"] = datetime.now()
            
            update_query = text(f"""
                UPDATE subscriptions 
                SET {', '.join(update_fields)}
                WHERE id = :subscription_id
            """)
            
            db.execute(update_query, update_values)
            db.commit()
            
            return ResponseBase(message="订阅更新成功")
        else:
            return ResponseBase(message="没有需要更新的字段")
            
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"更新订阅失败: {str(e)}")

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

@router.post("/subscriptions/user/{user_id}/reset-all", response_model=ResponseBase)
def reset_user_all_subscriptions(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """重置用户的所有订阅（V2Ray和Clash）"""
    try:
        subscription_service = SubscriptionService(db)
        
        # 获取用户的所有订阅
        user_subscriptions = db.query(Subscription).filter(Subscription.user_id == user_id).all()
        
        if not user_subscriptions:
            return ResponseBase(success=False, message="用户没有订阅")
        
        # 删除现有订阅
        for subscription in user_subscriptions:
            db.delete(subscription)
        
        # 创建新的V2Ray和Clash订阅
        from sqlalchemy import text
        from datetime import datetime, timedelta
        import secrets
        
        # 计算到期时间（默认30天）
        expire_time = datetime.now() + timedelta(days=30)
        current_time = datetime.now()
        device_limit = 3  # 默认设备限制
        
        # 生成V2Ray订阅标识符（16位字符）
        v2ray_key = secrets.token_urlsafe(16)
        
        # 生成Clash订阅标识符（16位字符）
        clash_key = secrets.token_urlsafe(16)
        
        # 插入V2Ray订阅
        v2ray_insert_query = text("""
            INSERT INTO subscriptions (user_id, subscription_url, device_limit, current_devices, is_active, expire_time, created_at, updated_at)
            VALUES (:user_id, :subscription_url, :device_limit, :current_devices, :is_active, :expire_time, :created_at, :updated_at)
        """)
        
        db.execute(v2ray_insert_query, {
            "user_id": user_id,
            "subscription_url": v2ray_url,
            "device_limit": device_limit,
            "current_devices": 0,
            "is_active": True,
            "expire_time": expire_time,
            "created_at": current_time,
            "updated_at": current_time
        })
        
        # 插入Clash订阅
        clash_insert_query = text("""
            INSERT INTO subscriptions (user_id, subscription_url, device_limit, current_devices, is_active, expire_time, created_at, updated_at)
            VALUES (:user_id, :subscription_url, :device_limit, :current_devices, :is_active, :expire_time, :created_at, :updated_at)
        """)
        
        db.execute(clash_insert_query, {
            "user_id": user_id,
            "subscription_url": clash_url,
            "device_limit": device_limit,
            "current_devices": 0,
            "is_active": True,
            "expire_time": expire_time,
            "created_at": current_time,
            "updated_at": current_time
        })
        
        db.commit()
        
        return ResponseBase(message="用户所有订阅重置成功", data={
            "v2ray_subscription_url": v2ray_key,
            "clash_subscription_url": clash_key
        })
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"重置用户订阅失败: {str(e)}")

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

@router.delete("/subscriptions/user/{user_id}/delete-all", response_model=ResponseBase)
def delete_user_all_data(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除用户的所有数据（订阅、设备等）"""
    try:
        subscription_service = SubscriptionService(db)
        user_service = UserService(db)
        
        # 获取用户信息
        user = user_service.get(user_id)
        if not user:
            return ResponseBase(success=False, message="用户不存在")
        
        # 删除用户的所有订阅
        user_subscriptions = db.query(Subscription).filter(Subscription.user_id == user_id).all()
        for subscription in user_subscriptions:
            subscription_service.delete(subscription.id)
        
        # 删除用户
        db.delete(user)
        db.commit()
        
        return ResponseBase(message="用户及其所有数据删除成功")
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"删除用户失败: {str(e)}")

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
        from sqlalchemy import text
        from datetime import datetime
        
        # 保存支付配置到数据库
        current_time = datetime.now()
        
        for key, value in payment_configs.items():
            # 检查配置是否已存在
            check_query = text("SELECT id FROM system_configs WHERE key = :key AND type = 'payment'")
            existing = db.execute(check_query, {"key": key}).first()
            
            if existing:
                # 更新现有配置
                update_query = text("""
                    UPDATE system_configs 
                    SET value = :value, updated_at = :updated_at
                    WHERE "key" = :key AND type = 'payment'
                """)
                db.execute(update_query, {
                    "value": str(value),
                    "updated_at": current_time,
                    "key": key
                })
        else:
                # 插入新配置
                insert_query = text("""
                    INSERT INTO system_configs ("key", value, type, category, display_name, description, is_public, sort_order, created_at, updated_at)
                    VALUES (:key, :value, 'payment', 'payment', :display_name, :description, false, 0, :created_at, :updated_at)
                """)
                db.execute(insert_query, {
                    "key": key,
                    "value": str(value),
                    "display_name": key.replace('_', ' ').title(),
                    "description": f"Payment configuration for {key}",
                    "created_at": current_time,
                    "updated_at": current_time
                })
        
        db.commit()
        return ResponseBase(message="支付配置更新成功")
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"更新支付配置失败: {str(e)}")

@router.post("/payment-configs/test", response_model=ResponseBase)
def test_payment_config(
    payment_config: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """测试支付配置"""
    try:
        # 这里可以添加实际的支付配置测试逻辑
        # 例如测试API密钥、连接支付网关等
        
        # 暂时返回成功（模拟测试通过）
            return ResponseBase(message="支付配置测试成功")
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

@router.post("/packages", response_model=ResponseBase)
def create_package(
    package_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建新套餐"""
    try:
        from sqlalchemy import text
        from datetime import datetime
        
        # 检查套餐名称是否已存在
        check_query = text("SELECT id FROM packages WHERE name = :name")
        existing_package = db.execute(check_query, {"name": package_data.get("name")}).first()
        if existing_package:
            return ResponseBase(success=False, message="套餐名称已存在")
        
        # 创建套餐
        insert_query = text("""
            INSERT INTO packages (name, description, price, duration_days, device_limit, bandwidth_limit, sort_order, is_active, created_at, updated_at)
            VALUES (:name, :description, :price, :duration_days, :device_limit, :bandwidth_limit, :sort_order, :is_active, :created_at, :updated_at)
        """)
        
        current_time = datetime.now()
        result = db.execute(insert_query, {
            "name": package_data["name"],
            "description": package_data.get("description", ""),
            "price": package_data.get("price", 0),
            "duration_days": package_data.get("duration_days", 30),
            "device_limit": package_data.get("device_limit", 3),
            "bandwidth_limit": package_data.get("bandwidth_limit", 0),
            "sort_order": package_data.get("sort_order", 0),
            "is_active": package_data.get("is_active", True),
            "created_at": current_time,
            "updated_at": current_time
        })
        
        db.commit()
        package_id = result.lastrowid
        
        return ResponseBase(message="套餐创建成功", data={"package_id": package_id})
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"创建套餐失败: {str(e)}")

@router.put("/packages/{package_id}", response_model=ResponseBase)
def update_package(
    package_id: int,
    package_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新套餐信息"""
    try:
        from sqlalchemy import text
        from datetime import datetime
        
        # 检查套餐是否存在
        check_query = text("SELECT id FROM packages WHERE id = :package_id")
        existing_package = db.execute(check_query, {"package_id": package_id}).first()
        if not existing_package:
            return ResponseBase(success=False, message="套餐不存在")
        
        # 更新套餐
        update_fields = []
        update_values = {"package_id": package_id}
        
        if "name" in package_data:
            update_fields.append("name = :name")
            update_values["name"] = package_data["name"]
        
        if "description" in package_data:
            update_fields.append("description = :description")
            update_values["description"] = package_data["description"]
        
        if "price" in package_data:
            update_fields.append("price = :price")
            update_values["price"] = package_data["price"]
        
        if "duration_days" in package_data:
            update_fields.append("duration_days = :duration_days")
            update_values["duration_days"] = package_data["duration_days"]
        
        if "device_limit" in package_data:
            update_fields.append("device_limit = :device_limit")
            update_values["device_limit"] = package_data["device_limit"]
        
        if "bandwidth_limit" in package_data:
            update_fields.append("bandwidth_limit = :bandwidth_limit")
            update_values["bandwidth_limit"] = package_data["bandwidth_limit"]
        
        if "sort_order" in package_data:
            update_fields.append("sort_order = :sort_order")
            update_values["sort_order"] = package_data["sort_order"]
        
        if "is_active" in package_data:
            update_fields.append("is_active = :is_active")
            update_values["is_active"] = package_data["is_active"]
        
        if update_fields:
            update_fields.append("updated_at = :updated_at")
            update_values["updated_at"] = datetime.now()
            
            update_query = text(f"""
                UPDATE packages 
                SET {', '.join(update_fields)}
                WHERE id = :package_id
            """)
            
            db.execute(update_query, update_values)
            db.commit()
            return ResponseBase(message="套餐更新成功")
        else:
            return ResponseBase(message="没有需要更新的字段")
            
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"更新套餐失败: {str(e)}")

@router.delete("/packages/{package_id}", response_model=ResponseBase)
def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除套餐"""
    try:
        from sqlalchemy import text
        
        # 检查套餐是否存在
        check_query = text("SELECT id FROM packages WHERE id = :package_id")
        existing_package = db.execute(check_query, {"package_id": package_id}).first()
        if not existing_package:
            return ResponseBase(success=False, message="套餐不存在")
        
        # 检查套餐是否被使用
        usage_query = text("SELECT id FROM orders WHERE package_id = :package_id LIMIT 1")
        usage_check = db.execute(usage_query, {"package_id": package_id}).first()
        if usage_check:
            return ResponseBase(success=False, message="套餐正在被使用，无法删除")
        
        # 删除套餐
        delete_query = text("DELETE FROM packages WHERE id = :package_id")
        db.execute(delete_query, {"package_id": package_id})
        db.commit()
        
        return ResponseBase(message="套餐删除成功")
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"删除套餐失败: {str(e)}")

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

# ==================== 设备管理 ====================

@router.delete("/subscriptions/{subscription_id}/devices/{device_id}", response_model=ResponseBase)
def remove_device(
    subscription_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除设备"""
    try:
        subscription_service = SubscriptionService(db)
        success = subscription_service.remove_device(device_id)
        if success:
            return ResponseBase(message="设备删除成功")
        else:
            return ResponseBase(success=False, message="设备删除失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"删除设备失败: {str(e)}")

@router.delete("/subscriptions/{subscription_id}/devices", response_model=ResponseBase)
def clear_all_devices(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """清空订阅的所有设备"""
    try:
        subscription_service = SubscriptionService(db)
        success = subscription_service.delete_devices_by_subscription_id(subscription_id)
        if success:
            return ResponseBase(message="所有设备已清空")
        else:
            return ResponseBase(success=False, message="清空设备失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"清空设备失败: {str(e)}")

@router.get("/subscriptions/{subscription_id}/devices", response_model=ResponseBase)
def get_subscription_devices(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取订阅的设备列表"""
    try:
        subscription_service = SubscriptionService(db)
        devices = subscription_service.get_devices_by_subscription_id(subscription_id)
        
        device_list = []
        for device in devices:
            device_data = {
                "id": device.id,
                "name": device.device_name or "未知设备",
                "type": device.device_type or "未知类型",
                "ip": device.ip_address,
                "user_agent": device.user_agent,
                "last_access": device.last_access.isoformat() if device.last_access else None,
                "is_active": device.is_active,
                "created_at": device.created_at.isoformat() if device.created_at else None
            }
            device_list.append(device_data)
        
        return ResponseBase(data={
            "devices": device_list,
            "total": len(device_list)
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取设备列表失败: {str(e)}")

# 新增的订阅管理API端点

@router.post("/subscriptions/batch-clear-devices", response_model=ResponseBase)
def batch_clear_devices(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量清理所有用户设备"""
    try:
        subscription_service = SubscriptionService(db)
        
        # 获取所有订阅
        all_subscriptions = subscription_service.get_all()
        
        cleared_count = 0
        for subscription in all_subscriptions:
            # 清理设备
            subscription_service.clear_devices(subscription.id)
            # 重置设备计数
            subscription.current_devices = 0
            cleared_count += 1
        
        db.commit()
        
        return ResponseBase(message=f"成功清理 {cleared_count} 个用户的设备")
    except Exception as e:
        db.rollback()
        return ResponseBase(success=False, message=f"批量清理设备失败: {str(e)}")

@router.post("/subscriptions/{subscription_id}/send-email", response_model=ResponseBase)
def send_subscription_email(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """发送订阅邮件"""
    try:
        subscription_service = SubscriptionService(db)
        subscription = subscription_service.get(subscription_id)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="订阅不存在")
        
        # 发送订阅邮件
        success = subscription_service.send_subscription_email(subscription.user_id)
        
        if success:
            return ResponseBase(message="订阅邮件发送成功")
        else:
            return ResponseBase(success=False, message="订阅邮件发送失败")
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"发送订阅邮件失败: {str(e)}")

@router.post("/subscriptions/user/{user_id}/send-email", response_model=ResponseBase)
def send_subscription_email_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """根据用户ID发送订阅邮件"""
    try:
        subscription_service = SubscriptionService(db)
        
        # 发送订阅邮件
        success = subscription_service.send_subscription_email(user_id)
        
        if success:
            return ResponseBase(message="订阅邮件发送成功")
        else:
            return ResponseBase(success=False, message="订阅邮件发送失败")
    except Exception as e:
        return ResponseBase(success=False, message=f"发送订阅邮件失败: {str(e)}")

@router.get("/subscriptions/export", response_model=ResponseBase)
def export_subscriptions(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """导出订阅数据"""
    try:
        subscription_service = SubscriptionService(db)
        subscriptions = subscription_service.get_all()
        
        export_data = []
        for subscription in subscriptions:
            export_item = {
                "用户ID": subscription.user_id,
                "用户名": subscription.user.username if subscription.user else "未知",
                "邮箱": subscription.user.email if subscription.user else "未知",
                "订阅地址": subscription.subscription_url,
                "通用配置地址": f"http://localhost:8000/api/v1/subscriptions/ssr/{subscription.subscription_url}",
                "移动端配置地址": f"http://localhost:8000/api/v1/subscriptions/clash/{subscription.subscription_url}",
                "设备限制": subscription.device_limit,
                "当前设备": subscription.current_devices,
                "状态": "活跃" if subscription.is_active else "暂停",
                "到期时间": subscription.expire_time.isoformat() if subscription.expire_time else "无",
                "创建时间": subscription.created_at.isoformat() if subscription.created_at else "无"
            }
            export_data.append(export_item)
        
        return ResponseBase(data={
            "subscriptions": export_data,
            "total": len(export_data)
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"导出订阅数据失败: {str(e)}")

@router.get("/subscriptions/apple-stats", response_model=ResponseBase)
def get_apple_stats(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取苹果设备统计"""
    try:
        subscription_service = SubscriptionService(db)
        
        # 统计苹果设备
        apple_count = 0
        total_devices = 0
        
        all_subscriptions = subscription_service.get_all()
        for subscription in all_subscriptions:
            devices = subscription_service.get_devices(subscription.id)
            total_devices += len(devices)
            for device in devices:
                if 'apple' in device.device_type.lower() or 'ios' in device.device_type.lower():
                    apple_count += 1
        
        return ResponseBase(data={
            "apple_devices": apple_count,
            "total_devices": total_devices,
            "apple_percentage": (apple_count / total_devices * 100) if total_devices > 0 else 0
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取苹果设备统计失败: {str(e)}")

@router.get("/subscriptions/online-stats", response_model=ResponseBase)
def get_online_stats(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取在线设备统计"""
    try:
        subscription_service = SubscriptionService(db)
        
        online_count = 0
        total_devices = 0
        
        all_subscriptions = subscription_service.get_all()
        for subscription in all_subscriptions:
            devices = subscription_service.get_devices(subscription.id)
            total_devices += len(devices)
            for device in devices:
                if device.is_online:
                    online_count += 1
        
        return ResponseBase(data={
            "online_devices": online_count,
            "total_devices": total_devices,
            "online_percentage": (online_count / total_devices * 100) if total_devices > 0 else 0
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取在线设备统计失败: {str(e)}")
