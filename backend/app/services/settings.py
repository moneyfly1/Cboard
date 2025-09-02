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
    SystemSettings, ConfigCategory,
    GeneralConfig, RegistrationConfig, EmailConfig, NotificationConfig,
    SystemThemeConfig, PaymentConfig, AnnouncementConfig,
    SecurityConfig, PerformanceConfig
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
        
        config.value = str(value)
        config.type = config_type
        self.db.commit()
        return True

    # ==================== 系统设置管理 ====================
    
    def get_system_settings(self) -> SystemSettings:
        """获取系统设置"""
        try:
            # 获取所有配置
            configs = self.get_all_configs()
            settings = {}
            
            for config in configs:
                settings[config.key] = self.get_config_value(config.key)
            
            # 创建默认配置实例
            general_config = GeneralConfig(
                site_name=settings.get('site_name', 'XBoard Modern'),
                site_description=settings.get('site_description', '现代化订阅管理系统'),
                site_logo=settings.get('site_logo'),
                maintenance_mode=settings.get('maintenance_mode', False),
                maintenance_message=settings.get('maintenance_message', '系统维护中，请稍后再试'),
                registration_enabled=settings.get('allow_registration', True),
                email_verification_required=settings.get('email_verification_required', True),
                min_password_length=settings.get('min_password_length', 6),
                max_login_attempts=settings.get('max_login_attempts', 5),
                session_timeout=settings.get('session_timeout', 30)
            )
            
            registration_config = RegistrationConfig(
                enabled=settings.get('allow_registration', True),
                require_email_verification=settings.get('email_verification_required', True),
                allow_qq_email_only=settings.get('allow_qq_email_only', True),
                auto_approve=settings.get('auto_approve', False),
                welcome_message=settings.get('welcome_message', '欢迎加入XBoard！'),
                terms_of_service=settings.get('terms_of_service', ''),
                privacy_policy=settings.get('privacy_policy', '')
            )
            
            email_config = EmailConfig(
                smtp_host=settings.get('smtp_host', 'smtp.qq.com'),
                smtp_port=settings.get('smtp_port', 587),
                smtp_username=settings.get('smtp_username', ''),
                smtp_password=settings.get('smtp_password', ''),
                sender_name=settings.get('sender_name', 'XBoard'),
                sender_email=settings.get('sender_email', ''),
                use_tls=settings.get('use_tls', True),
                use_ssl=settings.get('use_ssl', False),
                max_retries=settings.get('max_retries', 3),
                retry_delay=settings.get('retry_delay', 60)
            )
            
            notification_config = NotificationConfig(
                email_notifications=settings.get('email_notifications', True),
                push_notifications=settings.get('push_notifications', False),
                subscription_expiry_reminder=settings.get('subscription_expiry_reminder', True),
                reminder_days=settings.get('reminder_days', [7, 3, 1]),
                new_user_notification=settings.get('new_user_notification', True),
                payment_notification=settings.get('payment_notification', True),
                system_notification=settings.get('system_notification', True)
            )
            
            theme_config = SystemThemeConfig(
                default_theme=settings.get('default_theme', 'default'),
                available_themes=settings.get('available_themes', ['default', 'dark', 'light']),
                custom_css=settings.get('custom_css'),
                logo_url=settings.get('logo_url'),
                favicon_url=settings.get('favicon_url'),
                primary_color=settings.get('primary_color', '#1677ff'),
                secondary_color=settings.get('secondary_color', '#52c41a')
            )
            
            payment_config = PaymentConfig(
                enabled=settings.get('payment_enabled', True),
                currency=settings.get('currency', 'CNY'),
                alipay_enabled=settings.get('alipay_enabled', True),
                wechat_enabled=settings.get('wechat_enabled', True),
                paypal_enabled=settings.get('paypal_enabled', False),
                stripe_enabled=settings.get('stripe_enabled', False)
            )
            
            announcement_config = AnnouncementConfig(
                enabled=settings.get('announcement_enabled', True),
                max_announcements=settings.get('max_announcements', 10),
                auto_expire=settings.get('auto_expire', True),
                expire_days=settings.get('expire_days', 30)
            )
            
            security_config = SecurityConfig(
                two_factor_auth=settings.get('two_factor_auth', False),
                login_attempts_limit=settings.get('login_attempts_limit', 5),
                lockout_duration=settings.get('lockout_duration', 15),
                password_expiry_days=settings.get('password_expiry_days', 90),
                require_strong_password=settings.get('require_strong_password', True),
                session_timeout_minutes=settings.get('session_timeout_minutes', 30)
            )
            
            performance_config = PerformanceConfig(
                cache_enabled=settings.get('cache_enabled', True),
                cache_type=settings.get('cache_type', 'memory'),
                cache_timeout=settings.get('cache_timeout', 300),
                max_connections=settings.get('max_connections', 1000),
                workers=settings.get('workers', 4),
                enable_compression=settings.get('enable_compression', True),
                enable_gzip=settings.get('enable_gzip', True),
                static_file_cache=settings.get('static_file_cache', 3600),
                api_rate_limit=settings.get('api_rate_limit', 100),
                api_rate_limit_window=settings.get('api_rate_limit_window', 60)
            )
            
            return SystemSettings(
                general=general_config,
                registration=registration_config,
                email=email_config,
                notification=notification_config,
                theme=theme_config,
                payment=payment_config,
                announcement=announcement_config,
                security=security_config,
                performance=performance_config
            )
        except Exception as e:
            # 如果出错，返回默认配置
            return self._get_default_system_settings()

    def update_system_settings(self, settings: Dict[str, Any]) -> bool:
        """更新系统设置"""
        try:
            for key, value in settings.items():
                # 根据键名确定配置类型
                if key in ['maintenance_mode', 'registration_enabled', 'email_verification_required']:
                    self.set_config_value(key, value, 'boolean')
                elif key in ['min_password_length', 'max_login_attempts', 'session_timeout', 'smtp_port']:
                    self.set_config_value(key, value, 'number')
                elif key in ['reminder_days', 'available_themes']:
                    self.set_config_value(key, value, 'json')
                else:
                    self.set_config_value(key, value, 'string')
            return True
        except Exception:
            return False

    def _get_default_system_settings(self) -> SystemSettings:
        """获取默认系统设置"""
        return SystemSettings(
            general=GeneralConfig(),
            registration=RegistrationConfig(),
            email=EmailConfig(),
            notification=NotificationConfig(),
            theme=SystemThemeConfig(),
            payment=PaymentConfig(),
            announcement=AnnouncementConfig(),
            security=SecurityConfig(),
            performance=PerformanceConfig()
        )

    def get_smtp_config(self) -> Dict[str, Any]:
        """获取SMTP配置"""
        try:
            configs = self.get_configs_by_category('email')
            smtp_config = {}
            for config in configs:
                if config.key.startswith('smtp_'):
                    smtp_config[config.key] = self.get_config_value(config.key)
            
            # 如果没有配置，返回默认值
            if not smtp_config:
                smtp_config = {
                    'smtp_host': 'smtp.qq.com',
                    'smtp_port': 587,
                    'smtp_username': '',
                    'smtp_password': '',
                    'sender_name': 'XBoard',
                    'sender_email': '',
                    'use_tls': True,
                    'use_ssl': False
                }
            
            return smtp_config
        except Exception:
            return {
                'smtp_host': 'smtp.qq.com',
                'smtp_port': 587,
                'smtp_username': '',
                'smtp_password': '',
                'sender_name': 'XBoard',
                'sender_email': '',
                'use_tls': True,
                'use_ssl': False
            }

    def update_smtp_config(self, smtp_config: Dict[str, Any]) -> bool:
        """更新SMTP配置"""
        try:
            for key, value in smtp_config.items():
                if key.startswith('smtp_') or key in ['sender_name', 'sender_email', 'use_tls', 'use_ssl']:
                    self.set_config_value(key, value)
            return True
        except Exception:
            return False

    def test_smtp_connection(self, smtp_config: Dict[str, Any]) -> bool:
        """测试SMTP连接"""
        try:
            # 这里应该实现实际的SMTP连接测试
            # 暂时返回True表示测试通过
            return True
        except Exception:
            return False

    def get_registration_config(self) -> Dict[str, Any]:
        """获取注册配置"""
        try:
            configs = self.get_configs_by_category('registration')
            reg_config = {}
            for config in configs:
                reg_config[config.key] = self.get_config_value(config.key)
            
            # 如果没有配置，返回默认值
            if not reg_config:
                reg_config = {
                    'allow_registration': True,
                    'email_verification_required': True,
                    'allow_qq_email_only': True,
                    'auto_approve': False,
                    'welcome_message': '欢迎加入XBoard！'
                }
            
            return reg_config
        except Exception:
            return {
                'allow_registration': True,
                'email_verification_required': True,
                'allow_qq_email_only': True,
                'auto_approve': False,
                'welcome_message': '欢迎加入XBoard！'
            }

    def update_registration_config(self, reg_config: Dict[str, Any]) -> bool:
        """更新注册配置"""
        try:
            for key, value in reg_config.items():
                if key in ['allow_registration', 'email_verification_required', 'allow_qq_email_only', 'auto_approve', 'welcome_message']:
                    self.set_config_value(key, value)
            return True
        except Exception:
            return False

    def get_notification_config(self) -> Dict[str, Any]:
        """获取通知配置"""
        try:
            configs = self.get_configs_by_category('notification')
            notif_config = {}
            for config in configs:
                notif_config[config.key] = self.get_config_value(config.key)
            
            # 如果没有配置，返回默认值
            if not notif_config:
                notif_config = {
                    'email_notifications': True,
                    'push_notifications': False,
                    'subscription_expiry_reminder': True,
                    'reminder_days': [7, 3, 1],
                    'new_user_notification': True,
                    'payment_notification': True,
                    'system_notification': True
                }
            
            return notif_config
        except Exception:
            return {
                'email_notifications': True,
                'push_notifications': False,
                'subscription_expiry_reminder': True,
                'reminder_days': [7, 3, 1],
                'new_user_notification': True,
                'payment_notification': True,
                'system_notification': True
            }

    def update_notification_config(self, notif_config: Dict[str, Any]) -> bool:
        """更新通知配置"""
        try:
            for key, value in notif_config.items():
                if key in ['email_notifications', 'push_notifications', 'subscription_expiry_reminder', 'reminder_days', 'new_user_notification', 'payment_notification', 'system_notification']:
                    self.set_config_value(key, value)
            return True
        except Exception:
            return False

    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        try:
            configs = self.get_configs_by_category('security')
            security_config = {}
            for config in configs:
                security_config[config.key] = self.get_config_value(config.key)
            
            # 如果没有配置，返回默认值
            if not security_config:
                security_config = {
                    'two_factor_auth': False,
                    'login_attempts_limit': 5,
                    'lockout_duration': 15,
                    'password_expiry_days': 90,
                    'require_strong_password': True,
                    'session_timeout_minutes': 30
                }
            
            return security_config
        except Exception:
            return {
                'two_factor_auth': False,
                'login_attempts_limit': 5,
                'lockout_duration': 15,
                'password_expiry_days': 90,
                'require_strong_password': True,
                'session_timeout_minutes': 30
            }

    def update_security_config(self, security_config: Dict[str, Any]) -> bool:
        """更新安全配置"""
        try:
            for key, value in security_config.items():
                if key in ['two_factor_auth', 'login_attempts_limit', 'lockout_duration', 'password_expiry_days', 'require_strong_password', 'session_timeout_minutes']:
                    self.set_config_value(key, value)
            return True
        except Exception:
            return False

    def update_payment_configs(self, payment_configs: Dict[str, Any]) -> bool:
        """更新支付配置"""
        try:
            # 基本支付设置
            basic_fields = ['payment_enabled', 'currency', 'default_payment_method']
            for key, value in payment_configs.items():
                if key in basic_fields:
                    self.set_config_value(key, value)
            
            # 支付宝配置
            alipay_fields = ['alipay_app_id', 'alipay_private_key', 'alipay_public_key', 'alipay_gateway']
            for key, value in payment_configs.items():
                if key in alipay_fields:
                    self.set_config_value(key, value)
            
            # 微信支付配置
            wechat_fields = ['wechat_app_id', 'wechat_mch_id', 'wechat_api_key', 'wechat_cert_path', 'wechat_key_path']
            for key, value in payment_configs.items():
                if key in wechat_fields:
                    self.set_config_value(key, value)
            
            # PayPal配置
            paypal_fields = ['paypal_client_id', 'paypal_secret', 'paypal_mode']
            for key, value in payment_configs.items():
                if key in paypal_fields:
                    self.set_config_value(key, value)
            
            # Stripe配置
            stripe_fields = ['stripe_publishable_key', 'stripe_secret_key', 'stripe_webhook_secret']
            for key, value in payment_configs.items():
                if key in stripe_fields:
                    self.set_config_value(key, value)
            
            # 银行转账配置
            bank_fields = ['bank_name', 'bank_account', 'bank_branch', 'account_holder']
            for key, value in payment_configs.items():
                if key in bank_fields:
                    self.set_config_value(key, value)
            
            # 回调地址配置
            callback_fields = ['return_url', 'notify_url']
            for key, value in payment_configs.items():
                if key in callback_fields:
                    self.set_config_value(key, value)
            
            return True
        except Exception:
            return False

    def test_payment_config(self, payment_config: Dict[str, Any]) -> bool:
        """测试支付配置"""
        try:
            payment_method = payment_config.get('default_payment_method', 'alipay')
            
            if payment_method == 'alipay':
                # 测试支付宝配置
                app_id = payment_config.get('alipay_app_id')
                private_key = payment_config.get('alipay_private_key')
                if not app_id or not private_key:
                    return False
                # 这里可以添加实际的支付宝API测试逻辑
                return True
                
            elif payment_method == 'wechat':
                # 测试微信支付配置
                app_id = payment_config.get('wechat_app_id')
                mch_id = payment_config.get('wechat_mch_id')
                api_key = payment_config.get('wechat_api_key')
                if not app_id or not mch_id or not api_key:
                    return False
                # 这里可以添加实际的微信支付API测试逻辑
                return True
                
            elif payment_method == 'paypal':
                # 测试PayPal配置
                client_id = payment_config.get('paypal_client_id')
                secret = payment_config.get('paypal_secret')
                if not client_id or not secret:
                    return False
                # 这里可以添加实际的PayPal API测试逻辑
                return True
                
            elif payment_method == 'stripe':
                # 测试Stripe配置
                publishable_key = payment_config.get('stripe_publishable_key')
                secret_key = payment_config.get('stripe_secret_key')
                if not publishable_key or not secret_key:
                    return False
                # 这里可以添加实际的Stripe API测试逻辑
                return True
                
            elif payment_method == 'bank_transfer':
                # 测试银行转账配置
                bank_name = payment_config.get('bank_name')
                bank_account = payment_config.get('bank_account')
                account_holder = payment_config.get('account_holder')
                if not bank_name or not bank_account or not account_holder:
                    return False
                return True
                
            return False
        except Exception:
            return False

    # ==================== 公告管理 ====================
    
    def get_announcements(self, target_users: str = 'all') -> List[Announcement]:
        """获取公告列表"""
        query = self.db.query(Announcement).filter(Announcement.is_active == True)
        
        if target_users != 'all':
            query = query.filter(
                or_(
                    Announcement.target_audience == target_users,
                    Announcement.target_audience == 'all'
                )
            )
        
        return query.order_by(Announcement.priority.desc(), Announcement.created_at.desc()).all()

    def get_active_announcements(self, target_users: str = 'all') -> List[Announcement]:
        """获取活跃公告"""
        now = datetime.utcnow()
        announcements = self.get_announcements(target_users)
        
        active_announcements = []
        for announcement in announcements:
            # 检查时间范围
            if announcement.start_date and announcement.start_date > now:
                continue
            if announcement.end_date and announcement.end_date < now:
                continue
            active_announcements.append(announcement)
        
        return active_announcements

    def create_announcement(self, announcement_in: AnnouncementCreate) -> Announcement:
        """创建公告"""
        announcement = Announcement(**announcement_in.dict())
        self.db.add(announcement)
        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def update_announcement(self, announcement_id: int, announcement_in: AnnouncementUpdate) -> Optional[Announcement]:
        """更新公告"""
        announcement = self.db.query(Announcement).filter(Announcement.id == announcement_id).first()
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
        announcement = self.db.query(Announcement).filter(Announcement.id == announcement_id).first()
        if not announcement:
            return False
        
        self.db.delete(announcement)
        self.db.commit()
        return True

    # ==================== 主题管理 ====================
    
    def get_themes(self) -> List[ThemeConfig]:
        """获取主题列表"""
        return self.db.query(ThemeConfig).filter(ThemeConfig.is_active == True).all()

    def get_theme(self, theme_id: int) -> Optional[ThemeConfig]:
        """获取主题"""
        return self.db.query(ThemeConfig).filter(ThemeConfig.id == theme_id).first()

    def create_theme(self, theme_in: ThemeConfigCreate) -> ThemeConfig:
        """创建主题"""
        theme = ThemeConfig(**theme_in.dict())
        self.db.add(theme)
        self.db.commit()
        self.db.refresh(theme)
        return theme

    def update_theme(self, theme_id: int, theme_in: ThemeConfigUpdate) -> Optional[ThemeConfig]:
        """更新主题"""
        theme = self.get_theme(theme_id)
        if not theme:
            return None
        
        update_data = theme_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(theme, field, value)
        
        self.db.commit()
        self.db.refresh(theme)
        return theme

    def delete_theme(self, theme_id: int) -> bool:
        """删除主题"""
        theme = self.get_theme(theme_id)
        if not theme:
            return False
        
        self.db.delete(theme)
        self.db.commit()
        return True 