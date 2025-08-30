from datetime import datetime
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order import OrderCreate, OrderInDB
from app.schemas.common import ResponseBase, PaginationParams
from app.services.order import OrderService
from app.services.package import PackageService
from app.services.subscription import SubscriptionService
from app.utils.security import get_current_user, generate_order_no

router = APIRouter()

@router.post("/", response_model=ResponseBase)
def create_order(
    order_data: OrderCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """创建订单"""
    order_service = OrderService(db)
    package_service = PackageService(db)
    
    # 检查套餐是否存在
    package = package_service.get(order_data.package_id)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    # 创建订单
    order = order_service.create_order(
        user_id=current_user.id,
        package_id=order_data.package_id,
        payment_method=order_data.payment_method,
        amount=package.price
    )
    
    # 生成支付URL
    payment_url = order_service.generate_payment_url(order)
    
    return ResponseBase(
        message="订单创建成功",
        data={
            "order_id": order.id,
            "order_no": order.order_no,
            "amount": order.amount,
            "payment_url": payment_url,
            "payment_qr_code": payment_url  # 用于生成二维码
        }
    )

@router.get("/user-orders", response_model=ResponseBase)
def get_user_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """获取用户订单列表"""
    order_service = OrderService(db)
    
    # 计算偏移量
    skip = (page - 1) * size
    
    # 获取订单列表
    orders, total = order_service.get_user_orders(
        user_id=current_user.id,
        skip=skip,
        limit=size
    )
    
    return ResponseBase(
        data={
            "orders": [
                {
                    "id": order.id,
                    "order_no": order.order_no,
                    "package_name": order.package.name if order.package else "未知套餐",
                    "package_duration": order.package.duration if order.package else 0,
                    "package_device_limit": order.package.device_limit if order.package else 0,
                    "amount": order.amount,
                    "status": order.status,
                    "payment_method": order.payment_method,
                    "created_at": order.created_at.isoformat(),
                    "payment_time": order.payment_time.isoformat() if order.payment_time else None,
                    "expire_time": order.expire_time.isoformat() if order.expire_time else None
                }
                for order in orders
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    )

@router.get("/{order_no}/status", response_model=ResponseBase)
def get_order_status(
    order_no: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取订单状态"""
    order_service = OrderService(db)
    
    # 获取订单
    order = order_service.get_by_order_no(order_no)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 检查订单是否属于当前用户
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此订单"
        )
    
    return ResponseBase(
        data={
            "order_no": order.order_no,
            "status": order.status,
            "amount": order.amount,
            "payment_method": order.payment_method,
            "created_at": order.created_at.isoformat(),
            "payment_time": order.payment_time.isoformat() if order.payment_time else None
        }
    )

@router.post("/{order_no}/cancel", response_model=ResponseBase)
def cancel_order(
    order_no: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """取消订单"""
    order_service = OrderService(db)
    
    # 获取订单
    order = order_service.get_by_order_no(order_no)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 检查订单是否属于当前用户
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此订单"
        )
    
    # 检查订单状态
    if order.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能取消待支付的订单"
        )
    
    # 取消订单
    success = order_service.cancel_order(order_no)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="取消订单失败"
        )
    
    return ResponseBase(message="订单取消成功")

@router.post("/payment/notify", response_model=ResponseBase)
def payment_notify(
    db: Session = Depends(get_db)
) -> Any:
    """支付回调通知"""
    # 这里应该处理第三方支付平台的回调
    # 验证签名、更新订单状态等
    
    return ResponseBase(message="success") 