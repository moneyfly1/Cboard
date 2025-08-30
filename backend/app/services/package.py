from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.order import Package
from app.schemas.order import PackageCreate, PackageUpdate

class PackageService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, package_id: int) -> Optional[Package]:
        """根据ID获取套餐"""
        return self.db.query(Package).filter(Package.id == package_id).first()

    def get_all_packages(self) -> List[Package]:
        """获取所有套餐"""
        return self.db.query(Package).order_by(Package.id.desc()).all()

    def get_active_packages(self) -> List[Package]:
        """获取活跃套餐"""
        return self.db.query(Package).filter(Package.is_active == True).order_by(Package.id.desc()).all()

    def create(self, package_in: PackageCreate) -> Package:
        """创建套餐"""
        package = Package(
            name=package_in.name,
            price=package_in.price,
            duration=package_in.duration,
            device_limit=package_in.device_limit,
            description=package_in.description,
            is_active=package_in.is_active,
            is_recommended=package_in.is_recommended,
            is_popular=package_in.is_popular,
            features=package_in.features
        )
        
        self.db.add(package)
        self.db.commit()
        self.db.refresh(package)
        return package

    def update(self, package_id: int, package_in: PackageUpdate) -> Optional[Package]:
        """更新套餐"""
        package = self.get(package_id)
        if not package:
            return None
        
        update_data = package_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(package, field, value)
        
        self.db.commit()
        self.db.refresh(package)
        return package

    def delete(self, package_id: int) -> bool:
        """删除套餐"""
        package = self.get(package_id)
        if not package:
            return False
        
        self.db.delete(package)
        self.db.commit()
        return True

    def count(self) -> int:
        """统计套餐数量"""
        return self.db.query(Package).count()

    def get_recommended_packages(self) -> List[Package]:
        """获取推荐套餐"""
        return self.db.query(Package).filter(
            Package.is_active == True,
            Package.is_recommended == True
        ).all()

    def get_popular_packages(self) -> List[Package]:
        """获取热门套餐"""
        return self.db.query(Package).filter(
            Package.is_active == True,
            Package.is_popular == True
        ).all() 