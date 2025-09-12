from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.payment_config import PaymentConfigService
from app.schemas.payment_config import (
    PaymentConfig, PaymentConfigCreate, PaymentConfigUpdate,
    PaymentConfigList
)
from app.core.auth import get_current_admin_user

router = APIRouter()

@router.get("/", response_model=PaymentConfigList)
def get_payment_configs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    pay_type: Optional[str] = Query(None, description="支付类型过滤"),
    status: Optional[int] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取支付配置列表"""
    skip = (page - 1) * size
    service = PaymentConfigService(db)

    payment_configs = service.get_payment_configs(
        skip=skip,
        limit=size,
        pay_type_filter=pay_type,
        status_filter=status
    )

    # 计算总数
    total = len(service.get_payment_configs())

    return PaymentConfigList(
        items=payment_configs,
        total=total,
        page=page,
        size=size
    )

@router.get("/active", response_model=List[PaymentConfig])
def get_active_payment_configs(
    db: Session = Depends(get_db)
):
    """获取所有启用的支付配置（公开接口）"""
    service = PaymentConfigService(db)
    return service.get_active_payment_configs()

@router.get("/{payment_config_id}", response_model=PaymentConfig)
def get_payment_config(
    payment_config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """根据ID获取支付配置"""
    service = PaymentConfigService(db)
    payment_config = service.get_payment_config(payment_config_id)

    if not payment_config:
        raise HTTPException(status_code=404, detail="支付配置不存在")

    return payment_config

@router.post("/", response_model=PaymentConfig)
def create_payment_config(
    payment_config: PaymentConfigCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """创建支付配置"""
    service = PaymentConfigService(db)
    return service.create_payment_config(payment_config)

@router.put("/{payment_config_id}", response_model=PaymentConfig)
def update_payment_config(
    payment_config_id: int,
    payment_config: PaymentConfigUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """更新支付配置"""
    service = PaymentConfigService(db)
    updated_config = service.update_payment_config(payment_config_id, payment_config)

    if not updated_config:
        raise HTTPException(status_code=404, detail="支付配置不存在")

    return updated_config

@router.delete("/{payment_config_id}")
def delete_payment_config(
    payment_config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """删除支付配置"""
    service = PaymentConfigService(db)
    success = service.delete_payment_config(payment_config_id)

    if not success:
        raise HTTPException(status_code=404, detail="支付配置不存在")

    return {"message": "支付配置删除成功"}

@router.put("/{payment_config_id}/status", response_model=PaymentConfig)
def update_payment_config_status(
    payment_config_id: int,
    status: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """更新支付配置状态"""
    if status not in [0, 1]:
        raise HTTPException(status_code=400, detail="状态值无效")

    service = PaymentConfigService(db)
    updated_config = service.update_payment_config_status(payment_config_id, status)

    if not updated_config:
        raise HTTPException(status_code=404, detail="支付配置不存在")

    return updated_config

@router.put("/{payment_config_id}/config", response_model=PaymentConfig)
def update_payment_config_config(
    payment_config_id: int,
    config: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """更新支付配置内容"""
    service = PaymentConfigService(db)
    updated_config = service.update_payment_config_config(payment_config_id, config)

    if not updated_config:
        raise HTTPException(status_code=404, detail="支付配置不存在")

    return updated_config

@router.get("/{payment_config_id}/config")
def get_payment_config_config(
    payment_config_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取支付配置内容"""
    service = PaymentConfigService(db)
    config = service.get_payment_config_config(payment_config_id)

    if config is None:
        raise HTTPException(status_code=404, detail="支付配置不存在")

    return {"config": config}


@router.post("/bulk-enable")
def bulk_enable_payment_configs(
    config_ids: List[int],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """批量启用支付配置"""
    service = PaymentConfigService(db)
    count = service.bulk_update_status(config_ids, 1)

    return {"message": f"成功启用 {count} 个支付配置"}

@router.post("/bulk-disable")
def bulk_disable_payment_configs(
    config_ids: List[int],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """批量禁用支付配置"""
    service = PaymentConfigService(db)
    count = service.bulk_update_status(config_ids, 0)

    return {"message": f"成功禁用 {count} 个支付配置"}

@router.post("/bulk-delete")
def bulk_delete_payment_configs(
    config_ids: List[int],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """批量删除支付配置"""
    service = PaymentConfigService(db)
    count = service.bulk_delete(config_ids)

    return {"message": f"成功删除 {count} 个支付配置"}

@router.get("/stats/summary")
def get_payment_config_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取支付配置统计信息"""
    service = PaymentConfigService(db)
    return service.get_payment_config_stats()

@router.get("/export")
def export_payment_configs(
    pay_type: Optional[str] = Query(None, description="支付类型过滤"),
    status: Optional[int] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """导出支付配置"""
    service = PaymentConfigService(db)
    payment_configs = service.get_payment_configs(
        pay_type_filter=pay_type,
        status_filter=status
    )

    # 这里可以实现Excel导出功能
    # 暂时返回JSON格式
    return {
        "data": payment_configs,
        "filename": f"payment_configs_{pay_type or 'all'}_{status or 'all'}.json"
    }
