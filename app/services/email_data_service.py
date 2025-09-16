"""
邮件数据服务
用于从数据库获取邮件模板所需的用户、订阅、套餐等信息
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime


class EmailDataService:
    """邮件数据服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_info(self, user_id: int) -> Dict[str, Any]:
        """获取用户信息"""
        try:
            query = text("""
                SELECT 
                    u.id,
                    u.username,
                    u.email,
                    u.nickname,
                    u.status,
                    u.is_verified,
                    u.created_at,
                    u.last_login,
                    u.avatar_url,
                    u.phone,
                    u.country,
                    u.timezone
                FROM users u
                WHERE u.id = :user_id
            """)
            
            result = self.db.execute(query, {'user_id': user_id}).first()
            if result:
                return {
                    'id': result.id,
                    'username': result.username,
                    'email': result.email,
                    'nickname': result.nickname or result.username,
                    'status': result.status,
                    'is_verified': result.is_verified,
                    'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S') if result.created_at else '未知',
                    'last_login': result.last_login.strftime('%Y-%m-%d %H:%M:%S') if result.last_login else '从未登录',
                    'avatar_url': result.avatar_url,
                    'phone': result.phone,
                    'country': result.country,
                    'timezone': result.timezone
                }
            return {}
        except Exception as e:
            print(f"获取用户信息失败: {str(e)}")
            return {}
    
    def get_subscription_info(self, subscription_id: int) -> Dict[str, Any]:
        """获取订阅信息"""
        try:
            query = text("""
                SELECT 
                    s.id,
                    s.user_id,
                    s.subscription_url,
                    s.device_limit,
                    s.current_devices,
                    s.is_active,
                    s.expire_time,
                    s.created_at,
                    s.updated_at,
                    u.username,
                    u.email,
                    p.name as package_name,
                    p.description as package_description,
                    p.price as package_price,
                    p.duration as package_duration,
                    p.bandwidth_limit as package_bandwidth_limit
                FROM subscriptions s
                LEFT JOIN users u ON s.user_id = u.id
                LEFT JOIN packages p ON s.package_id = p.id
                WHERE s.id = :subscription_id
            """)
            
            result = self.db.execute(query, {'subscription_id': subscription_id}).first()
            if result:
                # 调试信息
                print(f"订阅信息查询结果: subscription_id={subscription_id}, username={result.username}, email={result.email}")
                
                # 计算剩余天数
                remaining_days = 0
                if result.expire_time:
                    remaining_days = max(0, (result.expire_time - datetime.now()).days)
                
                return {
                    'id': result.id,
                    'user_id': result.user_id,
                    'subscription_url': result.subscription_url,
                    'device_limit': result.device_limit,
                    'current_devices': result.current_devices,
                    'max_devices': result.device_limit,
                    'is_active': result.is_active,
                    'expire_time': result.expire_time.strftime('%Y-%m-%d %H:%M:%S') if result.expire_time else '永久',
                    'remaining_days': remaining_days,
                    'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S') if result.created_at else '未知',
                    'updated_at': result.updated_at.strftime('%Y-%m-%d %H:%M:%S') if result.updated_at else '未知',
                    'username': result.username,
                    'user_email': result.email,
                    'package_name': result.package_name or '未知套餐',
                    'package_description': result.package_description or '无描述',
                    'package_price': float(result.package_price) if result.package_price else 0.0,
                    'package_duration': result.package_duration or 0,
                    'package_bandwidth_limit': result.package_bandwidth_limit
                }
            return {}
        except Exception as e:
            print(f"获取订阅信息失败: {str(e)}")
            return {}
    
    def get_user_subscription_info(self, user_id: int) -> Dict[str, Any]:
        """获取用户的订阅信息"""
        try:
            query = text("""
                SELECT 
                    s.id,
                    s.subscription_url,
                    s.device_limit,
                    s.current_devices,
                    s.is_active,
                    s.expire_time,
                    s.created_at,
                    p.name as package_name,
                    p.description as package_description,
                    p.price as package_price,
                    p.duration as package_duration,
                    p.bandwidth_limit as package_bandwidth_limit
                FROM subscriptions s
                LEFT JOIN packages p ON s.package_id = p.id
                WHERE s.user_id = :user_id
                ORDER BY s.created_at DESC
                LIMIT 1
            """)
            
            result = self.db.execute(query, {'user_id': user_id}).first()
            if result:
                # 计算剩余天数
                remaining_days = 0
                if result.expire_time:
                    remaining_days = max(0, (result.expire_time - datetime.now()).days)
                
                return {
                    'id': result.id,
                    'subscription_url': result.subscription_url,
                    'device_limit': result.device_limit,
                    'current_devices': result.current_devices,
                    'max_devices': result.device_limit,
                    'is_active': result.is_active,
                    'expire_time': result.expire_time.strftime('%Y-%m-%d %H:%M:%S') if result.expire_time else '永久',
                    'remaining_days': remaining_days,
                    'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S') if result.created_at else '未知',
                    'package_name': result.package_name or '未知套餐',
                    'package_description': result.package_description or '无描述',
                    'package_price': float(result.package_price) if result.package_price else 0.0,
                    'package_duration': result.package_duration or 0,
                    'package_bandwidth_limit': result.package_bandwidth_limit
                }
            return {}
        except Exception as e:
            print(f"获取用户订阅信息失败: {str(e)}")
            return {}
    
    def get_order_info(self, order_id: int) -> Dict[str, Any]:
        """获取订单信息"""
        try:
            query = text("""
                SELECT 
                    o.id,
                    o.order_no,
                    o.user_id,
                    o.amount,
                    o.status,
                    o.payment_method_name,
                    o.created_at,
                    o.updated_at,
                    u.username,
                    u.email,
                    p.name as package_name,
                    p.description as package_description,
                    p.price as package_price,
                    p.duration as package_duration
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
                LEFT JOIN packages p ON o.package_id = p.id
                WHERE o.id = :order_id
            """)
            
            result = self.db.execute(query, {'order_id': order_id}).first()
            if result:
                return {
                    'id': result.id,
                    'order_no': result.order_no,
                    'user_id': result.user_id,
                    'amount': float(result.amount) if result.amount else 0.0,
                    'status': result.status,
                    'payment_method_name': result.payment_method_name,
                    'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S') if result.created_at else '未知',
                    'updated_at': result.updated_at.strftime('%Y-%m-%d %H:%M:%S') if result.updated_at else '未知',
                    'username': result.username,
                    'user_email': result.email,
                    'package_name': result.package_name or '未知套餐',
                    'package_description': result.package_description or '无描述',
                    'package_price': float(result.package_price) if result.package_price else 0.0,
                    'package_duration': result.package_duration or 0
                }
            return {}
        except Exception as e:
            print(f"获取订单信息失败: {str(e)}")
            return {}
    
    def get_system_config(self, key: str) -> Optional[str]:
        """获取系统配置"""
        try:
            query = text("SELECT value FROM system_configs WHERE key = :key")
            result = self.db.execute(query, {'key': key}).first()
            return result[0] if result else None
        except Exception as e:
            print(f"获取系统配置失败: {str(e)}")
            return None
    
    def get_complete_subscription_data(self, subscription_id: int, request=None) -> Dict[str, Any]:
        """获取完整的订阅数据，包括用户信息、订阅信息、套餐信息"""
        try:
            # 获取订阅信息
            subscription_info = self.get_subscription_info(subscription_id)
            if not subscription_info:
                return {}
            
            # 获取用户信息
            user_info = self.get_user_info(subscription_info['user_id'])
            
            # 获取系统配置
            site_name = self.get_system_config('site_name') or '网络服务'
            
            # 合并所有信息，确保用户名正确传递
            complete_data = {
                **subscription_info,
                **user_info,
                'site_name': site_name,
                'subscription_id': subscription_id
            }
            
            # 确保用户名字段存在且不为空
            if not complete_data.get('username') and user_info.get('username'):
                complete_data['username'] = user_info['username']
            elif not complete_data.get('username') and subscription_info.get('username'):
                complete_data['username'] = subscription_info['username']
            
            # 添加订阅URL（使用动态域名）
            from app.core.domain_config import get_domain_config
            domain_config = get_domain_config()
            base_url = domain_config.get_base_url(request, self.db)
            
            if subscription_info.get('subscription_url'):
                complete_data.update({
                    'v2ray_url': f"{base_url}/api/v1/subscriptions/ssr/{subscription_info['subscription_url']}",
                    'clash_url': f"{base_url}/api/v1/subscriptions/clash/{subscription_info['subscription_url']}",
                    'ssr_url': f"{base_url}/api/v1/subscriptions/ssr/{subscription_info['subscription_url']}"
                })
            
            return complete_data
            
        except Exception as e:
            print(f"获取完整订阅数据失败: {str(e)}")
            return {}
    
    def get_complete_user_data(self, user_id: int, request=None) -> Dict[str, Any]:
        """获取完整的用户数据，包括用户信息和订阅信息"""
        try:
            # 获取用户信息
            user_info = self.get_user_info(user_id)
            if not user_info:
                return {}
            
            # 获取用户订阅信息
            subscription_info = self.get_user_subscription_info(user_id)
            
            # 获取系统配置
            site_name = self.get_system_config('site_name') or '网络服务'
            
            # 合并所有信息，确保用户名正确传递
            complete_data = {
                **user_info,
                **subscription_info,
                'site_name': site_name
            }
            
            # 确保用户名字段存在且不为空
            if not complete_data.get('username') and user_info.get('username'):
                complete_data['username'] = user_info['username']
            
            # 添加订阅URL（使用动态域名）
            from app.core.domain_config import get_domain_config
            domain_config = get_domain_config()
            base_url = domain_config.get_base_url(request, self.db)
            
            if subscription_info.get('subscription_url'):
                complete_data.update({
                    'v2ray_url': f"{base_url}/api/v1/subscriptions/ssr/{subscription_info['subscription_url']}",
                    'clash_url': f"{base_url}/api/v1/subscriptions/clash/{subscription_info['subscription_url']}",
                    'ssr_url': f"{base_url}/api/v1/subscriptions/ssr/{subscription_info['subscription_url']}"
                })
            
            return complete_data
            
        except Exception as e:
            print(f"获取完整用户数据失败: {str(e)}")
            return {}
