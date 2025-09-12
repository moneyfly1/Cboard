from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import re
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.schemas.user import (
    UserLogin, UserCreate, EmailVerificationRequest, 
    EmailVerification, PasswordResetRequest, PasswordReset
)
from app.models.user import User
from app.schemas.common import ResponseBase, Token
from app.services.user import UserService
from app.services.email import EmailService
from app.utils.security import create_access_token, create_refresh_token
import secrets
import hashlib
from datetime import datetime, timedelta

router = APIRouter()

# 添加一个支持JSON格式的登录模型
class LoginRequest(BaseModel):
    username: str
    password: str

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def extract_username(email: str) -> str:
    """从邮箱中提取用户名"""
    return email.split('@')[0]

@router.post("/register", response_model=ResponseBase)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """用户注册 - 需要邮箱验证"""
    from app.core.auth import validate_password_strength
    
    # 验证密码强度
    is_valid, message = validate_password_strength(user_in.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"密码不符合安全要求: {message}"
        )
    
    user_service = UserService(db)
    email_service = EmailService(db)
    
    # 检查用户是否已存在
    if user_service.get_by_username(user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名已被注册"
        )
    
    if user_service.get_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )
    
    # 创建用户（未验证状态）
    user = user_service.create(user_in)
    
    # 生成邮箱验证令牌（JWT格式）
    from app.utils.security import create_access_token
    verification_token = create_access_token(
        data={"user_id": str(user.id), "type": "email_verification"},
        expires_delta=timedelta(hours=24)
    )
    
    # 保存验证令牌到数据库
    user.verification_token = verification_token
    user.verification_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    
    # 发送验证邮件
    try:
        verification_url = f"{settings.BASE_URL}/verify-email?token={verification_token}"
        success = email_service.send_verification_email(user.email, verification_token, user.username)
        if not success:
            print(f"发送验证邮件失败: 邮件服务返回失败")
        else:
            print(f"验证邮件发送成功: {user.email}")
    except Exception as e:
        # 如果邮件发送失败，记录日志但不影响注册流程
        print(f"发送验证邮件失败: {e}")
    
    return ResponseBase(
        message="注册成功，请查收邮箱验证邮件",
        data={"user_id": user.id, "username": user.username}
    )

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None
) -> Any:
    """用户登录 - 支持用户名或邮箱登录"""
    user_service = UserService(db)
    
    # 判断输入的是用户名还是邮箱
    login_identifier = form_data.username
    if '@' in login_identifier:
        # 邮箱登录
        user = user_service.authenticate_by_email(login_identifier, form_data.password)
    else:
        # 用户名登录
        user = user_service.authenticate(login_identifier, form_data.password)
    
    if not user:
        # 登录失败时不记录用户活动，因为user_id为None
        # 可以选择记录到系统日志或跳过
        pass
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        # 记录失败的登录尝试
        if request:
            user_service.log_user_activity(
                user_id=user.id,
                activity_type="login_failed",
                description="登录失败: 账户已被禁用",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账户已被禁用"
        )
    
    # 检查邮箱是否已验证
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先验证邮箱，请查收注册时发送的验证邮件"
        )
    
    # 记录成功的登录
    if request:
        user_service.log_login(
            user_id=user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            login_status="success"
        )
        
        user_service.log_user_activity(
            user_id=user.id,
            activity_type="login_success",
            description="用户登录成功",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    
    # 更新最后登录时间
    user_service.update_last_login(user.id)
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    # 创建刷新令牌
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "user_id": user.id}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
        user=user.__dict__ if hasattr(user, '__dict__') else None
    )

@router.post("/login-json", response_model=Token)
def login_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    request: Request = None
) -> Any:
    """用户登录 - JSON格式，支持用户名或邮箱登录"""
    user_service = UserService(db)
    
    # 判断输入的是用户名还是邮箱
    login_identifier = login_data.username
    if '@' in login_identifier:
        # 邮箱登录
        user = user_service.authenticate_by_email(login_identifier, login_data.password)
    else:
        # 用户名登录
        user = user_service.authenticate(login_identifier, login_data.password)
    
    if not user:
        # 登录失败时不记录用户活动，因为user_id为None
        # 可以选择记录到系统日志或跳过
        pass
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        # 记录失败的登录尝试
        if request:
            user_service.log_user_activity(
                user_id=user.id,
                activity_type="login_failed",
                description="登录失败: 账户已被禁用",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账户已被禁用"
        )
    
    # 临时禁用邮箱验证检查
    # if not user.is_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="请先验证QQ邮箱"
    #     )
    
    # 记录成功的登录
    if request:
        user_service.log_login(
            user_id=user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            login_status="success"
        )
        
        user_service.log_user_activity(
            user_id=user.id,
            activity_type="login_success",
            description="用户登录成功",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    
    # 更新最后登录时间
    user_service.update_last_login(user.id)
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    # 创建刷新令牌
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "user_id": user.id}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
        user=user.__dict__ if hasattr(user, '__dict__') else None
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
        data={"sub": str(user_id), "user_id": user_id},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/verify-email", response_model=ResponseBase)
def verify_email_post(
    request_data: dict,
    db: Session = Depends(get_db)
) -> Any:
    """验证邮箱 - POST请求"""
    token = request_data.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少验证令牌"
        )
    return verify_email_logic(token, db)

@router.get("/verify-email", response_model=ResponseBase)
def verify_email_get(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """验证邮箱 - GET请求（用于邮件链接）"""
    return verify_email_logic(token, db)

def verify_email_logic(token: str, db: Session) -> Any:
    """验证QQ邮箱逻辑"""
    from app.utils.security import verify_token
    
    # 验证令牌
    payload = verify_token(token)
    if not payload or payload.get("type") != "email_verification":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的验证令牌"
        )
    
    user_id = payload.get("user_id") or payload.get("sub")
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

# 删除重复的验证端点，使用上面的统一验证逻辑

@router.post("/resend-verification", response_model=ResponseBase)
def resend_verification(
    request_data: EmailVerificationRequest,
    db: Session = Depends(get_db)
) -> Any:
    """重新发送验证邮件"""
    user_service = UserService(db)
    email_service = EmailService(db)
    
    user = user_service.get_by_email(request_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已验证，无需重复验证"
        )
    
    # 生成新的验证令牌（使用JWT格式保持一致性）
    from app.utils.security import create_access_token
    verification_token = create_access_token(
        data={"user_id": str(user.id), "type": "email_verification"},
        expires_delta=timedelta(hours=24)
    )
    user.verification_token = verification_token
    user.verification_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    
    # 发送验证邮件
    try:
        verification_url = f"{settings.BASE_URL}/verify-email?token={verification_token}"
        success = email_service.send_verification_email(user.email, verification_token, user.username)
        if not success:
            print(f"发送验证邮件失败: 邮件服务返回失败")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="发送验证邮件失败，请稍后重试"
            )
        else:
            print(f"验证邮件发送成功: {user.email}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"发送验证邮件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证邮件失败，请稍后重试"
        )
    
    return ResponseBase(
        message="验证邮件已重新发送，请查收",
        data={"email": user.email}
    )

@router.post("/forgot-password-new", response_model=ResponseBase)
def forgot_password_new(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> Any:
    """忘记密码 - 发送重置邮件"""
    user_service = UserService(db)
    email_service = EmailService(db)
    
    user = user_service.get_by_email(request_data.email)
    if not user:
        # 为了安全，不透露用户是否存在
        return ResponseBase(
            message="如果该邮箱已注册，重置链接已发送到您的邮箱",
            data={}
        )
    
    # 生成密码重置令牌（JWT格式）
    from app.utils.security import create_access_token
    reset_token = create_access_token(
        data={"user_id": str(user.id), "type": "password_reset"},
        expires_delta=timedelta(hours=1)
    )
    user.reset_token = reset_token
    user.reset_expires = datetime.utcnow() + timedelta(hours=1)  # 1小时有效期
    db.commit()
    
    # 发送重置邮件
    try:
        reset_url = f"{settings.BASE_URL}/reset-password?token={reset_token}"
        email_service.send_password_reset_email(user.email, user.username, reset_url)
    except Exception as e:
        print(f"发送重置邮件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送重置邮件失败，请稍后重试"
        )
    
    return ResponseBase(
        message="如果该邮箱已注册，重置链接已发送到您的邮箱",
        data={}
    )

@router.post("/reset-password-new", response_model=ResponseBase)
def reset_password_new(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
) -> Any:
    """重置密码"""
    from app.utils.security import verify_token
    
    # 验证JWT令牌
    payload = verify_token(reset_data.token)
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
    
    # 查找用户
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新密码
    from app.utils.security import get_password_hash
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    user.reset_expires = None
    db.commit()
    
    return ResponseBase(
        message="密码重置成功，请使用新密码登录",
        data={"user_id": user.id, "username": user.username}
    ) 