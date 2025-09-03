from typing import Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.database import get_db
from app.schemas.user import UserUpdate
from app.schemas.order import OrderUpdate
from app.schemas.order import PackageCreate, PackageUpdate
from app.schemas.common import ResponseBase, PaginationParams
from app.services.user import UserService
from app.services.order import OrderService
from app.services.package import PackageService
from app.services.subscription import SubscriptionService
from app.services.email import EmailService
from app.utils.security import get_current_user, get_current_admin_user

router = APIRouter()

# ==================== 管理端首页统计 ====================

@router.get("/dashboard", response_model=ResponseBase)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取管理端首页统计数据"""
    user_service = UserService(db)
    order_service = OrderService(db)
    subscription_service = SubscriptionService(db)
    
    # 时间计算
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    today_end = today_start + timedelta(days=1)
    yesterday_start = today_start - timedelta(days=1)
    yesterday_end = today_start
    week_start = today_start - timedelta(days=7)
    month_start = datetime(now.year, now.month, 1)
    month_end = (month_start + timedelta(days=32)).replace(day=1)
    
    # 用户统计
    total_users = user_service.count()
    today_users = user_service.count_users_since(today_start)
    yesterday_users = user_service.count_users_since(yesterday_start, yesterday_end)
    active_users = user_service.count_active_users(30)  # 30天内活跃
    
    # 订阅统计
    total_subscriptions = subscription_service.count()
    active_subscriptions = subscription_service.count_active()
    expired_subscriptions = subscription_service.count_expired()
    expiring_soon = subscription_service.count_expiring_soon(7)  # 7天内过期
    expiring_in_30_days = subscription_service.count_expiring_soon(30)  # 30天内过期
    
    # 订单和收入统计
    today_orders = order_service.count_orders_since(today_start, today_end)
    yesterday_orders = order_service.count_orders_since(yesterday_start, yesterday_end)
    week_orders = order_service.count_orders_since(week_start, now)
    month_orders = order_service.count_orders_since(month_start, month_end)
    
    today_revenue = order_service.get_revenue_since(today_start, today_end)
    yesterday_revenue = order_service.get_revenue_since(yesterday_start, yesterday_end)
    week_revenue = order_service.get_revenue_since(week_start, now)
    month_revenue = order_service.get_revenue_since(month_start, month_end)
    
    # 设备统计
    total_devices = subscription_service.count_total_devices()
    online_devices = subscription_service.count_online_devices()
    
    # 最近7天数据趋势
    daily_stats = []
    for i in range(7):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        daily_stats.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "users": user_service.count_users_since(day_start, day_end),
            "orders": order_service.count_orders_since(day_start, day_end),
            "revenue": order_service.get_revenue_since(day_start, day_end)
        })
    daily_stats.reverse()
    
    return ResponseBase(
        data={
            "users": {
                "total": total_users,
                "today": today_users,
                "yesterday": yesterday_users,
                "active": active_users
            },
            "subscriptions": {
                "total": total_subscriptions,
                "active": active_subscriptions,
                "expired": expired_subscriptions,
                "expiring_soon": expiring_soon,
                "expiring_in_30_days": expiring_in_30_days
            },
            "orders": {
                "today": today_orders,
                "yesterday": yesterday_orders,
                "week": week_orders,
                "month": month_orders
            },
            "revenue": {
                "today": float(today_revenue),
                "yesterday": float(yesterday_revenue),
                "week": float(week_revenue),
                "month": float(month_revenue)
            },
            "devices": {
                "total": total_devices,
                "online": online_devices
            },
            "daily_stats": daily_stats
        }
    )

# ==================== 用户管理 ====================

@router.post("/users/batch-delete", response_model=ResponseBase)
def batch_delete_users(
    user_ids: List[int],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量删除用户"""
    user_service = UserService(db)
    subscription_service = SubscriptionService(db)
    
    deleted_count = 0
    failed_count = 0
    
    for user_id in user_ids:
        try:
            # 删除用户相关的所有数据
            user = user_service.get(user_id)
            if user:
                # 删除用户的订阅
                subscription = subscription_service.get_by_user_id(user_id)
                if subscription:
                    subscription_service.delete(subscription.id)
                
                # 删除用户
                if user_service.delete(user_id):
                    deleted_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
    
    return ResponseBase(
        message=f"批量删除完成，成功：{deleted_count}，失败：{failed_count}",
        data={
            "deleted_count": deleted_count,
            "failed_count": failed_count
        }
    )

@router.post("/users/batch-enable", response_model=ResponseBase)
def batch_enable_users(
    user_ids: List[int],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量启用用户"""
    user_service = UserService(db)
    
    updated_count = 0
    failed_count = 0
    
    for user_id in user_ids:
        try:
            user = user_service.get(user_id)
            if user:
                user.is_active = True
                db.commit()
                updated_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
    
    return ResponseBase(
        message=f"批量启用完成，成功：{updated_count}，失败：{failed_count}",
        data={
            "updated_count": updated_count,
            "failed_count": failed_count
        }
    )

@router.post("/users/batch-disable", response_model=ResponseBase)
def batch_disable_users(
    user_ids: List[int],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量禁用用户"""
    user_service = UserService(db)
    
    updated_count = 0
    failed_count = 0
    
    for user_id in user_ids:
        try:
            user = user_service.get(user_id)
            if user:
                user.is_active = False
                db.commit()
                updated_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
    
    return ResponseBase(
        message=f"批量禁用完成，成功：{updated_count}，失败：{failed_count}",
        data={
            "updated_count": updated_count,
            "failed_count": failed_count
        }
    )

@router.post("/users/batch-verify", response_model=ResponseBase)
def batch_verify_users(
    user_ids: List[int],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量验证用户邮箱"""
    user_service = UserService(db)
    
    updated_count = 0
    failed_count = 0
    
    for user_id in user_ids:
        try:
            user = user_service.get(user_id)
            if user:
                user.is_verified = True
                db.commit()
                updated_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
    
    return ResponseBase(
        message=f"批量验证完成，成功：{updated_count}，失败：{failed_count}",
        data={
            "updated_count": updated_count,
            "failed_count": failed_count
        }
    )

@router.post("/users/{user_id}/send-subscription-email", response_model=ResponseBase)
def send_subscription_email_to_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """向用户发送订阅邮件"""
    user_service = UserService(db)
    subscription_service = SubscriptionService(db)
    
    user = user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    subscription = subscription_service.get_by_user_id(user_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户没有订阅"
        )
    
    # 发送订阅邮件
    email_service = EmailService(db)
    subscription_data = {
        'id': subscription.id if subscription else 0,
        'package_name': subscription.package.name if subscription and subscription.package else '未知套餐',
        'expires_at': subscription.expire_time.strftime('%Y-%m-%d %H:%M:%S') if subscription and subscription.expire_time else '未知',
        'status': subscription.status if subscription else '未知'
    }
    success = email_service.send_subscription_email(user.email, subscription_data)
    
    if success:
        return ResponseBase(message="订阅邮件发送成功")
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="邮件发送失败"
        )

@router.post("/users/batch-send-subscription-email", response_model=ResponseBase)
def batch_send_subscription_email(
    user_ids: List[int],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量发送订阅邮件"""
    user_service = UserService(db)
    subscription_service = SubscriptionService(db)
    
    success_count = 0
    failed_count = 0
    
    for user_id in user_ids:
        try:
            user = user_service.get(user_id)
            if user:
                subscription = subscription_service.get_by_user_id(user_id)
                if subscription:
                    email_service = EmailService(db)
                    subscription_data = {
                        'id': subscription.id,
                        'package_name': subscription.package.name if subscription.package else '未知套餐',
                        'expires_at': subscription.expire_time.strftime('%Y-%m-%d %H:%M:%S') if subscription.expire_time else '未知',
                        'status': subscription.status
                    }
                    if email_service.send_subscription_email(user.email, subscription_data):
                        success_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
    
    return ResponseBase(
        message=f"批量发送完成，成功：{success_count}，失败：{failed_count}",
        data={
            "success_count": success_count,
            "failed_count": failed_count
        }
    )

@router.get("/users/expiring", response_model=ResponseBase)
def get_expiring_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取即将过期的用户列表"""
    subscription_service = SubscriptionService(db)
    
    skip = (page - 1) * size
    expiring_subscriptions = subscription_service.get_expiring_subscriptions(days)
    
    # 分页处理
    total = len(expiring_subscriptions)
    paginated_subscriptions = expiring_subscriptions[skip:skip + size]
    
    return ResponseBase(
        data={
            "users": [
                {
                    "id": sub.user.id if sub.user else 0,
                    "username": sub.user.username if sub.user else "未知",
                    "email": sub.user.email if sub.user else "未知",
                    "subscription_id": sub.id,
                    "expire_time": sub.expire_time.isoformat() if sub.expire_time else None,
                    "days_left": (sub.expire_time - datetime.utcnow()).days if sub.expire_time else 0,
                    "device_count": len(sub.devices) if sub.devices else 0,
                    "device_limit": sub.device_limit,
                    "is_active": sub.user.is_active if sub.user else False,
                    "is_verified": sub.user.is_verified if sub.user else False
                }
                for sub in paginated_subscriptions
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    )

@router.post("/users/batch-expire-reminder", response_model=ResponseBase)
def batch_send_expire_reminder(
    user_ids: List[int],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量发送即将过期提醒邮件"""
    user_service = UserService(db)
    subscription_service = SubscriptionService(db)
    
    success_count = 0
    failed_count = 0
    
    for user_id in user_ids:
        try:
            user = user_service.get(user_id)
            if user:
                subscription = subscription_service.get_by_user_id(user_id)
                if subscription and subscription.expire_time:
                    from app.utils.email import send_subscription_expiry_reminder
                    if send_subscription_expiry_reminder(user.email, user.username, subscription.expire_time):
                        success_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
    
    return ResponseBase(
        message=f"批量发送提醒完成，成功：{success_count}，失败：{failed_count}",
        data={
            "success_count": success_count,
            "failed_count": failed_count
        }
    )

@router.post("/users", response_model=ResponseBase)
def create_user(
    user_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建用户"""
    user_service = UserService(db)
    
    # 检查用户名是否已存在
    existing_user = user_service.get_by_username(user_data.get("username"))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = user_service.get_by_email(user_data.get("email"))
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 创建用户
    from app.schemas.user import UserCreate
    from app.utils.security import get_password_hash
    
    user_create = UserCreate(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
        is_active=user_data.get("is_active", True),
        is_verified=user_data.get("is_verified", False),
        is_admin=user_data.get("is_admin", False)
    )
    
    user = user_service.create(user_create)
    
    return ResponseBase(
        message="用户创建成功",
        data={"user_id": user.id}
    )

@router.get("/users", response_model=ResponseBase)
def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取用户列表"""
    try:
        user_service = UserService(db)
        
        skip = (page - 1) * size
        users, total = user_service.get_users_with_pagination(
            skip=skip,
            limit=size,
            search=search,
            status=status
        )
        
        return ResponseBase(
            data={
                "users": [
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "is_active": user.is_active,
                        "is_verified": user.is_verified,
                        "is_admin": user.is_admin,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "last_login": user.last_login.isoformat() if user.last_login else None,
                        "subscription_count": 0,  # 暂时硬编码
                        "order_count": 0  # 暂时硬编码
                    }
                    for user in users
                ],
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
        )
    except Exception as e:
        return ResponseBase(
            success=False,
            message=f"获取用户列表失败: {str(e)}"
        )

@router.get("/users/{user_id}", response_model=ResponseBase)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取用户详情"""
    user_service = UserService(db)
    user = user_service.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return ResponseBase(
        data={
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "subscriptions": [
                    {
                        "id": sub.id,
                        "url": sub.url,
                        "device_limit": sub.device_limit,
                        "expire_time": sub.expire_time.isoformat() if sub.expire_time else None,
                        "device_count": len(getattr(sub, 'devices', []) or [])
                    }
                    for sub in (getattr(user, 'subscriptions', []) or [])
                ],
                "orders": [
                    {
                        "id": order.id,
                        "order_no": order.order_no,
                        "amount": order.amount,
                        "status": order.status,
                        "created_at": order.created_at.isoformat()
                    }
                    for order in (getattr(user, 'orders', []) or [])
                ]
            }
        }
    )

@router.put("/users/{user_id}", response_model=ResponseBase)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新用户信息"""
    user_service = UserService(db)
    
    user = user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    updated_user = user_service.update(user_id, user_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新失败"
        )
    
    return ResponseBase(message="用户更新成功")

@router.delete("/users/{user_id}", response_model=ResponseBase)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除用户"""
    user_service = UserService(db)
    
    user = user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    success = user_service.delete(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="删除失败"
        )
    
    return ResponseBase(message="用户删除成功")

@router.post("/users/{user_id}/login-as", response_model=ResponseBase)
def login_as_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """管理员登录为用户"""
    user_service = UserService(db)
    
    user = user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 生成用户登录令牌
    from app.utils.security import create_access_token
    token = create_access_token(data={"sub": user.username})
    
    return ResponseBase(
        message="登录成功",
        data={
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }
    )

# ==================== 订阅管理 ====================

@router.post("/subscriptions/batch-delete", response_model=ResponseBase)
def batch_delete_subscriptions(
    subscription_ids: List[int],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量删除订阅"""
    subscription_service = SubscriptionService(db)
    
    deleted_count = 0
    failed_count = 0
    
    for subscription_id in subscription_ids:
        try:
            if subscription_service.delete(subscription_id):
                deleted_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
    
    return ResponseBase(
        message=f"批量删除完成，成功：{deleted_count}，失败：{failed_count}",
        data={
            "deleted_count": deleted_count,
            "failed_count": failed_count
        }
    )

@router.post("/subscriptions/batch-enable", response_model=ResponseBase)
def batch_enable_subscriptions(
    subscription_ids: List[int],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量启用订阅"""
    subscription_service = SubscriptionService(db)
    
    updated_count = 0
    failed_count = 0
    
    for subscription_id in subscription_ids:
        try:
            subscription = subscription_service.get(subscription_id)
            if subscription:
                # 延长订阅时间（默认30天）
                subscription_service.extend_subscription(subscription_id, 30)
                updated_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
    
    return ResponseBase(
        message=f"批量启用完成，成功：{updated_count}，失败：{failed_count}",
        data={
            "updated_count": updated_count,
            "failed_count": failed_count
        }
    )

@router.post("/subscriptions/batch-disable", response_model=ResponseBase)
def batch_disable_subscriptions(
    subscription_ids: List[int],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量禁用订阅（设置为过期）"""
    subscription_service = SubscriptionService(db)
    
    updated_count = 0
    failed_count = 0
    
    for subscription_id in subscription_ids:
        try:
            subscription = subscription_service.get(subscription_id)
            if subscription:
                # 设置为过期
                subscription.expire_time = datetime.utcnow()
                db.commit()
                updated_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
    
    return ResponseBase(
        message=f"批量禁用完成，成功：{updated_count}，失败：{failed_count}",
        data={
            "updated_count": updated_count,
            "failed_count": failed_count
        }
    )

@router.post("/subscriptions/batch-reset", response_model=ResponseBase)
def batch_reset_subscriptions(
    subscription_ids: List[int],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量重置订阅地址"""
    subscription_service = SubscriptionService(db)
    
    updated_count = 0
    failed_count = 0
    
    for subscription_id in subscription_ids:
        try:
            if subscription_service.reset_subscription(subscription_id):
                updated_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
    
    return ResponseBase(
        message=f"批量重置完成，成功：{updated_count}，失败：{failed_count}",
        data={
            "updated_count": updated_count,
            "failed_count": failed_count
        }
    )

@router.post("/subscriptions/batch-send-email", response_model=ResponseBase)
def batch_send_subscription_email(
    subscription_ids: List[int],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """批量发送订阅邮件"""
    subscription_service = SubscriptionService(db)
    
    success_count = 0
    failed_count = 0
    
    for subscription_id in subscription_ids:
        try:
            subscription = subscription_service.get(subscription_id)
            if subscription and subscription.user:
                email_service = EmailService(db)
                subscription_data = {
                    'id': subscription.id,
                    'package_name': subscription.package.name if subscription.package else '未知套餐',
                    'expires_at': subscription.expire_time.strftime('%Y-%m-%d %H:%M:%S') if subscription.expire_time else '未知',
                    'status': subscription.status
                }
                if email_service.send_subscription_email(subscription.user.email, subscription_data):
                    success_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
    
    return ResponseBase(
        message=f"批量发送完成，成功：{success_count}，失败：{failed_count}",
        data={
            "success_count": success_count,
            "failed_count": failed_count
        }
    )

@router.post("/subscriptions/{subscription_id}/extend", response_model=ResponseBase)
def extend_subscription(
    subscription_id: int,
    days: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """延长订阅时间"""
    subscription_service = SubscriptionService(db)
    
    subscription = subscription_service.get(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )
    
    success = subscription_service.extend_subscription(subscription_id, days)
    
    if success:
        return ResponseBase(message=f"订阅已延长{days}天")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="延长订阅失败"
        )

@router.post("/subscriptions", response_model=ResponseBase)
def create_subscription(
    subscription_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建订阅"""
    subscription_service = SubscriptionService(db)
    user_service = UserService(db)
    
    # 检查用户是否存在
    user = user_service.get(subscription_data.get("user_id"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查用户是否已有订阅
    existing_subscription = subscription_service.get_by_user_id(subscription_data.get("user_id"))
    if existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已有订阅"
        )
    
    # 创建订阅
    from app.schemas.subscription import SubscriptionCreate
    from datetime import datetime, timedelta
    
    # 计算到期时间
    duration_days = subscription_data.get("duration_days", 30)
    expire_time = datetime.utcnow() + timedelta(days=duration_days)
    
    subscription_create = SubscriptionCreate(
        user_id=subscription_data["user_id"],
        url="",  # 将在创建时生成
        device_limit=subscription_data.get("device_limit", 5),
        expire_time=expire_time
    )
    
    subscription = subscription_service.create(subscription_create)
    
    # 生成订阅URL
    subscription_service.update_subscription_key(subscription.id)
    
    return ResponseBase(
        message="订阅创建成功",
        data={"subscription_id": subscription.id}
    )

@router.put("/subscriptions/{subscription_id}", response_model=ResponseBase)
def update_subscription(
    subscription_id: int,
    subscription_update: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新订阅"""
    subscription_service = SubscriptionService(db)
    
    subscription = subscription_service.get(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )
    
    # 更新订阅信息
    from app.schemas.subscription import SubscriptionUpdate
    from datetime import datetime, timedelta
    
    update_data = {}
    
    if "device_limit" in subscription_update:
        update_data["device_limit"] = subscription_update["device_limit"]
    
    if "duration_days" in subscription_update:
        # 延长订阅时间
        duration_days = subscription_update["duration_days"]
        if subscription.expire_time and subscription.expire_time > datetime.utcnow():
            # 从当前到期时间延长
            new_expire_time = subscription.expire_time + timedelta(days=duration_days)
        else:
            # 从当前时间开始计算
            new_expire_time = datetime.utcnow() + timedelta(days=duration_days)
        update_data["expire_time"] = new_expire_time
    
    if update_data:
        subscription_update_obj = SubscriptionUpdate(**update_data)
        updated_subscription = subscription_service.update(subscription_id, subscription_update_obj)
        
        if not updated_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新失败"
            )
    
    return ResponseBase(message="订阅更新成功")

@router.get("/subscriptions", response_model=ResponseBase)
def get_subscriptions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取订阅列表"""
    subscription_service = SubscriptionService(db)
    
    skip = (page - 1) * size
    subscriptions, total = subscription_service.get_subscriptions_with_pagination(
        skip=skip,
        limit=size,
        search=search,
        status=status
    )
    
    return ResponseBase(
        data={
            "subscriptions": [
                {
                    "id": sub.id,
                    "user_id": sub.user_id,
                    "username": sub.user.username if sub.user else "未知",
                    "url": sub.url,
                    "device_limit": sub.device_limit,
                    "device_count": len(sub.devices) if sub.devices else 0,
                    "expire_time": sub.expire_time.isoformat() if sub.expire_time else None,
                    "is_active": sub.expire_time > datetime.utcnow() if sub.expire_time else False,
                    "created_at": sub.created_at.isoformat()
                }
                for sub in subscriptions
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    )

@router.post("/subscriptions/{subscription_id}/reset", response_model=ResponseBase)
def reset_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """重置订阅地址"""
    subscription_service = SubscriptionService(db)
    
    subscription = subscription_service.get(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )
    
    success = subscription_service.reset_subscription(subscription_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="重置失败"
        )
    
    return ResponseBase(message="订阅地址重置成功")

# ==================== 订单管理 ====================

@router.get("/orders", response_model=ResponseBase)
def get_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    date_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取订单列表"""
    order_service = OrderService(db)
    
    skip = (page - 1) * size
    orders, total = order_service.get_orders_with_pagination(
        skip=skip,
        limit=size,
        status=status_filter,
        date_filter=date_filter,
        search=search
    )
    
    return ResponseBase(
        data={
            "orders": [
                {
                    "id": order.id,
                    "order_no": order.order_no,
                    "user_id": order.user_id,
                    "username": order.user.username if order.user else "未知",
                    "package_name": order.package.name if order.package else "未知",
                    "amount": order.amount,
                    "status": order.status,
                    "payment_method": order.payment_method,
                    "created_at": order.created_at.isoformat(),
                    "payment_time": order.payment_time.isoformat() if order.payment_time else None
                }
                for order in orders
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    )

@router.put("/orders/{order_id}", response_model=ResponseBase)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新订单状态"""
    order_service = OrderService(db)
    
    order = order_service.get(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    updated_order = order_service.update(order_id, order_update)
    
    if not updated_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新失败"
        )
    
    return ResponseBase(message="订单更新成功")

# ==================== 套餐管理 ====================

@router.get("/packages", response_model=ResponseBase)
def get_admin_packages(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取套餐列表"""
    package_service = PackageService(db)
    packages = package_service.get_all_packages()
    
    return ResponseBase(
        data={
            "packages": [
                {
                    "id": pkg.id,
                    "name": pkg.name,
                    "price": pkg.price,
                    "duration": pkg.duration,
                    "device_limit": pkg.device_limit,
                    "description": pkg.description,
                    "is_active": pkg.is_active,
                    "is_recommended": pkg.is_recommended,
                    "is_popular": pkg.is_popular,
                    "created_at": pkg.created_at.isoformat(),
                    "order_count": len(pkg.orders) if pkg.orders else 0
                }
                for pkg in packages
            ]
        }
    )

@router.post("/packages", response_model=ResponseBase)
def create_package(
    package_data: PackageCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建套餐"""
    package_service = PackageService(db)
    
    package = package_service.create(package_data)
    
    return ResponseBase(
        message="套餐创建成功",
        data={"package_id": package.id}
    )

@router.put("/packages/{package_id}", response_model=ResponseBase)
def update_package(
    package_id: int,
    package_update: PackageUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新套餐"""
    package_service = PackageService(db)
    
    package = package_service.get(package_id)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    updated_package = package_service.update(package_id, package_update)
    
    if not updated_package:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新失败"
        )
    
    return ResponseBase(message="套餐更新成功")

@router.delete("/packages/{package_id}", response_model=ResponseBase)
def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除套餐"""
    package_service = PackageService(db)
    
    package = package_service.get(package_id)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    success = package_service.delete(package_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="删除失败"
        )
    
    return ResponseBase(message="套餐删除成功")

# ==================== 邮件队列管理 ====================

@router.get("/email-queue", response_model=ResponseBase)
def get_email_queue(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    email_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取邮件队列"""
    from app.models.email import EmailQueue
    
    query = db.query(EmailQueue)
    
    if status:
        query = query.filter(EmailQueue.status == status)
    if email_type:
        query = query.filter(EmailQueue.type == email_type)
    
    total = query.count()
    emails = query.offset((page - 1) * size).limit(size).all()
    
    return ResponseBase(
        data={
            "emails": [
                {
                    "id": email.id,
                    "to_email": email.to_email,
                    "subject": email.subject,
                    "type": email.type,
                    "status": email.status,
                    "retry_count": email.retry_count,
                    "error_message": email.error_message,
                    "created_at": email.created_at.isoformat(),
                    "updated_at": email.updated_at.isoformat() if email.updated_at else None
                }
                for email in emails
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    )

@router.post("/email-queue/{email_id}/resend", response_model=ResponseBase)
def resend_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """重新发送邮件"""
    from app.models.email import EmailQueue
    
    email = db.query(EmailQueue).filter(EmailQueue.id == email_id).first()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮件不存在"
        )
    
    # 重置邮件状态
    email.status = "pending"
    email.retry_count = 0
    email.error_message = ""
    email.updated_at = datetime.utcnow()
    
    db.commit()
    
    return ResponseBase(message="邮件已重新加入发送队列")

# ==================== 统计信息 ====================

@router.get("/stats", response_model=ResponseBase)
def get_admin_stats(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取管理端统计信息"""
    user_service = UserService(db)
    order_service = OrderService(db)
    subscription_service = SubscriptionService(db)
    
    # 用户统计
    total_users = user_service.count()
    active_users = user_service.count_active_users(30)
    recent_users = user_service.count_recent_users(7)
    
    # 订单统计
    total_orders = order_service.count()
    pending_orders = order_service.count_by_status("pending")
    paid_orders = order_service.count_by_status("paid")
    
    # 订阅统计
    total_subscriptions = subscription_service.count()
    active_subscriptions = subscription_service.count_active()
    expiring_subscriptions = subscription_service.count_expiring_soon(7)
    
    # 收入统计
    total_revenue = order_service.get_total_revenue()
    today_revenue = order_service.get_revenue_since(
        datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    )
    
    return ResponseBase(
        data={
            "users": {
                "total": total_users,
                "active": active_users,
                "recent_7_days": recent_users
            },
            "orders": {
                "total": total_orders,
                "pending": pending_orders,
                "paid": paid_orders
            },
            "subscriptions": {
                "total": total_subscriptions,
                "active": active_subscriptions,
                "expiring_7_days": expiring_subscriptions
            },
            "revenue": {
                "total": float(total_revenue),
                "today": float(today_revenue)
            }
        }
    ) 