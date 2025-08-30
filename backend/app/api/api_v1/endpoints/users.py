from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import User, UserUpdate, UserPasswordChange
from app.schemas.common import ResponseBase
from app.services.user import UserService
from app.utils.security import get_current_user, verify_password, get_password_hash

router = APIRouter()

@router.get("/profile", response_model=User)
def get_user_profile(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户资料"""
    user_service = UserService(db)
    user = user_service.get(current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user

@router.put("/profile", response_model=User)
def update_user_profile(
    user_update: UserUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """更新用户资料"""
    user_service = UserService(db)
    
    # 检查用户是否存在
    user = user_service.get(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新用户资料
    updated_user = user_service.update(current_user.id, user_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新失败"
        )
    
    return updated_user

@router.post("/change-password", response_model=ResponseBase)
def change_password(
    password_change: UserPasswordChange,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """修改密码"""
    user_service = UserService(db)
    
    # 检查用户是否存在
    user = user_service.get(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证当前密码
    if not verify_password(password_change.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 更新密码
    success = user_service.update_password(current_user.id, password_change.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码修改失败"
        )
    
    return ResponseBase(message="密码修改成功")

@router.get("/login-history", response_model=ResponseBase)
def get_login_history(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取登录历史"""
    user_service = UserService(db)
    
    # 这里可以添加登录历史记录功能
    # 目前返回基本信息
    login_history = [
        {
            "login_time": current_user.last_login,
            "ip": "未知",
            "user_agent": "未知"
        }
    ]
    
    return ResponseBase(
        data={
            "login_history": login_history
        }
    ) 