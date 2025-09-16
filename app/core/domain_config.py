"""
动态域名配置管理
支持从环境变量、数据库配置或请求头中获取域名信息
"""
import os
from typing import Optional, Dict, Any
from functools import lru_cache
from sqlalchemy.orm import Session
from app.core.database import get_db


class DomainConfig:
    """域名配置管理器"""
    
    def __init__(self):
        self._domain_cache = {}
        self._ssl_enabled_cache = {}
    
    def get_base_url(self, request=None, db: Optional[Session] = None) -> str:
        """
        获取基础URL，优先级：
        1. 请求头中的Host
        2. 环境变量
        3. 数据库配置
        4. 默认值
        """
        # 1. 从请求头获取（最高优先级）
        if request:
            host = request.headers.get('host', '')
            if host:
                scheme = 'https' if self.is_ssl_enabled(request, db) else 'http'
                return f"{scheme}://{host}"
        
        # 2. 从环境变量获取
        domain = os.getenv('DOMAIN_NAME')
        if domain:
            scheme = 'https' if self.is_ssl_enabled(None, db) else 'http'
            return f"{scheme}://{domain}"
        
        # 3. 从数据库配置获取
        if db:
            try:
                from sqlalchemy import text
                result = db.execute(text("SELECT value FROM system_configs WHERE key = 'domain_name'")).first()
                if result:
                    domain = result[0]
                    scheme = 'https' if self.is_ssl_enabled(None, db) else 'http'
                    return f"{scheme}://{domain}"
            except Exception:
                pass
        
        # 4. 默认值（开发环境）
        return "http://localhost:8000"
    
    def get_frontend_url(self, request=None, db: Optional[Session] = None) -> str:
        """
        获取前端URL
        """
        base_url = self.get_base_url(request, db)
        
        # 如果配置了前端域名，使用前端域名
        frontend_domain = os.getenv('FRONTEND_DOMAIN')
        if frontend_domain:
            scheme = 'https' if self.is_ssl_enabled(request, db) else 'http'
            return f"{scheme}://{frontend_domain}"
        
        # 否则使用基础URL
        return base_url
    
    def is_ssl_enabled(self, request=None, db: Optional[Session] = None) -> bool:
        """
        检查是否启用SSL
        """
        # 1. 从请求头检查
        if request:
            # 检查X-Forwarded-Proto头（负载均衡器设置）
            if request.headers.get('x-forwarded-proto') == 'https':
                return True
            # 检查X-Forwarded-Ssl头
            if request.headers.get('x-forwarded-ssl') == 'on':
                return True
            # 检查请求scheme
            if hasattr(request, 'url') and str(request.url).startswith('https'):
                return True
        
        # 2. 从环境变量检查
        ssl_enabled = os.getenv('SSL_ENABLED', '').lower()
        if ssl_enabled in ['true', '1', 'yes', 'on']:
            return True
        
        # 3. 从数据库配置检查
        if db:
            try:
                from sqlalchemy import text
                result = db.execute(text("SELECT value FROM system_configs WHERE key = 'ssl_enabled'")).first()
                if result:
                    return result[0].lower() in ['true', '1', 'yes', 'on']
            except Exception:
                pass
        
        # 4. 默认不启用SSL（开发环境）
        return False
    
    def get_payment_callback_urls(self, request=None, db: Optional[Session] = None) -> Dict[str, str]:
        """
        获取支付回调URL
        """
        base_url = self.get_base_url(request, db)
        
        return {
            'notify_url': f"{base_url}/api/v1/payment/alipay/notify",
            'return_url': f"{base_url}/payment/success",
            'cancel_url': f"{base_url}/payment/cancel"
        }
    
    def get_subscription_urls(self, subscription_key: str, request=None, db: Optional[Session] = None) -> Dict[str, str]:
        """
        获取订阅URL
        """
        base_url = self.get_base_url(request, db)
        
        return {
            'v2ray_url': f"{base_url}/api/v1/subscriptions/v2ray/{subscription_key}",
            'clash_url': f"{base_url}/api/v1/subscriptions/clash/{subscription_key}",
            'ssr_url': f"{base_url}/api/v1/subscriptions/ssr/{subscription_key}"
        }
    
    def get_email_base_url(self, request=None, db: Optional[Session] = None) -> str:
        """
        获取邮件中使用的基础URL
        """
        # 邮件中的URL应该使用配置的域名，而不是请求域名
        domain = os.getenv('DOMAIN_NAME')
        if domain:
            scheme = 'https' if self.is_ssl_enabled(None, db) else 'http'
            return f"{scheme}://{domain}"
        
        # 如果没有配置域名，使用请求域名
        return self.get_base_url(request, db)
    
    def update_domain_config(self, domain_name: str, ssl_enabled: bool, db: Session):
        """
        更新域名配置到数据库
        """
        try:
            from sqlalchemy import text
            from datetime import datetime
            
            # 更新域名配置
            db.execute(text("""
                INSERT OR REPLACE INTO system_configs (key, value, type, created_at, updated_at)
                VALUES ('domain_name', :domain_name, 'system', :now, :now)
            """), {
                'domain_name': domain_name,
                'now': datetime.now()
            })
            
            # 更新SSL配置
            db.execute(text("""
                INSERT OR REPLACE INTO system_configs (key, value, type, created_at, updated_at)
                VALUES ('ssl_enabled', :ssl_enabled, 'system', :now, :now)
            """), {
                'ssl_enabled': str(ssl_enabled).lower(),
                'now': datetime.now()
            })
            
            db.commit()
            
            # 清除缓存
            self._domain_cache.clear()
            self._ssl_enabled_cache.clear()
            
        except Exception as e:
            db.rollback()
            raise e
    
    def get_domain_info(self, request=None, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        获取完整的域名信息
        """
        return {
            'base_url': self.get_base_url(request, db),
            'frontend_url': self.get_frontend_url(request, db),
            'ssl_enabled': self.is_ssl_enabled(request, db),
            'domain_name': self._extract_domain_name(self.get_base_url(request, db)),
            'payment_urls': self.get_payment_callback_urls(request, db),
            'email_base_url': self.get_email_base_url(request, db)
        }
    
    def _extract_domain_name(self, url: str) -> str:
        """从URL中提取域名"""
        if '://' in url:
            return url.split('://')[1].split('/')[0]
        return url


# 全局域名配置实例
domain_config = DomainConfig()


def get_domain_config() -> DomainConfig:
    """获取域名配置实例"""
    return domain_config
