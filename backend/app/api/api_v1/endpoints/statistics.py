from typing import Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract

from app.core.database import get_db
from app.schemas.common import ResponseBase
from app.services.user import UserService
from app.services.subscription import SubscriptionService
from app.services.order import OrderService
from app.utils.security import get_current_admin_user

router = APIRouter()

@router.get("/admin/statistics/users", response_model=ResponseBase)
def get_user_statistics(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取用户统计"""
    user_service = UserService(db)
    
    # 计算时间范围
    now = datetime.utcnow()
    if period == "7d":
        start_date = now - timedelta(days=7)
    elif period == "30d":
        start_date = now - timedelta(days=30)
    elif period == "90d":
        start_date = now - timedelta(days=90)
    else:  # 1y
        start_date = now - timedelta(days=365)
    
    # 基础统计
    total_users = user_service.count()
    active_users = user_service.count_active_users(30)
    verified_users = user_service.count_verified_users()
    today_users = user_service.count_users_since(now.replace(hour=0, minute=0, second=0, microsecond=0))
    
    # 注册趋势
    registration_trend = []
    current_date = start_date
    while current_date <= now:
        next_date = current_date + timedelta(days=1)
        count = user_service.count_users_since(current_date, next_date)
        registration_trend.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "count": count
        })
        current_date = next_date
    
    # 用户地域分布（示例数据）
    region_distribution = [
        {"region": "中国大陆", "count": int(total_users * 0.8)},
        {"region": "香港", "count": int(total_users * 0.1)},
        {"region": "台湾", "count": int(total_users * 0.05)},
        {"region": "其他", "count": int(total_users * 0.05)}
    ]
    
    return ResponseBase(
        data={
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "today_users": today_users,
            "registration_trend": registration_trend,
            "region_distribution": region_distribution,
            "period": period
        }
    )

@router.get("/admin/statistics/subscriptions", response_model=ResponseBase)
def get_subscription_statistics(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取订阅统计"""
    subscription_service = SubscriptionService(db)
    
    # 基础统计
    total_subscriptions = subscription_service.count()
    active_subscriptions = subscription_service.count_active()
    expired_subscriptions = subscription_service.count_expired()
    expiring_soon = subscription_service.count_expiring_soon(7)
    expiring_in_30_days = subscription_service.count_expiring_soon(30)
    
    # 设备统计
    total_devices = subscription_service.count_total_devices()
    online_devices = subscription_service.count_online_devices()
    
    # 订阅时长分布
    duration_distribution = [
        {"duration": "1-7天", "count": int(total_subscriptions * 0.1)},
        {"duration": "8-30天", "count": int(total_subscriptions * 0.3)},
        {"duration": "31-90天", "count": int(total_subscriptions * 0.4)},
        {"duration": "90天以上", "count": int(total_subscriptions * 0.2)}
    ]
    
    # 设备使用情况
    device_usage = [
        {"devices": "0-1个", "count": int(total_subscriptions * 0.4)},
        {"devices": "2-3个", "count": int(total_subscriptions * 0.4)},
        {"devices": "4-5个", "count": int(total_subscriptions * 0.15)},
        {"devices": "5个以上", "count": int(total_subscriptions * 0.05)}
    ]
    
    return ResponseBase(
        data={
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "expired_subscriptions": expired_subscriptions,
            "expiring_soon": expiring_soon,
            "expiring_in_30_days": expiring_in_30_days,
            "total_devices": total_devices,
            "online_devices": online_devices,
            "duration_distribution": duration_distribution,
            "device_usage": device_usage
        }
    )

@router.get("/admin/statistics/orders", response_model=ResponseBase)
def get_order_statistics(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取订单统计"""
    order_service = OrderService(db)
    
    # 计算时间范围
    now = datetime.utcnow()
    if period == "7d":
        start_date = now - timedelta(days=7)
    elif period == "30d":
        start_date = now - timedelta(days=30)
    elif period == "90d":
        start_date = now - timedelta(days=90)
    else:  # 1y
        start_date = now - timedelta(days=365)
    
    # 基础统计
    total_orders = order_service.count()
    total_revenue = order_service.get_total_revenue()
    today_orders = order_service.count_orders_since(now.replace(hour=0, minute=0, second=0, microsecond=0))
    today_revenue = order_service.get_revenue_since(now.replace(hour=0, minute=0, second=0, microsecond=0))
    
    # 订单状态分布
    status_distribution = [
        {"status": "待支付", "count": order_service.count_by_status("pending")},
        {"status": "已支付", "count": order_service.count_by_status("paid")},
        {"status": "已取消", "count": order_service.count_by_status("cancelled")},
        {"status": "已过期", "count": order_service.count_by_status("expired")}
    ]
    
    # 收入趋势
    revenue_trend = []
    current_date = start_date
    while current_date <= now:
        next_date = current_date + timedelta(days=1)
        revenue = order_service.get_revenue_since(current_date, next_date)
        revenue_trend.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "revenue": float(revenue)
        })
        current_date = next_date
    
    # 支付方式统计
    payment_methods = [
        {"method": "支付宝", "count": int(total_orders * 0.8), "revenue": float(total_revenue * 0.8)},
        {"method": "微信支付", "count": int(total_orders * 0.15), "revenue": float(total_revenue * 0.15)},
        {"method": "其他", "count": int(total_orders * 0.05), "revenue": float(total_revenue * 0.05)}
    ]
    
    return ResponseBase(
        data={
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "today_orders": today_orders,
            "today_revenue": float(today_revenue),
            "status_distribution": status_distribution,
            "revenue_trend": revenue_trend,
            "payment_methods": payment_methods,
            "period": period
        }
    )

@router.get("/admin/statistics/overview", response_model=ResponseBase)
def get_statistics_overview(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取统计概览"""
    user_service = UserService(db)
    subscription_service = SubscriptionService(db)
    order_service = OrderService(db)
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    yesterday_end = today_start
    
    # 今日数据
    today_users = user_service.count_users_since(today_start)
    today_orders = order_service.count_orders_since(today_start)
    today_revenue = order_service.get_revenue_since(today_start)
    
    # 昨日数据
    yesterday_users = user_service.count_users_since(yesterday_start, yesterday_end)
    yesterday_orders = order_service.count_orders_since(yesterday_start, yesterday_end)
    yesterday_revenue = order_service.get_revenue_since(yesterday_start, yesterday_end)
    
    # 总体数据
    total_users = user_service.count()
    total_subscriptions = subscription_service.count()
    total_orders = order_service.count()
    total_revenue = order_service.get_total_revenue()
    
    # 活跃数据
    active_users = user_service.count_active_users(30)
    active_subscriptions = subscription_service.count_active()
    online_devices = subscription_service.count_online_devices()
    
    return ResponseBase(
        data={
            "today": {
                "users": today_users,
                "orders": today_orders,
                "revenue": float(today_revenue)
            },
            "yesterday": {
                "users": yesterday_users,
                "orders": yesterday_orders,
                "revenue": float(yesterday_revenue)
            },
            "total": {
                "users": total_users,
                "subscriptions": total_subscriptions,
                "orders": total_orders,
                "revenue": float(total_revenue)
            },
            "active": {
                "users": active_users,
                "subscriptions": active_subscriptions,
                "devices": online_devices
            }
        }
    )

@router.get("/admin/statistics/export", response_model=ResponseBase)
def export_statistics(
    type: str = Query(..., regex="^(users|subscriptions|orders)$"),
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """导出统计数据"""
    if type == "users":
        user_service = UserService(db)
        users = user_service.get_multi()
        data = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            for user in users
        ]
    elif type == "subscriptions":
        subscription_service = SubscriptionService(db)
        subscriptions = subscription_service.get_all()
        data = [
            {
                "id": sub.id,
                "user_id": sub.user_id,
                "subscription_key": sub.subscription_key,
                "device_limit": sub.device_limit,
                "expire_time": sub.expire_time.isoformat() if sub.expire_time else None,
                "created_at": sub.created_at.isoformat()
            }
            for sub in subscriptions
        ]
    else:  # orders
        order_service = OrderService(db)
        orders = order_service.get_all()
        data = [
            {
                "id": order.id,
                "order_no": order.order_no,
                "user_id": order.user_id,
                "amount": float(order.amount),
                "status": order.status,
                "payment_method": order.payment_method,
                "created_at": order.created_at.isoformat()
            }
            for order in orders
        ]
    
    if format == "csv":
        # 这里应该实现CSV导出逻辑
        return ResponseBase(
            message="CSV导出功能待实现",
            data={"count": len(data)}
        )
    else:
        return ResponseBase(
            data={
                "type": type,
                "format": format,
                "count": len(data),
                "data": data
            }
        ) 