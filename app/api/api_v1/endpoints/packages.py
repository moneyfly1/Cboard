from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.package import Package
from app.schemas.common import ResponseBase
from app.services.package import PackageService
from app.utils.security import get_current_user

router = APIRouter()

@router.get("/", response_model=ResponseBase)
def get_packages(
    db: Session = Depends(get_db)
) -> Any:
    """获取套餐列表"""
    package_service = PackageService(db)
    packages = package_service.get_active_packages()
    
    # 转换为字典格式，包含所有必要字段
    package_list = [
        {
            "id": pkg.id,
            "name": pkg.name,
            "price": float(pkg.price),  # 转换为float避免Decimal序列化问题
            "duration_days": pkg.duration_days,
            "device_limit": pkg.device_limit,
            "description": pkg.description,
            "is_active": pkg.is_active,
            "sort_order": getattr(pkg, 'sort_order', 1),
            "bandwidth_limit": getattr(pkg, 'bandwidth_limit', None)
        }
        for pkg in packages
    ]
    
    return ResponseBase(
        data={"packages": package_list},
        message="获取套餐列表成功"
    )

@router.get("/{package_id}", response_model=ResponseBase)
def get_package(
    package_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """获取套餐详情"""
    package_service = PackageService(db)
    package = package_service.get(package_id)
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    return ResponseBase(
        data={
            "package": {
                "id": package.id,
                "name": package.name,
                "price": package.price,
                "duration_days": package.duration_days,
                "device_limit": package.device_limit,
                "description": package.description,
                "is_active": package.is_active
            }
        }
    ) 