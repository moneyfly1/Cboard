 #!/usr/bin/env python3
"""
全面修复XBoard Modern项目的所有导入和依赖问题
"""

import os
import sys
import re
from pathlib import Path

def fix_import_issues():
    """修复所有导入问题"""
    
    base_path = Path(__file__).parent
    backend_path = base_path / "backend"
    
    print("🔧 开始全面修复XBoard Modern项目...")
    
    # 1. 修复app.schemas.email导入问题
    print("📧 修复email schemas...")
    email_schemas_path = backend_path / "app" / "schemas" / "email.py"
    if not email_schemas_path.exists():
        with open(email_schemas_path, 'w', encoding='utf-8') as f:
            f.write('''from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class EmailQueueBase(BaseModel):
    to_email: str
    subject: str
    content: str
    content_type: str = "plain"  # plain, html
    email_type: Optional[str] = None  # verification, reset, subscription, etc.
    attachments: Optional[List[Dict[str, Any]]] = None

class EmailQueueCreate(EmailQueueBase):
    pass

class EmailQueueUpdate(BaseModel):
    to_email: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    content_type: Optional[str] = None
    email_type: Optional[str] = None
    status: Optional[str] = None
    retry_count: Optional[int] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None

class EmailQueueInDB(EmailQueueBase):
    id: int
    status: str
    retry_count: int
    max_retries: int
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EmailQueue(EmailQueueInDB):
    pass
''')
    
    # 2. 更新schemas/__init__.py
    print("📝 更新schemas/__init__.py...")
    schemas_init_path = backend_path / "app" / "schemas" / "__init__.py"
    if schemas_init_path.exists():
        content = schemas_init_path.read_text(encoding='utf-8')
        
        # 添加email导入
        if "from .email import" not in content:
            # 在notification导入后添加email导入
            content = re.sub(
                r'(from \.notification import.*?\n)',
                r'\1from .email import (\n    EmailQueue, EmailQueueCreate, EmailQueueUpdate, EmailQueueInDB, EmailQueueBase\n)\n',
                content,
                flags=re.DOTALL
            )
        
        # 添加email到__all__
        if '"EmailQueue"' not in content:
            content = re.sub(
                r'(# Notification schemas.*?\n.*?\n)',
                r'\1    # Email schemas\n    "EmailQueue", "EmailQueueCreate", "EmailQueueUpdate", "EmailQueueInDB", "EmailQueueBase",\n',
                content,
                flags=re.DOTALL
            )
        
        schemas_init_path.write_text(content, encoding='utf-8')
    
    # 3. 更新EmailQueue模型
    print("📊 更新EmailQueue模型...")
    email_model_path = backend_path / "app" / "models" / "email.py"
    if email_model_path.exists():
        content = email_model_path.read_text(encoding='utf-8')
        
        # 添加缺失的字段
        if "content_type = Column" not in content:
            content = re.sub(
                r'(content = Column\(Text, nullable=False\)\n)',
                r'\1    content_type = Column(String(20), default="plain")  # plain, html\n    email_type = Column(String(50), nullable=True)  # verification, reset, subscription, etc.\n    attachments = Column(Text, nullable=True)  # JSON string for attachments\n',
                content
            )
        
        email_model_path.write_text(content, encoding='utf-8')
    
    # 4. 修复security.py中的认证函数
    print("🔐 修复security.py认证函数...")
    security_path = backend_path / "app" / "utils" / "security.py"
    if security_path.exists():
        content = security_path.read_text(encoding='utf-8')
        
        # 添加必要的导入
        if "from fastapi import Depends, HTTPException, status" not in content:
            imports_to_add = '''from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
'''
            content = imports_to_add + content
        
        # 添加oauth2_scheme
        if "oauth2_scheme = OAuth2PasswordBearer" not in content:
            content = re.sub(
                r'(pwd_context = CryptContext\(schemes=\["bcrypt"\], deprecated="auto"\)\n)',
                r'\1\n# OAuth2 密码承载者\noauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")\n',
                content
            )
        
        # 添加get_current_user函数
        if "def get_current_user" not in content:
            current_user_func = '''

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
'''
            content += current_user_func
        
        security_path.write_text(content, encoding='utf-8')
    
    # 5. 修复auth.py中的Token导入
    print("🎫 修复auth.py中的Token导入...")
    auth_path = backend_path / "app" / "api" / "api_v1" / "endpoints" / "auth.py"
    if auth_path.exists():
        content = auth_path.read_text(encoding='utf-8')
        
        # 修复Token导入
        if "from app.schemas.user import.*Token" in content:
            content = re.sub(
                r'from app\.schemas\.user import UserLogin, UserCreate, User, Token',
                'from app.schemas.user import UserLogin, UserCreate, User',
                content
            )
            content = re.sub(
                r'from app\.schemas\.common import ResponseBase',
                'from app.schemas.common import ResponseBase, Token',
                content
            )
        
        auth_path.write_text(content, encoding='utf-8')
    
    # 6. 修复subscriptions.py中的email导入
    print("📧 修复subscriptions.py中的email导入...")
    subscriptions_path = backend_path / "app" / "api" / "api_v1" / "endpoints" / "subscriptions.py"
    if subscriptions_path.exists():
        content = subscriptions_path.read_text(encoding='utf-8')
        
        # 修复email导入
        if "from app.utils.email import send_subscription_email" in content:
            content = re.sub(
                r'from app\.utils\.email import send_subscription_email',
                'from app.services.email import EmailService',
                content
            )
        
        # 修复函数调用
        if "send_subscription_email(" in content:
            content = re.sub(
                r'send_subscription_email\([\s\S]*?\)',
                '''email_service = EmailService(db)
        subscription_data = {
            'id': subscription.id,
            'package_name': subscription.package.name if subscription.package else '未知套餐',
            'expires_at': subscription.expire_time.strftime('%Y-%m-%d %H:%M:%S') if subscription.expire_time else '未知',
            'status': subscription.status,
            'ssr_url': ssr_url,
            'clash_url': clash_url
        }
        success = email_service.send_subscription_email(current_user.email, subscription_data)
        if success:
            return ResponseBase(message="订阅邮件发送成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="邮件发送失败"
            )''',
                content
            )
        
        subscriptions_path.write_text(content, encoding='utf-8')
    
    # 7. 修复admin.py中的email导入
    print("👨‍💼 修复admin.py中的email导入...")
    admin_path = backend_path / "app" / "api" / "api_v1" / "endpoints" / "admin.py"
    if admin_path.exists():
        content = admin_path.read_text(encoding='utf-8')
        
        # 修复所有email导入
        content = re.sub(
            r'from app\.utils\.email import send_subscription_email',
            'from app.services.email import EmailService',
            content
        )
        
        # 修复函数调用
        content = re.sub(
            r'send_subscription_email\(user\.email, user\.username\)',
            '''email_service = EmailService(db)
        subscription_data = {
            'id': subscription.id if subscription else 0,
            'package_name': subscription.package.name if subscription and subscription.package else '未知套餐',
            'expires_at': subscription.expire_time.strftime('%Y-%m-%d %H:%M:%S') if subscription and subscription.expire_time else '未知',
            'status': subscription.status if subscription else '未知'
        }
        success = email_service.send_subscription_email(user.email, subscription_data)''',
            content
        )
        
        admin_path.write_text(content, encoding='utf-8')
    
    # 8. 确保所有__init__.py文件存在
    print("📁 确保__init__.py文件存在...")
    init_dirs = [
        backend_path / "app",
        backend_path / "app" / "api",
        backend_path / "app" / "api" / "api_v1",
        backend_path / "app" / "api" / "api_v1" / "endpoints",
        backend_path / "app" / "core",
        backend_path / "app" / "models",
        backend_path / "app" / "schemas",
        backend_path / "app" / "services",
        backend_path / "app" / "utils",
    ]
    
    for init_dir in init_dirs:
        init_file = init_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Auto-generated __init__.py\n", encoding='utf-8')
    
    # 9. 更新models/__init__.py
    print("📊 更新models/__init__.py...")
    models_init_path = backend_path / "app" / "models" / "__init__.py"
    if models_init_path.exists():
        content = models_init_path.read_text(encoding='utf-8')
        
        # 确保EmailQueue被导入
        if "from .email import EmailQueue" not in content:
            content = re.sub(
                r'(from \.notification import.*?\n)',
                r'\1from .email import EmailQueue\n',
                content,
                flags=re.DOTALL
            )
        
        # 确保EmailQueue在__all__中
        if '"EmailQueue"' not in content:
            content = re.sub(
                r'(\]\s*$)',
                r', "EmailQueue"\1',
                content
            )
        
        models_init_path.write_text(content, encoding='utf-8')
    
    print("✅ 全面修复完成！")

if __name__ == "__main__":
    fix_import_issues()