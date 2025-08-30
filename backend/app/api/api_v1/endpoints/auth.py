from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import re

from app.core.config import settings
from app.core.database import get_db
from app.schemas.user import UserLogin, UserCreate, User, Token
from app.schemas.common import ResponseBase
from app.services.user import UserService
from app.utils.security import create_access_token, create_refresh_token

router = APIRouter()

def validate_qq_email(email: str) -> bool:
    """验证是否为QQ邮箱"""
    qq_pattern = r'^\d+@qq\.com$'
    return bool(re.match(qq_pattern, email))

def extract_qq_number(email: str) -> str:
    """从QQ邮箱中提取QQ号码"""
    return email.split('@')[0]

@router.post("/register", response_model=ResponseBase)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """用户注册 - 只允许QQ邮箱注册"""
    user_service = UserService(db)
    
    # 验证邮箱格式
    if not validate_qq_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只允许使用QQ邮箱注册"
        )
    
    # 提取QQ号码作为用户名
    qq_number = extract_qq_number(user_in.email)
    user_in.username = qq_number
    
    # 检查用户是否已存在
    if user_service.get_by_username(qq_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该QQ号码已被注册"
        )
    
    if user_service.get_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该QQ邮箱已被注册"
        )
    
    # 创建用户
    user = user_service.create(user_in)
    
    return ResponseBase(
        message="注册成功，请查收QQ邮箱验证邮件",
        data={"user_id": user.id, "qq": qq_number}
    )

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """用户登录 - 支持QQ号码或QQ邮箱登录"""
    user_service = UserService(db)
    
    # 判断输入的是QQ号码还是邮箱
    login_identifier = form_data.username
    if '@' in login_identifier:
        # 邮箱登录
        user = user_service.authenticate_by_email(login_identifier, form_data.password)
    else:
        # QQ号码登录
        user = user_service.authenticate(login_identifier, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="QQ号码或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账户已被禁用"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先验证QQ邮箱"
        )
    
    # 更新最后登录时间
    user_service.update_last_login(user.id)
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    # 创建刷新令牌
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """刷新访问令牌"""
    from app.utils.security import verify_token
    
    # 验证刷新令牌
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    username = payload.get("sub")
    user_id = payload.get("user_id")
    
    if not username or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌数据"
        )
    
    # 检查用户是否存在
    user_service = UserService(db)
    user = user_service.get_by_username(username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username, "user_id": user_id},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/verify-email", response_model=ResponseBase)
def verify_email(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """验证QQ邮箱"""
    from app.utils.security import verify_token
    
    # 验证令牌
    payload = verify_token(token)
    if not payload or payload.get("type") != "email_verification":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的验证令牌"
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的令牌数据"
        )
    
    # 更新用户验证状态
    user_service = UserService(db)
    user = user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.is_verified:
        return ResponseBase(message="QQ邮箱已验证")
    
    user_service.verify_email(user_id)
    
    return ResponseBase(message="QQ邮箱验证成功")

@router.post("/forgot-password", response_model=ResponseBase)
def forgot_password(
    email: str,
    db: Session = Depends(get_db)
) -> Any:
    """忘记密码 - 只支持QQ邮箱"""
    # 验证QQ邮箱格式
    if not validate_qq_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请输入正确的QQ邮箱地址"
        )
    
    user_service = UserService(db)
    user = user_service.get_by_email(email)
    
    if not user:
        # 为了安全，不暴露用户是否存在
        return ResponseBase(message="如果QQ邮箱存在，重置链接已发送到您的QQ邮箱")
    
    # 发送密码重置邮件
    user_service.send_password_reset_email(user)
    
    return ResponseBase(message="重置链接已发送到您的QQ邮箱，请查收")

@router.post("/reset-password", response_model=ResponseBase)
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
) -> Any:
    """重置密码"""
    from app.utils.security import verify_token
    
    # 验证令牌
    payload = verify_token(token)
    if not payload or payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的重置令牌"
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的令牌数据"
        )
    
    # 更新密码
    user_service = UserService(db)
    user = user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user_service.update_password(user_id, new_password)
    
    return ResponseBase(message="密码重置成功") 