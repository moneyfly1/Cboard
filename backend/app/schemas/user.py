from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
import re

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    username: Optional[str] = None  # 可选，会自动从QQ邮箱提取
    
    @validator('email')
    def validate_qq_email(cls, v):
        """验证是否为QQ邮箱"""
        qq_pattern = r'^\d+@qq\.com$'
        if not re.match(qq_pattern, v):
            raise ValueError('只允许使用QQ邮箱注册')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 6:
            raise ValueError('密码长度不能少于6位')
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_admin: Optional[bool] = None
    avatar: Optional[str] = None

class UserInDB(UserBase):
    id: int
    username: str
    is_active: bool
    is_verified: bool
    is_admin: bool
    avatar: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDB):
    pass

class UserLogin(BaseModel):
    username: str  # 可以是QQ号码或QQ邮箱
    password: str

class UserPasswordChange(BaseModel):
    old_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码强度"""
        if len(v) < 6:
            raise ValueError('密码长度不能少于6位')
        return v

class UserPasswordReset(BaseModel):
    email: EmailStr
    
    @validator('email')
    def validate_qq_email(cls, v):
        """验证是否为QQ邮箱"""
        qq_pattern = r'^\d+@qq\.com$'
        if not re.match(qq_pattern, v):
            raise ValueError('请输入正确的QQ邮箱地址')
        return v

class UserPasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码强度"""
        if len(v) < 6:
            raise ValueError('密码长度不能少于6位')
        return v 