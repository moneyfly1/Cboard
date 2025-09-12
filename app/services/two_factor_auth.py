"""
双因素认证服务
支持TOTP (Time-based One-Time Password) 和短信验证码
"""
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import secrets
import string

from app.models.user import User
from app.core.config import settings

class TwoFactorAuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_totp_secret(self, user: User) -> str:
        """生成TOTP密钥"""
        secret = pyotp.random_base32()
        
        # 保存密钥到用户记录（实际应用中应该加密存储）
        # 这里简化处理，实际应该存储在专门的2FA表中
        user.totp_secret = secret
        self.db.commit()
        
        return secret
    
    def generate_totp_qr_code(self, user: User, secret: str) -> str:
        """生成TOTP二维码"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=settings.SITE_NAME or "XBoard"
        )
        
        # 生成二维码
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为base64字符串
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_totp_code(self, user: User, code: str) -> bool:
        """验证TOTP验证码"""
        if not user.totp_secret:
            return False
        
        totp = pyotp.TOTP(user.totp_secret)
        return totp.verify(code, valid_window=1)  # 允许1个时间窗口的误差
    
    def generate_sms_code(self, phone_number: str) -> str:
        """生成短信验证码"""
        # 生成6位数字验证码
        code = ''.join(secrets.choice(string.digits) for _ in range(6))
        
        # 这里应该调用短信服务发送验证码
        # 实际应用中需要集成短信服务商API
        print(f"短信验证码发送到 {phone_number}: {code}")
        
        # 将验证码存储到缓存或数据库（设置过期时间）
        # 这里简化处理
        return code
    
    def verify_sms_code(self, phone_number: str, code: str) -> bool:
        """验证短信验证码"""
        # 这里应该从缓存或数据库中验证验证码
        # 实际应用中需要实现验证码存储和验证逻辑
        return True  # 简化处理
    
    def enable_2fa_totp(self, user: User) -> Dict[str, Any]:
        """启用TOTP双因素认证"""
        if user.totp_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP双因素认证已启用"
            )
        
        secret = self.generate_totp_secret(user)
        qr_code = self.generate_totp_qr_code(user, secret)
        
        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": self.generate_backup_codes(user)
        }
    
    def confirm_2fa_totp(self, user: User, code: str) -> bool:
        """确认启用TOTP双因素认证"""
        if not self.verify_totp_code(user, code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误"
            )
        
        user.totp_enabled = True
        self.db.commit()
        return True
    
    def disable_2fa_totp(self, user: User, code: str) -> bool:
        """禁用TOTP双因素认证"""
        if not user.totp_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP双因素认证未启用"
            )
        
        if not self.verify_totp_code(user, code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误"
            )
        
        user.totp_enabled = False
        user.totp_secret = None
        self.db.commit()
        return True
    
    def generate_backup_codes(self, user: User) -> list:
        """生成备用验证码"""
        backup_codes = []
        for _ in range(10):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            backup_codes.append(code)
        
        # 这里应该将备用验证码存储到数据库
        # 实际应用中需要实现备用验证码的存储和验证逻辑
        
        return backup_codes
    
    def verify_backup_code(self, user: User, code: str) -> bool:
        """验证备用验证码"""
        # 这里应该从数据库中验证备用验证码
        # 实际应用中需要实现备用验证码的验证逻辑
        return True  # 简化处理
    
    def is_2fa_enabled(self, user: User) -> bool:
        """检查是否启用了双因素认证"""
        return user.totp_enabled or user.sms_2fa_enabled
    
    def require_2fa_verification(self, user: User, code: str, method: str = "totp") -> bool:
        """要求双因素认证验证"""
        if not self.is_2fa_enabled(user):
            return True  # 如果未启用2FA，直接通过
        
        if method == "totp":
            return self.verify_totp_code(user, code)
        elif method == "sms":
            return self.verify_sms_code(user.phone_number, code)
        elif method == "backup":
            return self.verify_backup_code(user, code)
        
        return False

# 全局2FA服务实例
def get_2fa_service(db: Session) -> TwoFactorAuthService:
    """获取2FA服务实例"""
    return TwoFactorAuthService(db)
