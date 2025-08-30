from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.schemas.payment import (
    PaymentConfigCreate, PaymentConfigUpdate, PaymentConfigInDB,
    PaymentTransactionInDB, PaymentCallbackInDB,
    PaymentRequest, PaymentResponse, PaymentCallbackRequest
)
from app.schemas.common import ResponseBase, PaginationParams
from app.services.payment import PaymentService
from app.utils.security import get_current_user, get_current_admin_user
from app.models.payment import PaymentConfig, PaymentTransaction

router = APIRouter()

# ==================== 用户端支付API ====================

@router.get("/payment-methods", response_model=ResponseBase)
def get_payment_methods(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """获取可用的支付方式"""
    payment_service = PaymentService(db)
    payment_configs = payment_service.get_active_payment_configs()
    
    return ResponseBase(
        data={
            "payment_methods": [
                {
                    "id": config.id,
                    "name": config.name,
                    "display_name": config.display_name,
                    "type": config.type,
                    "description": config.description,
                    "icon": config.icon,
                    "is_default": config.is_default
                }
                for config in payment_configs
            ]
        }
    )

@router.post("/create-payment", response_model=ResponseBase)
def create_payment(
    payment_request: PaymentRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """创建支付"""
    payment_service = PaymentService(db)
    
    # 验证订单是否属于当前用户
    # 这里需要添加订单验证逻辑
    
    payment_response = payment_service.create_payment(payment_request)
    
    if payment_response.success:
        return ResponseBase(
            message="支付创建成功",
            data={
                "payment_url": payment_response.payment_url,
                "qr_code": payment_response.qr_code,
                "transaction_id": payment_response.transaction_id
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=payment_response.message
        )

@router.get("/payment-status/{transaction_id}", response_model=ResponseBase)
def get_payment_status(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """获取支付状态"""
    payment_service = PaymentService(db)
    transaction = payment_service.get_payment_transaction(transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易记录不存在"
        )
    
    # 验证交易是否属于当前用户
    # 这里需要添加权限验证逻辑
    
    return ResponseBase(
        data={
            "transaction_id": transaction.transaction_id,
            "status": transaction.status,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "created_at": transaction.created_at.isoformat(),
            "updated_at": transaction.updated_at.isoformat() if transaction.updated_at else None
        }
    )

# ==================== 管理端支付API ====================

@router.get("/admin/payment-configs", response_model=ResponseBase)
def get_payment_configs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取支付配置列表"""
    payment_service = PaymentService(db)
    
    skip = (page - 1) * size
    configs = payment_service.db.query(PaymentConfig).offset(skip).limit(size).all()
    total = payment_service.db.query(PaymentConfig).count()
    
    return ResponseBase(
        data={
            "configs": [
                {
                    "id": config.id,
                    "name": config.name,
                    "display_name": config.display_name,
                    "type": config.type,
                    "is_active": config.is_active,
                    "is_default": config.is_default,
                    "description": config.description,
                    "icon": config.icon,
                    "sort_order": config.sort_order,
                    "created_at": config.created_at.isoformat(),
                    "updated_at": config.updated_at.isoformat() if config.updated_at else None
                }
                for config in configs
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    )

@router.post("/admin/payment-configs", response_model=ResponseBase)
def create_payment_config(
    config_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建支付配置"""
    payment_service = PaymentService(db)
    
    try:
        config = payment_service.create_payment_config(PaymentConfigCreate(**config_data))
        return ResponseBase(
            message="支付配置创建成功",
            data={"config_id": config.id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建支付配置失败: {str(e)}"
        )

@router.put("/admin/payment-configs/{config_id}", response_model=ResponseBase)
def update_payment_config(
    config_id: int,
    config_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新支付配置"""
    payment_service = PaymentService(db)
    
    try:
        config = payment_service.update_payment_config(config_id, PaymentConfigUpdate(**config_data))
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付配置不存在"
            )
        
        return ResponseBase(message="支付配置更新成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新支付配置失败: {str(e)}"
        )

@router.delete("/admin/payment-configs/{config_id}", response_model=ResponseBase)
def delete_payment_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除支付配置"""
    payment_service = PaymentService(db)
    
    success = payment_service.delete_payment_config(config_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="支付配置不存在"
        )
    
    return ResponseBase(message="支付配置删除成功")

@router.get("/admin/payment-transactions", response_model=ResponseBase)
def get_payment_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    payment_method: str = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取支付交易列表"""
    payment_service = PaymentService(db)
    
    query = payment_service.db.query(PaymentTransaction)
    
    # 添加筛选条件
    if status:
        query = query.filter(PaymentTransaction.status == status)
    if payment_method:
        query = query.filter(PaymentTransaction.payment_method == payment_method)
    
    skip = (page - 1) * size
    transactions = query.order_by(PaymentTransaction.created_at.desc()).offset(skip).limit(size).all()
    total = query.count()
    
    return ResponseBase(
        data={
            "transactions": [
                {
                    "id": trans.id,
                    "order_id": trans.order_id,
                    "transaction_id": trans.transaction_id,
                    "amount": float(trans.amount),
                    "currency": trans.currency,
                    "status": trans.status,
                    "payment_method": trans.payment_method,
                    "created_at": trans.created_at.isoformat(),
                    "updated_at": trans.updated_at.isoformat() if trans.updated_at else None
                }
                for trans in transactions
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    )

@router.get("/admin/payment-transactions/{transaction_id}", response_model=ResponseBase)
def get_payment_transaction_detail(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取支付交易详情"""
    payment_service = PaymentService(db)
    transaction = payment_service.get_payment_transaction(transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易记录不存在"
        )
    
    return ResponseBase(
        data={
            "id": transaction.id,
            "order_id": transaction.order_id,
            "payment_config_id": transaction.payment_config_id,
            "transaction_id": transaction.transaction_id,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "status": transaction.status,
            "payment_method": transaction.payment_method,
            "gateway_response": transaction.gateway_response,
            "callback_data": transaction.callback_data,
            "created_at": transaction.created_at.isoformat(),
            "updated_at": transaction.updated_at.isoformat() if transaction.updated_at else None
        }
    )

# ==================== 支付回调API ====================

@router.post("/payment-callback/{payment_method}")
def payment_callback(
    payment_method: str,
    callback_data: dict,
    db: Session = Depends(get_db)
) -> Any:
    """支付回调处理"""
    payment_service = PaymentService(db)
    
    try:
        # 获取支付配置
        config = payment_service.get_payment_config_by_name(payment_method)
        if not config or not config.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="支付方式不可用"
            )
        
        # 验证回调签名
        if not payment_service._verify_callback_signature(callback_data, config):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="回调签名验证失败"
            )
        
        # 处理回调
        result = payment_service._process_payment_callback(config, callback_data)
        
        return {"status": "success", "message": "回调处理成功"}
        
    except Exception as e:
        # 记录错误日志
        print(f"支付回调处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="回调处理失败"
        )

# ==================== 支付统计API ====================

@router.get("/admin/payment-stats", response_model=ResponseBase)
def get_payment_stats(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取支付统计信息"""
    payment_service = PaymentService(db)
    
    # 统计各种状态的交易数量
    total_transactions = payment_service.db.query(PaymentTransaction).count()
    pending_transactions = payment_service.db.query(PaymentTransaction).filter(
        PaymentTransaction.status == "pending"
    ).count()
    success_transactions = payment_service.db.query(PaymentTransaction).filter(
        PaymentTransaction.status == "success"
    ).count()
    failed_transactions = payment_service.db.query(PaymentTransaction).filter(
        PaymentTransaction.status == "failed"
    ).count()
    
    # 统计各种支付方式的使用情况
    payment_methods = payment_service.db.query(
        PaymentTransaction.payment_method,
        func.count(PaymentTransaction.id).label('count'),
        func.sum(PaymentTransaction.amount).label('total_amount')
    ).group_by(PaymentTransaction.payment_method).all()
    
    return ResponseBase(
        data={
            "total_transactions": total_transactions,
            "pending_transactions": pending_transactions,
            "success_transactions": success_transactions,
            "failed_transactions": failed_transactions,
            "payment_methods": [
                {
                    "method": method.payment_method,
                    "count": method.count,
                    "total_amount": float(method.total_amount) if method.total_amount else 0
                }
                for method in payment_methods
            ]
        }
    ) 