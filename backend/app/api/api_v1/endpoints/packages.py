from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order import PackageInDB
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
                    "is_recommended": pkg.is_recommended,
                    "is_popular": pkg.is_popular
                }
                for pkg in packages
            ]
        }
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
                "duration": package.duration,
                "device_limit": package.device_limit,
                "description": package.description,
                "is_recommended": package.is_recommended,
                "is_popular": package.is_popular,
                "features": package.features
            }
        }
    ) 