from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.package import Package
from app.schemas.package import PackageCreate, PackageUpdate

class PackageService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, package_id: int) -> Optional[Package]:
        """根据ID获取套餐"""
        return self.db.query(Package).filter(Package.id == package_id).first()

    def get_by_name(self, name: str) -> Optional[Package]:
        """根据名称获取套餐"""
        return self.db.query(Package).filter(Package.name == name).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Package]:
        """获取所有套餐"""
        return self.db.query(Package).filter(Package.is_active == True).offset(skip).limit(limit).all()

    def get_active_packages(self) -> List[Package]:
        """获取所有活跃套餐"""
        return self.db.query(Package).filter(Package.is_active == True).all()

    def create(self, package: PackageCreate) -> Package:
        """创建新套餐"""
        db_package = Package(**package.dict())
        self.db.add(db_package)
        self.db.commit()
        self.db.refresh(db_package)
        return db_package

    def update(self, package_id: int, package: PackageUpdate) -> Optional[Package]:
        """更新套餐"""
        db_package = self.get(package_id)
        if not db_package:
            return None
        
        update_data = package.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_package, field, value)
        
        self.db.commit()
        self.db.refresh(db_package)
        return db_package

    def delete(self, package_id: int) -> bool:
        """删除套餐"""
        db_package = self.get(package_id)
        if not db_package:
            return False
        
        self.db.delete(db_package)
        self.db.commit()
        return True

    def deactivate(self, package_id: int) -> bool:
        """停用套餐"""
        db_package = self.get(package_id)
        if not db_package:
            return False
        
        db_package.is_active = False
        self.db.commit()
        return True

    def activate(self, package_id: int) -> bool:
        """启用套餐"""
        db_package = self.get(package_id)
        if not db_package:
            return False
        
        db_package.is_active = True
        self.db.commit()
        return True 