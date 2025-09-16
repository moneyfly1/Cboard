"""
邮件API客户端服务
用于通过API端点获取邮件模板所需的用户、订阅等信息
"""
import requests
import json
from typing import Dict, Any, Optional
from fastapi import Request
from sqlalchemy.orm import Session


class EmailAPIClient:
    """邮件API客户端类"""
    
    def __init__(self, request: Request, db: Session):
        self.request = request
        self.db = db
        self.base_url = self._get_base_url()
    
    def _get_base_url(self) -> str:
        """获取API基础URL"""
        try:
            from app.core.domain_config import get_domain_config
            domain_config = get_domain_config()
            return domain_config.get_base_url(self.request, self.db)
        except Exception as e:
            print(f"获取base_url失败: {str(e)}")
            return "http://localhost:8000"
    
    def _make_api_request(self, endpoint: str, method: str = "GET", data: dict = None) -> Optional[Dict[str, Any]]:
        """发送API请求"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            else:
                return None
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API请求失败: {endpoint}, 状态码: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"API请求异常: {endpoint}, 错误: {str(e)}")
            return None
    
    def get_user_info(self, user_id: int) -> Dict[str, Any]:
        """通过API获取用户信息"""
        try:
            # 这里需要根据实际的API端点调整
            # 假设有一个获取用户信息的API端点
            endpoint = f"/api/v1/users/{user_id}"
            result = self._make_api_request(endpoint)
            
            if result and result.get('success'):
                user_data = result.get('data', {})
                return {
                    'id': user_data.get('id'),
                    'username': user_data.get('username', '用户'),
                    'email': user_data.get('email', ''),
                    'nickname': user_data.get('nickname') or user_data.get('username', '用户'),
                    'status': user_data.get('status', 'active'),
                    'is_verified': user_data.get('is_verified', False),
                    'created_at': user_data.get('created_at', '未知'),
                    'last_login': user_data.get('last_login', '从未登录'),
                    'avatar_url': user_data.get('avatar_url', ''),
                    'phone': user_data.get('phone', ''),
                    'country': user_data.get('country', ''),
                    'timezone': user_data.get('timezone', '')
                }
            return {}
        except Exception as e:
            print(f"获取用户信息失败: {str(e)}")
            return {}
    
    def get_subscription_info(self, subscription_id: int) -> Dict[str, Any]:
        """通过API获取订阅信息"""
        try:
            # 使用订阅API端点
            endpoint = f"/api/v1/subscriptions/{subscription_id}"
            result = self._make_api_request(endpoint)
            
            if result and result.get('success'):
                sub_data = result.get('data', {})
                return {
                    'id': sub_data.get('id'),
                    'user_id': sub_data.get('user_id'),
                    'subscription_url': sub_data.get('subscription_url', ''),
                    'device_limit': sub_data.get('device_limit', 3),
                    'current_devices': sub_data.get('current_devices', 0),
                    'max_devices': sub_data.get('device_limit', 3),
                    'is_active': sub_data.get('is_active', True),
                    'expire_time': sub_data.get('expire_time', '永久'),
                    'remaining_days': sub_data.get('remaining_days', 0),
                    'created_at': sub_data.get('created_at', '未知'),
                    'updated_at': sub_data.get('updated_at', '未知'),
                    'username': sub_data.get('username', '用户'),
                    'user_email': sub_data.get('user_email', ''),
                    'package_name': sub_data.get('package_name', '未知套餐'),
                    'package_description': sub_data.get('package_description', '无描述'),
                    'package_price': sub_data.get('package_price', 0.0),
                    'package_duration': sub_data.get('package_duration', 0),
                    'package_bandwidth_limit': sub_data.get('package_bandwidth_limit')
                }
            return {}
        except Exception as e:
            print(f"获取订阅信息失败: {str(e)}")
            return {}
    
    def get_user_dashboard_info(self, user_id: int) -> Dict[str, Any]:
        """通过API获取用户仪表板信息（包含订阅信息）"""
        try:
            # 使用用户仪表板API端点
            endpoint = f"/api/v1/users/dashboard"
            # 这里需要传递认证信息，实际使用时需要调整
            result = self._make_api_request(endpoint)
            
            if result and result.get('success'):
                data = result.get('data', {})
                return {
                    'id': data.get('id'),
                    'username': data.get('username', '用户'),
                    'email': data.get('email', ''),
                    'nickname': data.get('nickname') or data.get('username', '用户'),
                    'subscription_id': data.get('subscription_id'),
                    'subscription_url': data.get('subscription_url', ''),
                    'device_limit': data.get('device_limit', 3),
                    'current_devices': data.get('current_devices', 0),
                    'max_devices': data.get('device_limit', 3),
                    'is_active': data.get('is_active', True),
                    'expire_time': data.get('expire_time', '永久'),
                    'remaining_days': data.get('remaining_days', 0),
                    'package_name': data.get('package_name', '未知套餐'),
                    'package_description': data.get('package_description', '无描述'),
                    'package_price': data.get('package_price', 0.0),
                    'package_duration': data.get('package_duration', 0),
                    'package_bandwidth_limit': data.get('package_bandwidth_limit')
                }
            return {}
        except Exception as e:
            print(f"获取用户仪表板信息失败: {str(e)}")
            return {}
    
    def get_subscription_urls(self, subscription_id: int) -> Dict[str, str]:
        """通过API获取订阅地址"""
        try:
            # 获取V2Ray/SSR订阅地址
            v2ray_endpoint = f"/api/v1/subscriptions/{subscription_id}/v2ray"
            clash_endpoint = f"/api/v1/subscriptions/{subscription_id}/clash"
            ssr_endpoint = f"/api/v1/subscriptions/{subscription_id}/ssr"
            
            # 构建完整的订阅地址
            subscription_urls = {
                'v2ray_url': f"{self.base_url}{v2ray_endpoint}",
                'clash_url': f"{self.base_url}{clash_endpoint}",
                'ssr_url': f"{self.base_url}{ssr_endpoint}"
            }
            
            return subscription_urls
        except Exception as e:
            print(f"获取订阅地址失败: {str(e)}")
            return {
                'v2ray_url': '',
                'clash_url': '',
                'ssr_url': ''
            }
    
    def get_complete_subscription_data(self, subscription_id: int) -> Dict[str, Any]:
        """获取完整的订阅数据（通过API）"""
        try:
            # 获取订阅信息
            subscription_info = self.get_subscription_info(subscription_id)
            if not subscription_info:
                return {}
            
            # 获取用户信息
            user_info = self.get_user_info(subscription_info.get('user_id', 0))
            
            # 获取订阅地址
            subscription_urls = self.get_subscription_urls(subscription_id)
            
            # 合并所有信息
            complete_data = {
                **subscription_info,
                **user_info,
                **subscription_urls,
                'subscription_id': subscription_id,
                'base_url': self.base_url
            }
            
            return complete_data
            
        except Exception as e:
            print(f"获取完整订阅数据失败: {str(e)}")
            return {}
    
    def get_order_info(self, order_id: int) -> Dict[str, Any]:
        """通过API获取订单信息"""
        try:
            # 使用订单API端点
            endpoint = f"/api/v1/orders/{order_id}"
            result = self._make_api_request(endpoint)
            
            if result and result.get('success'):
                order_data = result.get('data', {})
                return {
                    'id': order_data.get('id'),
                    'order_no': order_data.get('order_no', ''),
                    'user_id': order_data.get('user_id'),
                    'amount': order_data.get('amount', 0.0),
                    'status': order_data.get('status', ''),
                    'payment_method_name': order_data.get('payment_method_name', ''),
                    'created_at': order_data.get('created_at', '未知'),
                    'updated_at': order_data.get('updated_at', '未知'),
                    'username': order_data.get('username', '用户'),
                    'user_email': order_data.get('user_email', ''),
                    'package_name': order_data.get('package_name', '未知套餐'),
                    'package_description': order_data.get('package_description', '无描述'),
                    'package_price': order_data.get('package_price', 0.0),
                    'package_duration': order_data.get('package_duration', 0),
                    'base_url': self.base_url
                }
            return {}
        except Exception as e:
            print(f"获取订单信息失败: {str(e)}")
            return {}
    
    def get_complete_user_data(self, user_id: int) -> Dict[str, Any]:
        """获取完整的用户数据（通过API）"""
        try:
            # 获取用户仪表板信息（包含订阅信息）
            user_data = self.get_user_dashboard_info(user_id)
            if not user_data:
                return {}
            
            # 获取订阅地址
            subscription_id = user_data.get('subscription_id')
            if subscription_id:
                subscription_urls = self.get_subscription_urls(subscription_id)
                user_data.update(subscription_urls)
            
            user_data['base_url'] = self.base_url
            return user_data
            
        except Exception as e:
            print(f"获取完整用户数据失败: {str(e)}")
            return {}
