from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# 密码加密上下文 - 增强安全性配置
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12,  # 增加计算成本，提高安全性
    bcrypt__min_rounds=10,  # 最小轮数
    bcrypt__max_rounds=15   # 最大轮数
)

# HTTP Bearer 认证
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """验证密码强度"""
    if len(password) < 8:
        return False, "密码长度至少8位"
    
    if len(password) < 12:
        return False, "建议密码长度至少12位以提高安全性"
    
    # 检查是否包含大写字母
    if not any(c.isupper() for c in password):
        return False, "密码必须包含至少一个大写字母"
    
    # 检查是否包含小写字母
    if not any(c.islower() for c in password):
        return False, "密码必须包含至少一个小写字母"
    
    # 检查是否包含数字
    if not any(c.isdigit() for c in password):
        return False, "密码必须包含至少一个数字"
    
    # 检查是否包含特殊字符
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "密码必须包含至少一个特殊字符 (!@#$%^&*()_+-=[]{}|;:,.<>?)"
    
    # 检查常见弱密码
    weak_passwords = [
        "password", "123456", "123456789", "qwerty", "abc123",
        "password123", "admin", "root", "user", "test"
    ]
    if password.lower() in weak_passwords:
        return False, "密码过于简单，请使用更复杂的密码"
    
    return True, "密码强度符合要求"

def is_password_strong_enough(password: str) -> bool:
    """检查密码是否足够强"""
    is_valid, _ = validate_password_strength(password)
    return is_valid

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """验证令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload is None:
            raise credentials_exception
        
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # 检查令牌类型
        token_type = payload.get("type")
        if token_type == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌不能用于访问"
            )
        
    except JWTError:
        raise credentials_exception
    
    # 从数据库获取用户
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
    except (ValueError, TypeError):
        raise credentials_exception
    if user is None:
        raise credentials_exception
    
    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已停用"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已停用"
        )
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user

async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前已验证用户"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先验证邮箱"
        )
    return current_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """验证用户"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_user_tokens(user: User) -> dict:
    """创建用户令牌"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "is_admin": user.is_admin},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

def refresh_access_token(refresh_token: str) -> Optional[str]:
    """刷新访问令牌"""
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        
        if token_type != "refresh":
            return None
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id, "email": payload.get("email"), "is_admin": payload.get("is_admin")},
            expires_delta=access_token_expires
        )
        
        return access_token
        
    except JWTError:
        return None

def get_user_from_token(token: str, db: Session) -> Optional[User]:
    """从令牌获取用户"""
    try:
        payload = verify_token(token)
        if payload is None:
            return None
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
        
    except Exception:
        return None

def check_permission(user: User, required_permission: str) -> bool:
    """检查用户权限"""
    if user.is_admin:
        return True
    
    # 这里可以添加更细粒度的权限检查
    # 例如：角色权限、功能权限等
    
    return False

def require_permission(permission: str):
    """权限装饰器"""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要 {permission} 权限"
            )
        return current_user
    
    return permission_checker

# 常用权限检查器
require_admin = get_current_admin_user
require_verified = get_current_verified_user
require_auth = get_current_user

# 可选认证（不强制要求认证）
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取可选用户（不强制要求认证）"""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None

# 令牌黑名单管理（用于登出）
class TokenBlacklist:
    def __init__(self):
        self.blacklisted_tokens = set()
    
    def add_token(self, token: str):
        """添加令牌到黑名单"""
        self.blacklisted_tokens.add(token)
    
    def is_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单中"""
        return token in self.blacklisted_tokens
    
    def remove_token(self, token: str):
        """从黑名单移除令牌"""
        self.blacklisted_tokens.discard(token)

# 全局令牌黑名单实例
token_blacklist = TokenBlacklist()

def blacklist_token(token: str):
    """将令牌加入黑名单"""
    token_blacklist.add_token(token)

def is_token_blacklisted(token: str) -> bool:
    """检查令牌是否在黑名单中"""
    return token_blacklist.is_blacklisted(token)

# 更新get_current_user以检查黑名单
async def get_current_user_with_blacklist(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户（包含黑名单检查）"""
    token = credentials.credentials
    
    # 检查令牌是否在黑名单中
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已失效，请重新登录"
        )
    
    return await get_current_user(credentials, db)

# 用户会话管理
class UserSession:
    def __init__(self):
        self.active_sessions = {}  # user_id -> session_info
    
    def create_session(self, user_id: int, token: str, ip_address: str = None):
        """创建用户会话"""
        session_info = {
            "token": token,
            "ip_address": ip_address,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        self.active_sessions[user_id] = session_info
    
    def update_activity(self, user_id: int):
        """更新用户活动时间"""
        if user_id in self.active_sessions:
            self.active_sessions[user_id]["last_activity"] = datetime.utcnow()
    
    def remove_session(self, user_id: int):
        """移除用户会话"""
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
    
    def get_session(self, user_id: int):
        """获取用户会话信息"""
        return self.active_sessions.get(user_id)
    
    def cleanup_expired_sessions(self, max_idle_minutes: int = 30):
        """清理过期会话"""
        now = datetime.utcnow()
        expired_users = []
        
        for user_id, session_info in self.active_sessions.items():
            idle_time = now - session_info["last_activity"]
            if idle_time.total_seconds() > max_idle_minutes * 60:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            self.remove_session(user_id)

# 全局用户会话管理器
user_sessions = UserSession()

def create_user_session(user_id: int, token: str, ip_address: str = None):
    """创建用户会话"""
    user_sessions.create_session(user_id, token, ip_address)

def update_user_activity(user_id: int):
    """更新用户活动"""
    user_sessions.update_activity(user_id)

def remove_user_session(user_id: int):
    """移除用户会话"""
    user_sessions.remove_session(user_id)
    # 同时将令牌加入黑名单
    session_info = user_sessions.get_session(user_id)
    if session_info:
        blacklist_token(session_info["token"])
