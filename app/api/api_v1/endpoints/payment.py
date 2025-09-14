from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.payment import PaymentTransaction
from app.models.payment_config import PaymentConfig
from app.models.order import Order
from app.models.user import User
from app.schemas.payment import (
    PaymentCreate, 
    PaymentUpdate, 
    PaymentResponse,
    PaymentCallback,
    PaymentMethod
)
from app.services.payment import PaymentService
from app.core.auth import get_current_user

router = APIRouter()

@router.post("/create")
async def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建支付订单"""
    try:
        
        # 验证订单
        order = db.query(Order).filter(
            Order.order_no == payment_data.order_no,
            Order.user_id == current_user.id
        ).first()
        
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        if order.status != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="订单状态不正确"
            )
        
        # 使用新的支付服务创建支付
        payment_service = PaymentService(db)
        payment_response = payment_service.create_payment(payment_data)
        
        # 返回前端期望的格式
        result = {
            "payment_url": payment_response.payment_url,
            "order_no": payment_response.order_no,
            "amount": payment_response.amount,
            "payment_method": payment_response.payment_method,
            "status": payment_response.status
        }
        return result
        
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"创建支付订单失败: {str(e)}" if str(e) else "创建支付订单失败: 未知错误"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )

@router.get("/methods")
async def get_payment_methods(db: Session = Depends(get_db)):
    """获取支持的支付方式"""
    payment_service = PaymentService(db)
    return payment_service.get_available_payment_methods()

@router.get("/transactions", response_model=List[PaymentResponse])
async def get_payment_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    order_no: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """获取用户支付交易记录"""
    query = db.query(PaymentTransaction).filter(
        PaymentTransaction.user_id == current_user.id
    )
    
    # 如果指定了订单号，按订单号过滤
    if order_no:
        query = query.join(Order).filter(Order.order_no == order_no)
    
    payments = query.offset(skip).limit(limit).all()
    
    return [
        PaymentResponse(
            id=payment.id,
            payment_url=payment.payment_data.get("payment_url", "") if payment.payment_data else "",
            order_no=payment.order.order_no if payment.order else "",
            amount=payment.amount / 100,  # 转换为元
            payment_method=payment.payment_data.get("method", "") if payment.payment_data else "",
            status=payment.status,
            created_at=payment.created_at
        )
        for payment in payments
    ]

@router.get("/transactions/{payment_id}", response_model=PaymentResponse)
async def get_payment_transaction(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取支付交易详情"""
    payment = db.query(PaymentTransaction).filter(
        PaymentTransaction.id == payment_id,
        PaymentTransaction.user_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="支付交易不存在"
        )
    
    return PaymentResponse(
        id=payment.id,
        payment_url=payment.payment_data.get("payment_url", "") if payment.payment_data else "",
        order_no=payment.order.order_no if payment.order else "",
        amount=payment.amount / 100,  # 转换为元
        payment_method=payment.payment_data.get("method", "") if payment.payment_data else "",
        status=payment.status,
        created_at=payment.created_at
    )

@router.post("/notify/{payment_method}")
async def payment_notify(
    payment_method: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """支付回调通知"""
    try:
        # 获取回调参数
        if payment_method in ['alipay']:
            # 支付宝回调参数在query string中
            params = dict(request.query_params)
        else:
            # 其他支付方式的回调参数在body中
            body = await request.body()
            if request.headers.get('content-type', '').startswith('application/json'):
                params = await request.json()
            else:
                # 解析表单数据
                params = dict(await request.form())
        
        # 验证支付回调
        payment_service = PaymentService(db)
        notify = payment_service.verify_payment_notify(payment_method, params)
        
        if notify:
            return {"status": "success", "message": "支付验证成功"}
        else:
            return {"status": "failed", "message": "支付验证失败"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"支付回调处理失败: {str(e)}"
        )

@router.post("/refund/{payment_id}")
async def refund_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """申请退款"""
    try:
        payment = db.query(PaymentTransaction).filter(
            PaymentTransaction.id == payment_id,
            PaymentTransaction.user_id == current_user.id
        ).first()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付交易不存在"
            )
        
        if payment.status != 'success':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有成功的支付才能申请退款"
            )
        
        # 这里应该调用支付平台的退款接口
        # 为了演示，直接更新状态
        payment.status = 'refunded'
        db.commit()
        
        return {"status": "success", "message": "退款申请成功"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"退款申请失败: {str(e)}"
        )

@router.get("/config")
async def get_payment_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取支付配置信息"""
    # 检查用户权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    configs = db.query(PaymentConfig).all()
    return configs

@router.post("/config")
async def update_payment_config(
    config_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新支付配置"""
    # 检查用户权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        for method, config in config_data.items():
            payment_config = db.query(PaymentConfig).filter(
                PaymentConfig.payment_method == method
            ).first()
            
            if payment_config:
                payment_config.config_data = config
                payment_config.is_enabled = config.get('enabled', True)
            else:
                payment_config = PaymentConfig(
                    payment_method=method,
                    is_enabled=config.get('enabled', True),
                    config_data=config
                )
                db.add(payment_config)
        
        db.commit()
        return {"status": "success", "message": "支付配置更新成功"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新支付配置失败: {str(e)}"
        )

@router.get("/statistics")
async def get_payment_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """获取支付统计信息"""
    # 检查用户权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        query = db.query(PaymentTransaction)
        
        if start_date:
            query = query.filter(PaymentTransaction.created_at >= start_date)
        if end_date:
            query = query.filter(PaymentTransaction.created_at <= end_date)
        
        payments = query.all()
        
        # 计算统计信息
        total_amount = sum(p.amount for p in payments if p.status == 'success')
        total_count = len([p for p in payments if p.status == 'success'])
        pending_count = len([p for p in payments if p.status == 'pending'])
        failed_count = len([p for p in payments if p.status == 'failed'])
        
        # 按支付方式统计
        alipay_amount = sum(p.amount for p in payments if p.payment_method == 'alipay' and p.status == 'success')
        wechat_amount = sum(p.amount for p in payments if p.payment_method == 'wechat' and p.status == 'success')
        
        return {
            "total_amount": total_amount,
            "total_count": total_count,
            "pending_count": pending_count,
            "failed_count": failed_count,
            "alipay_amount": alipay_amount,
            "wechat_amount": wechat_amount,
            "success_rate": (total_count / len(payments) * 100) if payments else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取支付统计失败: {str(e)}"
        ) 