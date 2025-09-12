from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.payment import PaymentMethodService
from app.schemas.payment import (
    PaymentMethod, PaymentMethodCreate, PaymentMethodUpdate, 
    PaymentMethodList
)
from app.core.auth import get_current_admin_user

router = APIRouter()

@router.get("/", response_model=PaymentMethodList)
def get_payment_methods(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None, description="支付类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取支付方式列表"""
    skip = (page - 1) * size
    service = PaymentMethodService(db)
    
    payment_methods = service.get_payment_methods(
        skip=skip, 
        limit=size,
        type_filter=type,
        status_filter=status
    )
    
    # 计算总数
    total = len(service.get_payment_methods())
    
    return PaymentMethodList(
        items=payment_methods,
        total=total,
        page=page,
        size=size
    )

@router.get("/active", response_model=List[PaymentMethod])
def get_active_payment_methods(
    db: Session = Depends(get_db)
):
    """获取所有启用的支付方式（公开接口）"""
    service = PaymentMethodService(db)
    return service.get_active_payment_methods()

@router.get("/{payment_method_id}", response_model=PaymentMethod)
def get_payment_method(
    payment_method_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """根据ID获取支付方式"""
    service = PaymentMethodService(db)
    payment_method = service.get_payment_method(payment_method_id)
    
    if not payment_method:
        raise HTTPException(status_code=404, detail="支付方式不存在")
    
    return payment_method

@router.post("/", response_model=PaymentMethod)
def create_payment_method(
    payment_method: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """创建支付方式"""
    service = PaymentMethodService(db)
    return service.create_payment_method(payment_method)

@router.put("/{payment_method_id}", response_model=PaymentMethod)
def update_payment_method(
    payment_method_id: int,
    payment_method: PaymentMethodUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """更新支付方式"""
    service = PaymentMethodService(db)
    updated_method = service.update_payment_method(payment_method_id, payment_method)
    
    if not updated_method:
        raise HTTPException(status_code=404, detail="支付方式不存在")
    
    return updated_method

@router.delete("/{payment_method_id}")
def delete_payment_method(
    payment_method_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """删除支付方式"""
    service = PaymentMethodService(db)
    success = service.delete_payment_method(payment_method_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="支付方式不存在")
    
    return {"message": "支付方式删除成功"}

@router.put("/{payment_method_id}/status", response_model=PaymentMethod)
def update_payment_method_status(
    payment_method_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """更新支付方式状态"""
    if status not in ["active", "inactive"]:
        raise HTTPException(status_code=400, detail="状态值无效")
    
    service = PaymentMethodService(db)
    updated_method = service.update_payment_method_status(payment_method_id, status)
    
    if not updated_method:
        raise HTTPException(status_code=404, detail="支付方式不存在")
    
    return updated_method

@router.put("/{payment_method_id}/config", response_model=PaymentMethod)
def update_payment_method_config(
    payment_method_id: int,
    config: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """更新支付方式配置"""
    service = PaymentMethodService(db)
    updated_method = service.update_payment_method_config(payment_method_id, config)
    
    if not updated_method:
        raise HTTPException(status_code=404, detail="支付方式不存在")
    
    return updated_method

@router.get("/{payment_method_id}/config")
def get_payment_method_config(
    payment_method_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取支付方式配置"""
    service = PaymentMethodService(db)
    config = service.get_payment_method_config(payment_method_id)
    
    if config is None:
        raise HTTPException(status_code=404, detail="支付方式不存在")
    
    return {"config": config}


@router.post("/bulk-enable")
def bulk_enable_payment_methods(
    method_ids: List[int],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """批量启用支付方式"""
    service = PaymentMethodService(db)
    count = service.bulk_update_status(method_ids, "active")
    
    return {"message": f"成功启用 {count} 个支付方式"}

@router.post("/bulk-disable")
def bulk_disable_payment_methods(
    method_ids: List[int],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """批量禁用支付方式"""
    service = PaymentMethodService(db)
    count = service.bulk_update_status(method_ids, "inactive")
    
    return {"message": f"成功禁用 {count} 个支付方式"}

@router.post("/bulk-delete")
def bulk_delete_payment_methods(
    method_ids: List[int],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """批量删除支付方式"""
    service = PaymentMethodService(db)
    count = service.bulk_delete(method_ids)
    
    return {"message": f"成功删除 {count} 个支付方式"}

@router.get("/export")
def export_payment_methods(
    type: Optional[str] = Query(None, description="支付类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """导出支付方式配置"""
    service = PaymentMethodService(db)
    payment_methods = service.get_payment_methods(
        type_filter=type,
        status_filter=status
    )
    
    # 这里可以实现Excel导出功能
    # 暂时返回JSON格式
    return {
        "data": payment_methods,
        "filename": f"payment_methods_{type or 'all'}_{status or 'all'}.json"
    }
