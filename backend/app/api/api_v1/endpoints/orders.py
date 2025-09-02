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

@router.post("/create", response_model=ResponseBase)
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

@router.post("/", response_model=ResponseBase)
def create_order_general(
    order_data: OrderCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """创建订单（通用端点）"""
    return create_order(order_data, current_user, db)

@router.get("/", response_model=ResponseBase)
def get_user_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str = Query("", description="订单状态筛选"),
    payment_method: str = Query("", description="支付方式筛选"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """获取用户订单列表"""
    try:
        order_service = OrderService(db)
        
        # 计算偏移量
        skip = (page - 1) * size
        
        # 获取订单列表
        orders, total = order_service.get_user_orders(
            user_id=current_user.id,
            skip=skip,
            limit=size
        )
        
        # 应用筛选
        if status:
            orders = [order for order in orders if order.status == status]
        if payment_method:
            orders = [order for order in orders if getattr(order, 'payment_method_name', '') == payment_method]
        
        order_list = []
        for order in orders:
            try:
                order_data = {
                    "id": order.id,
                    "order_no": order.order_no,
                    "package_name": order.package.name if order.package else "未知套餐",
                    "package_duration": order.package.duration_days if order.package else 0,
                    "package_device_limit": order.package.device_limit if order.package else 0,
                    "amount": float(order.amount) if order.amount else 0,
                    "status": order.status,
                    "payment_method": getattr(order, 'payment_method_name', '未知'),
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "payment_time": order.payment_time.isoformat() if order.payment_time else None,
                    "expire_time": order.expire_time.isoformat() if order.expire_time else None
                }
                order_list.append(order_data)
            except Exception as e:
                # 如果单个订单处理失败，跳过它
                print(f"处理订单 {order.id} 时出错: {e}")
                continue
        
        return ResponseBase(
            data={
                "orders": order_list,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
        )
    except Exception as e:
        # 如果发生错误，返回空订单列表
        print(f"获取用户订单失败: {e}")
        return ResponseBase(
            data={
                "orders": [],
                "total": 0,
                "page": page,
                "size": size,
                "pages": 0
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

@router.get("/stats", response_model=ResponseBase)
def get_user_order_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """获取用户订单统计信息"""
    try:
        order_service = OrderService(db)
        
        # 获取所有用户订单
        orders, total = order_service.get_user_orders(
            user_id=current_user.id,
            skip=0,
            limit=1000  # 获取所有订单用于统计
        )
        
        # 计算统计信息
        total_amount = sum(float(order.amount) if order.amount else 0 for order in orders)
        pending_count = len([order for order in orders if order.status == 'pending'])
        paid_count = len([order for order in orders if order.status == 'paid'])
        cancelled_count = len([order for order in orders if order.status == 'cancelled'])
        
        return ResponseBase(
            data={
                "total": total,
                "pending": pending_count,
                "paid": paid_count,
                "cancelled": cancelled_count,
                "totalAmount": total_amount
            }
        )
    except Exception as e:
        return ResponseBase(success=False, message=f"获取订单统计失败: {str(e)}") 