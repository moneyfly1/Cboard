from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, validator

# 系统配置模式
class SystemConfigBase(BaseModel):
    key: str
    value: Optional[str] = None
    type: str
    category: str
    display_name: str
    description: Optional[str] = None
    is_public: bool = False
    sort_order: int = 0

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfigUpdate(BaseModel):
    value: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    sort_order: Optional[int] = None

class SystemConfigInDB(SystemConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 公告模式
class AnnouncementBase(BaseModel):
    title: str
    content: str
    type: str = 'info'
    is_active: bool = True
    is_pinned: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    target_users: str = 'all'

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    is_pinned: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    target_users: Optional[str] = None

class AnnouncementInDB(AnnouncementBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 主题配置模式
class ThemeConfigBase(BaseModel):
    name: str
    display_name: str
    is_active: bool = False
    is_default: bool = False
    config: Optional[Dict[str, Any]] = None
    preview_image: Optional[str] = None

class ThemeConfigCreate(ThemeConfigBase):
    pass

class ThemeConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    preview_image: Optional[str] = None

class ThemeConfigInDB(ThemeConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 配置分类模式
class ConfigCategory(BaseModel):
    category: str
    display_name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    configs: List[SystemConfigInDB] = []

# 系统设置模式
class SystemSettings(BaseModel):
    # 基本设置
    site_name: str = "XBoard"
    site_description: str = "高性能面板系统"
    site_keywords: str = "面板,管理,系统"
    site_logo: Optional[str] = None
    site_favicon: Optional[str] = None
    
    # 注册设置
    allow_registration: bool = True
    require_email_verification: bool = True
    allow_qq_email_only: bool = True
    min_password_length: int = 8
    
    # 邮件设置
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_encryption: str = "tls"
    from_email: str = ""
    from_name: str = ""
    
    # 通知设置
    enable_email_notification: bool = True
    enable_sms_notification: bool = False
    enable_webhook_notification: bool = False
    webhook_url: Optional[str] = None
    
    # 主题设置
    default_theme: str = "default"
    allow_user_theme: bool = True
    available_themes: List[str] = ["default", "dark", "blue", "green"]
    
    # 支付设置
    enable_payment: bool = True
    default_payment_method: Optional[str] = None
    payment_currency: str = "CNY"
    
    # 公告设置
    enable_announcement: bool = True
    announcement_position: str = "top"  # top, sidebar, popup
    max_announcements: int = 5
    
    # 安全设置
    enable_captcha: bool = False
    max_login_attempts: int = 5
    lockout_duration: int = 30  # 分钟
    session_timeout: int = 1440  # 分钟
    
    # 性能设置
    enable_cache: bool = True
    cache_duration: int = 3600  # 秒
    enable_compression: bool = True
    max_upload_size: int = 10  # MB

# 配置更新模式
class ConfigUpdateRequest(BaseModel):
    category: str
    configs: Dict[str, Any]

# 配置初始化模式
class ConfigInitRequest(BaseModel):
    configs: List[SystemConfigCreate] 