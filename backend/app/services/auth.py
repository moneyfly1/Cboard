from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import re

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.core.settings_manager import settings_manager

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_data: UserCreate) -> User:
        """注册新用户"""
        # 检查是否允许注册
        if not settings_manager.is_registration_allowed(self.db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="注册功能已禁用"
            )
        
        # 验证邮箱格式
        if not settings_manager.validate_email(user_data.email, self.db):
            if settings_manager.is_qq_email_only(self.db):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="仅支持QQ邮箱注册"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱格式不正确"
                )
        
        # 验证密码强度
        if not settings_manager.validate_password(user_data.password, self.db):
            min_length = settings_manager.get_min_password_length(self.db)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"密码必须至少包含{min_length}个字符，包括字母、数字和特殊字符"
            )
        
        # 检查邮箱是否已存在
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册"
            )
        
        # 创建用户
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            is_active=False if settings_manager.is_email_verification_required(self.db) else True,
            is_verified=False if settings_manager.is_email_verification_required(self.db) else True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """用户认证"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="账户已被禁用"
            )
        
        # 检查邮箱验证
        if settings_manager.is_email_verification_required(self.db) and not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请先验证邮箱"
            )
        
        return user

    def create_user_token(self, user: User) -> Dict[str, Any]:
        """创建用户访问令牌"""
        # 获取会话超时时间
        session_timeout = settings_manager.get_session_timeout(self.db)
        expires_delta = timedelta(minutes=session_timeout)
        
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "is_admin": user.is_admin},
            expires_delta=expires_delta
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": session_timeout * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_admin": user.is_admin,
                "is_verified": user.is_verified
            }
        }

    def verify_email(self, token: str) -> bool:
        """验证邮箱"""
        # 这里需要实现邮箱验证逻辑
        # 简化实现，实际需要验证token
        return True

    def reset_password(self, email: str) -> bool:
        """重置密码"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return False
        
        # 检查邮件功能是否启用
        if not settings_manager.is_email_enabled(self.db):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="邮件服务未配置"
            )
        
        # 这里需要实现密码重置逻辑
        # 发送重置邮件等
        return True

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密码不正确"
            )
        
        # 验证新密码强度
        if not settings_manager.validate_password(new_password, self.db):
            min_length = settings_manager.get_min_password_length(self.db)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"密码必须至少包含{min_length}个字符，包括字母、数字和特殊字符"
            )
        
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        return True

    def update_user_profile(self, user_id: int, profile_data: UserUpdate) -> Optional[User]:
        """更新用户资料"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # 如果更新邮箱，需要验证格式
        if profile_data.email and profile_data.email != user.email:
            if not settings_manager.validate_email(profile_data.email, self.db):
                if settings_manager.is_qq_email_only(self.db):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="仅支持QQ邮箱"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="邮箱格式不正确"
                    )
            
            # 检查邮箱是否已被其他用户使用
            existing_user = self.db.query(User).filter(
                User.email == profile_data.email,
                User.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该邮箱已被其他用户使用"
                )
        
        # 更新用户信息
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()

    def activate_user(self, user_id: int) -> bool:
        """激活用户"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = True
        self.db.commit()
        return True

    def deactivate_user(self, user_id: int) -> bool:
        """停用用户"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        return True

    def verify_user_email(self, user_id: int) -> bool:
        """验证用户邮箱"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_verified = True
        self.db.commit()
        return True

    def make_admin(self, user_id: int) -> bool:
        """设置用户为管理员"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_admin = True
        self.db.commit()
        return True

    def remove_admin(self, user_id: int) -> bool:
        """移除用户管理员权限"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_admin = False
        self.db.commit()
        return True 