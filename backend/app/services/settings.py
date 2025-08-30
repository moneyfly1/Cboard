from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import json

from app.models.config import SystemConfig, Announcement, ThemeConfig
from app.schemas.config import (
    SystemConfigCreate, SystemConfigUpdate,
    AnnouncementCreate, AnnouncementUpdate,
    ThemeConfigCreate, ThemeConfigUpdate,
    SystemSettings, ConfigCategory
)

class SettingsService:
    def __init__(self, db: Session):
        self.db = db

    # ==================== 系统配置管理 ====================
    
    def get_config(self, key: str) -> Optional[SystemConfig]:
        """获取单个配置"""
        return self.db.query(SystemConfig).filter(SystemConfig.key == key).first()

    def get_configs_by_category(self, category: str) -> List[SystemConfig]:
        """根据分类获取配置"""
        return self.db.query(SystemConfig).filter(
            SystemConfig.category == category
        ).order_by(SystemConfig.sort_order, SystemConfig.id).all()

    def get_all_configs(self) -> List[SystemConfig]:
        """获取所有配置"""
        return self.db.query(SystemConfig).order_by(
            SystemConfig.category, SystemConfig.sort_order, SystemConfig.id
        ).all()

    def get_public_configs(self) -> List[SystemConfig]:
        """获取公开配置"""
        return self.db.query(SystemConfig).filter(
            SystemConfig.is_public == True
        ).order_by(SystemConfig.category, SystemConfig.sort_order).all()

    def create_config(self, config_in: SystemConfigCreate) -> SystemConfig:
        """创建配置"""
        config = SystemConfig(**config_in.dict())
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update_config(self, key: str, config_in: SystemConfigUpdate) -> Optional[SystemConfig]:
        """更新配置"""
        config = self.get_config(key)
        if not config:
            return None
        
        update_data = config_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
        
        self.db.commit()
        self.db.refresh(config)
        return config

    def delete_config(self, key: str) -> bool:
        """删除配置"""
        config = self.get_config(key)
        if not config:
            return False
        
        self.db.delete(config)
        self.db.commit()
        return True

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        config = self.get_config(key)
        if not config:
            return default
        
        if config.type == 'boolean':
            return config.value.lower() in ('true', '1', 'yes', 'on')
        elif config.type == 'number':
            try:
                return float(config.value) if '.' in config.value else int(config.value)
            except (ValueError, TypeError):
                return default
        elif config.type == 'json':
            try:
                return json.loads(config.value) if config.value else {}
            except (ValueError, TypeError):
                return default
        else:
            return config.value

    def set_config_value(self, key: str, value: Any, config_type: str = 'string') -> bool:
        """设置配置值"""
        config = self.get_config(key)
        if not config:
            return False
        
        if config_type == 'boolean':
            config.value = str(bool(value)).lower()
        elif config_type == 'number':
            config.value = str(value)
        elif config_type == 'json':
            config.value = json.dumps(value) if value else ''
        else:
            config.value = str(value)
        
        config.type = config_type
        self.db.commit()
        return True

    # ==================== 系统设置管理 ====================
    
    def get_system_settings(self) -> SystemSettings:
        """获取系统设置"""
        configs = self.get_all_configs()
        settings = {}
        
        for config in configs:
            settings[config.key] = self.get_config_value(config.key)
        
        return SystemSettings(**settings)

    def update_system_settings(self, settings: Dict[str, Any]) -> bool:
        """更新系统设置"""
        try:
            for key, value in settings.items():
                config = self.get_config(key)
                if config:
                    if config.type == 'boolean':
                        self.set_config_value(key, bool(value), 'boolean')
                    elif config.type == 'number':
                        self.set_config_value(key, value, 'number')
                    elif config.type == 'json':
                        self.set_config_value(key, value, 'json')
                    else:
                        self.set_config_value(key, value, 'string')
            return True
        except Exception:
            return False

    def initialize_default_configs(self):
        """初始化默认配置"""
        default_configs = [
            # 基本设置
            SystemConfigCreate(
                key="site_name",
                value="XBoard",
                type="string",
                category="general",
                display_name="网站名称",
                description="网站显示名称",
                is_public=True,
                sort_order=1
            ),
            SystemConfigCreate(
                key="site_description",
                value="高性能面板系统",
                type="text",
                category="general",
                display_name="网站描述",
                description="网站SEO描述",
                is_public=True,
                sort_order=2
            ),
            SystemConfigCreate(
                key="site_keywords",
                value="面板,管理,系统",
                type="text",
                category="general",
                display_name="网站关键词",
                description="网站SEO关键词",
                is_public=True,
                sort_order=3
            ),
            SystemConfigCreate(
                key="site_logo",
                value="",
                type="string",
                category="general",
                display_name="网站Logo",
                description="网站Logo图片URL",
                is_public=True,
                sort_order=4
            ),
            SystemConfigCreate(
                key="site_favicon",
                value="",
                type="string",
                category="general",
                display_name="网站图标",
                description="网站Favicon图标URL",
                is_public=True,
                sort_order=5
            ),
            
            # 注册设置
            SystemConfigCreate(
                key="allow_registration",
                value="true",
                type="boolean",
                category="registration",
                display_name="允许注册",
                description="是否允许新用户注册",
                is_public=True,
                sort_order=1
            ),
            SystemConfigCreate(
                key="require_email_verification",
                value="true",
                type="boolean",
                category="registration",
                display_name="邮箱验证",
                description="注册时是否需要邮箱验证",
                is_public=True,
                sort_order=2
            ),
            SystemConfigCreate(
                key="allow_qq_email_only",
                value="true",
                type="boolean",
                category="registration",
                display_name="仅允许QQ邮箱",
                description="是否只允许QQ邮箱注册",
                is_public=True,
                sort_order=3
            ),
            SystemConfigCreate(
                key="min_password_length",
                value="8",
                type="number",
                category="registration",
                display_name="最小密码长度",
                description="用户密码最小长度",
                is_public=True,
                sort_order=4
            ),
            
            # 邮件设置
            SystemConfigCreate(
                key="smtp_host",
                value="",
                type="string",
                category="email",
                display_name="SMTP服务器",
                description="邮件服务器地址",
                is_public=False,
                sort_order=1
            ),
            SystemConfigCreate(
                key="smtp_port",
                value="587",
                type="number",
                category="email",
                display_name="SMTP端口",
                description="邮件服务器端口",
                is_public=False,
                sort_order=2
            ),
            SystemConfigCreate(
                key="smtp_username",
                value="",
                type="string",
                category="email",
                display_name="SMTP用户名",
                description="邮件服务器用户名",
                is_public=False,
                sort_order=3
            ),
            SystemConfigCreate(
                key="smtp_password",
                value="",
                type="string",
                category="email",
                display_name="SMTP密码",
                description="邮件服务器密码",
                is_public=False,
                sort_order=4
            ),
            SystemConfigCreate(
                key="smtp_encryption",
                value="tls",
                type="string",
                category="email",
                display_name="加密方式",
                description="SMTP加密方式",
                is_public=False,
                sort_order=5
            ),
            SystemConfigCreate(
                key="from_email",
                value="",
                type="string",
                category="email",
                display_name="发件人邮箱",
                description="系统邮件发件人邮箱",
                is_public=False,
                sort_order=6
            ),
            SystemConfigCreate(
                key="from_name",
                value="XBoard",
                type="string",
                category="email",
                display_name="发件人名称",
                description="系统邮件发件人名称",
                is_public=False,
                sort_order=7
            ),
            
            # 通知设置
            SystemConfigCreate(
                key="enable_email_notification",
                value="true",
                type="boolean",
                category="notification",
                display_name="启用邮件通知",
                description="是否启用邮件通知功能",
                is_public=False,
                sort_order=1
            ),
            SystemConfigCreate(
                key="enable_sms_notification",
                value="false",
                type="boolean",
                category="notification",
                display_name="启用短信通知",
                description="是否启用短信通知功能",
                is_public=False,
                sort_order=2
            ),
            SystemConfigCreate(
                key="enable_webhook_notification",
                value="false",
                type="boolean",
                category="notification",
                display_name="启用Webhook通知",
                description="是否启用Webhook通知功能",
                is_public=False,
                sort_order=3
            ),
            SystemConfigCreate(
                key="webhook_url",
                value="",
                type="string",
                category="notification",
                display_name="Webhook地址",
                description="Webhook通知地址",
                is_public=False,
                sort_order=4
            ),
            
            # 主题设置
            SystemConfigCreate(
                key="default_theme",
                value="default",
                type="string",
                category="theme",
                display_name="默认主题",
                description="系统默认主题",
                is_public=True,
                sort_order=1
            ),
            SystemConfigCreate(
                key="allow_user_theme",
                value="true",
                type="boolean",
                category="theme",
                display_name="允许用户选择主题",
                description="是否允许用户自定义主题",
                is_public=True,
                sort_order=2
            ),
            SystemConfigCreate(
                key="available_themes",
                value='["default", "dark", "blue", "green"]',
                type="json",
                category="theme",
                display_name="可用主题",
                description="系统可用的主题列表",
                is_public=True,
                sort_order=3
            ),
            
            # 支付设置
            SystemConfigCreate(
                key="enable_payment",
                value="true",
                type="boolean",
                category="payment",
                display_name="启用支付",
                description="是否启用支付功能",
                is_public=False,
                sort_order=1
            ),
            SystemConfigCreate(
                key="default_payment_method",
                value="",
                type="string",
                category="payment",
                display_name="默认支付方式",
                description="系统默认支付方式",
                is_public=False,
                sort_order=2
            ),
            SystemConfigCreate(
                key="payment_currency",
                value="CNY",
                type="string",
                category="payment",
                display_name="支付货币",
                description="系统默认支付货币",
                is_public=False,
                sort_order=3
            ),
            
            # 公告设置
            SystemConfigCreate(
                key="enable_announcement",
                value="true",
                type="boolean",
                category="announcement",
                display_name="启用公告",
                description="是否启用公告功能",
                is_public=False,
                sort_order=1
            ),
            SystemConfigCreate(
                key="announcement_position",
                value="top",
                type="string",
                category="announcement",
                display_name="公告位置",
                description="公告显示位置",
                is_public=False,
                sort_order=2
            ),
            SystemConfigCreate(
                key="max_announcements",
                value="5",
                type="number",
                category="announcement",
                display_name="最大公告数",
                description="同时显示的最大公告数量",
                is_public=False,
                sort_order=3
            ),
            
            # 安全设置
            SystemConfigCreate(
                key="enable_captcha",
                value="false",
                type="boolean",
                category="security",
                display_name="启用验证码",
                description="是否启用验证码功能",
                is_public=False,
                sort_order=1
            ),
            SystemConfigCreate(
                key="max_login_attempts",
                value="5",
                type="number",
                category="security",
                display_name="最大登录尝试",
                description="最大登录失败次数",
                is_public=False,
                sort_order=2
            ),
            SystemConfigCreate(
                key="lockout_duration",
                value="30",
                type="number",
                category="security",
                display_name="锁定时间",
                description="登录失败后锁定时间（分钟）",
                is_public=False,
                sort_order=3
            ),
            SystemConfigCreate(
                key="session_timeout",
                value="1440",
                type="number",
                category="security",
                display_name="会话超时",
                description="用户会话超时时间（分钟）",
                is_public=False,
                sort_order=4
            ),
            
            # 性能设置
            SystemConfigCreate(
                key="enable_cache",
                value="true",
                type="boolean",
                category="performance",
                display_name="启用缓存",
                description="是否启用系统缓存",
                is_public=False,
                sort_order=1
            ),
            SystemConfigCreate(
                key="cache_duration",
                value="3600",
                type="number",
                category="performance",
                display_name="缓存时间",
                description="缓存持续时间（秒）",
                is_public=False,
                sort_order=2
            ),
            SystemConfigCreate(
                key="enable_compression",
                value="true",
                type="boolean",
                category="performance",
                display_name="启用压缩",
                description="是否启用响应压缩",
                is_public=False,
                sort_order=3
            ),
            SystemConfigCreate(
                key="max_upload_size",
                value="10",
                type="number",
                category="performance",
                display_name="最大上传大小",
                description="文件上传最大大小（MB）",
                is_public=False,
                sort_order=4
            )
        ]
        
        for config_data in default_configs:
            existing = self.get_config(config_data.key)
            if not existing:
                self.create_config(config_data)

    # ==================== 公告管理 ====================
    
    def get_announcement(self, announcement_id: int) -> Optional[Announcement]:
        """获取单个公告"""
        return self.db.query(Announcement).filter(Announcement.id == announcement_id).first()

    def get_active_announcements(self, target_users: str = 'all') -> List[Announcement]:
        """获取活跃公告"""
        now = datetime.now()
        return self.db.query(Announcement).filter(
            and_(
                Announcement.is_active == True,
                or_(
                    Announcement.start_time == None,
                    Announcement.start_time <= now
                ),
                or_(
                    Announcement.end_time == None,
                    Announcement.end_time >= now
                ),
                or_(
                    Announcement.target_users == 'all',
                    Announcement.target_users == target_users
                )
            )
        ).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).all()

    def get_all_announcements(self, page: int = 1, size: int = 20) -> tuple:
        """获取所有公告"""
        skip = (page - 1) * size
        announcements = self.db.query(Announcement).order_by(
            Announcement.is_pinned.desc(), Announcement.created_at.desc()
        ).offset(skip).limit(size).all()
        total = self.db.query(Announcement).count()
        return announcements, total

    def create_announcement(self, announcement_in: AnnouncementCreate, created_by: int) -> Announcement:
        """创建公告"""
        announcement = Announcement(**announcement_in.dict(), created_by=created_by)
        self.db.add(announcement)
        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def update_announcement(self, announcement_id: int, announcement_in: AnnouncementUpdate) -> Optional[Announcement]:
        """更新公告"""
        announcement = self.get_announcement(announcement_id)
        if not announcement:
            return None
        
        update_data = announcement_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(announcement, field, value)
        
        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def delete_announcement(self, announcement_id: int) -> bool:
        """删除公告"""
        announcement = self.get_announcement(announcement_id)
        if not announcement:
            return False
        
        self.db.delete(announcement)
        self.db.commit()
        return True

    def toggle_announcement_status(self, announcement_id: int) -> bool:
        """切换公告状态"""
        announcement = self.get_announcement(announcement_id)
        if not announcement:
            return False
        
        announcement.is_active = not announcement.is_active
        self.db.commit()
        return True

    def toggle_announcement_pin(self, announcement_id: int) -> bool:
        """切换公告置顶状态"""
        announcement = self.get_announcement(announcement_id)
        if not announcement:
            return False
        
        announcement.is_pinned = not announcement.is_pinned
        self.db.commit()
        return True

    # ==================== 主题配置管理 ====================
    
    def get_theme_config(self, theme_id: int) -> Optional[ThemeConfig]:
        """获取主题配置"""
        return self.db.query(ThemeConfig).filter(ThemeConfig.id == theme_id).first()

    def get_theme_config_by_name(self, name: str) -> Optional[ThemeConfig]:
        """根据名称获取主题配置"""
        return self.db.query(ThemeConfig).filter(ThemeConfig.name == name).first()

    def get_active_themes(self) -> List[ThemeConfig]:
        """获取活跃主题"""
        return self.db.query(ThemeConfig).filter(
            ThemeConfig.is_active == True
        ).order_by(ThemeConfig.is_default.desc(), ThemeConfig.id).all()

    def get_default_theme(self) -> Optional[ThemeConfig]:
        """获取默认主题"""
        return self.db.query(ThemeConfig).filter(
            ThemeConfig.is_active == True,
            ThemeConfig.is_default == True
        ).first()

    def create_theme_config(self, theme_in: ThemeConfigCreate) -> ThemeConfig:
        """创建主题配置"""
        # 如果设置为默认，先取消其他默认主题
        if theme_in.is_default:
            self.db.query(ThemeConfig).update({"is_default": False})
        
        theme = ThemeConfig(**theme_in.dict())
        self.db.add(theme)
        self.db.commit()
        self.db.refresh(theme)
        return theme

    def update_theme_config(self, theme_id: int, theme_in: ThemeConfigUpdate) -> Optional[ThemeConfig]:
        """更新主题配置"""
        theme = self.get_theme_config(theme_id)
        if not theme:
            return None
        
        # 如果设置为默认，先取消其他默认主题
        if theme_in.is_default:
            self.db.query(ThemeConfig).update({"is_default": False})
        
        update_data = theme_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(theme, field, value)
        
        self.db.commit()
        self.db.refresh(theme)
        return theme

    def delete_theme_config(self, theme_id: int) -> bool:
        """删除主题配置"""
        theme = self.get_theme_config(theme_id)
        if not theme:
            return False
        
        self.db.delete(theme)
        self.db.commit()
        return True 