from fastapi import APIRouter, Depends, HTTPException, status
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

@router.post("/create", response_model=PaymentResponse)
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
        
        # 生成支付URL（简化版本）
        if payment_data.payment_method == "alipay":
            payment_url = f"https://openapi.alipay.com/gateway.do?order_no={order.order_no}&amount={payment_data.amount}&subject={payment_data.subject}"
        elif payment_data.payment_method == "wechat":
            payment_url = f"weixin://wxpay/bizpayurl?order_no={order.order_no}&amount={payment_data.amount}"
        else:
            payment_url = f"https://example.com/payment?order_no={order.order_no}&amount={payment_data.amount}"
        
        # 创建支付交易记录
        payment = PaymentTransaction(
            user_id=current_user.id,
            order_id=order.id,
            payment_method_id=1,  # 临时使用ID 1
            transaction_id=f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{order.id}",
            amount=int(payment_data.amount * 100),  # 转换为分
            currency=payment_data.currency,
            status='pending',
            payment_data={"payment_url": payment_url, "method": payment_data.payment_method}
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        return PaymentResponse(
            id=payment.id,
            payment_url=payment_url,
            order_no=payment_data.order_no,
            amount=payment_data.amount,
            payment_method=payment_data.payment_method,
            status=payment.status,
            created_at=payment.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建支付订单失败: {str(e)}"
        )

@router.get("/methods", response_model=List[PaymentMethod])
async def get_payment_methods():
    """获取支持的支付方式"""
    return [
        PaymentMethod.alipay,
        PaymentMethod.wechat
    ]

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

@router.post("/verify")
async def verify_payment(
    payment_data: PaymentCallback,
    db: Session = Depends(get_db)
):
    """验证支付结果"""
    try:
        # 验证支付签名
        if not payment_service.verify_payment(db, payment_data.dict()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="支付验证失败"
            )
        
        return {"status": "success", "message": "支付验证成功"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"支付验证失败: {str(e)}"
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