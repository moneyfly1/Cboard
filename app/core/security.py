"""
安全配置和工具
"""
import secrets
import hashlib
import hmac
import time
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from app.core.config import settings


class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def generate_csrf_token(self) -> str:
        """生成CSRF令牌"""
        return secrets.token_urlsafe(32)
    
    def verify_csrf_token(self, token: str, session_token: str) -> bool:
        """验证CSRF令牌"""
        return hmac.compare_digest(token, session_token)
    
    def generate_api_key(self) -> str:
        """生成API密钥"""
        return f"xboard_{secrets.token_urlsafe(32)}"
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            self.secret_key.encode('utf-8'),
            100000
        ).hex()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        return hmac.compare_digest(
            self.hash_password(password),
            hashed
        )
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != token_type:
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def is_secure_request(self, request: Request) -> bool:
        """检查请求是否安全"""
        # 检查HTTPS
        if not request.url.scheme == "https" and not settings.DEBUG:
            return False
        
        # 检查必要的安全头
        required_headers = [
            "User-Agent",
            "Accept"
        ]
        
        for header in required_headers:
            if not request.headers.get(header):
                return False
        
        return True
    
    def sanitize_input(self, input_str: str) -> str:
        """清理用户输入"""
        if not input_str:
            return ""
        
        # 移除潜在的恶意字符
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`', '$']
        for char in dangerous_chars:
            input_str = input_str.replace(char, '')
        
        return input_str.strip()
    
    def validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """验证密码强度"""
        result = {
            "valid": True,
            "score": 0,
            "issues": []
        }
        
        if len(password) < 8:
            result["valid"] = False
            result["issues"].append("密码长度至少8位")
        
        if not any(c.isupper() for c in password):
            result["score"] += 1
            result["issues"].append("建议包含大写字母")
        
        if not any(c.islower() for c in password):
            result["score"] += 1
            result["issues"].append("建议包含小写字母")
        
        if not any(c.isdigit() for c in password):
            result["score"] += 1
            result["issues"].append("建议包含数字")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            result["score"] += 1
            result["issues"].append("建议包含特殊字符")
        
        # 检查常见弱密码
        weak_passwords = [
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin", "root", "user", "test"
        ]
        
        if password.lower() in weak_passwords:
            result["valid"] = False
            result["issues"].append("密码过于简单")
        
        return result


class SecurityHeaders:
    """安全头管理"""
    
    @staticmethod
    def add_security_headers(response):
        """添加安全头"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


class RateLimitTracker:
    """速率限制跟踪器"""
    
    def __init__(self):
        self.attempts = {}
        self.lockout_duration = 300  # 5分钟锁定
        self.max_attempts = 5
    
    def record_failed_attempt(self, identifier: str) -> bool:
        """记录失败尝试"""
        current_time = time.time()
        
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        # 清理过期记录
        self.attempts[identifier] = [
            attempt_time for attempt_time in self.attempts[identifier]
            if current_time - attempt_time < self.lockout_duration
        ]
        
        # 添加当前尝试
        self.attempts[identifier].append(current_time)
        
        # 检查是否超过限制
        return len(self.attempts[identifier]) >= self.max_attempts
    
    def is_locked_out(self, identifier: str) -> bool:
        """检查是否被锁定"""
        current_time = time.time()
        
        if identifier not in self.attempts:
            return False
        
        # 清理过期记录
        self.attempts[identifier] = [
            attempt_time for attempt_time in self.attempts[identifier]
            if current_time - attempt_time < self.lockout_duration
        ]
        
        return len(self.attempts[identifier]) >= self.max_attempts
    
    def clear_attempts(self, identifier: str):
        """清除尝试记录"""
        if identifier in self.attempts:
            del self.attempts[identifier]


# 全局实例
security_manager = SecurityManager()
rate_limit_tracker = RateLimitTracker()


async def security_middleware(request: Request, call_next):
    """安全中间件"""
    # 检查请求安全性
    if not security_manager.is_secure_request(request):
        # 在非调试模式下，拒绝不安全的请求
        if not settings.DEBUG:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不安全的请求"
            )
    
    # 处理请求
    response = await call_next(request)
    
    # 添加安全头
    response = SecurityHeaders.add_security_headers(response)
    
    return response
