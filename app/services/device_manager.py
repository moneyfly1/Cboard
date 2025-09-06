"""
设备管理服务
负责处理订阅设备的识别、管理和限制
"""

import hashlib
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.subscription import Subscription
from app.models.user import User


class DeviceManager:
    """设备管理器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_device_hash(self, user_agent: str, ip_address: str) -> str:
        """生成设备唯一标识"""
        device_string = f"{user_agent}|{ip_address}"
        return hashlib.md5(device_string.encode('utf-8')).hexdigest()
    
    def parse_user_agent(self, user_agent: str) -> Dict[str, str]:
        """解析User-Agent，识别软件、操作系统、设备信息"""
        result = {
            'software_name': 'Unknown',
            'software_version': '',
            'os_name': 'Unknown',
            'os_version': '',
            'device_model': '',
            'device_brand': '',
            'software_category': 'unknown'
        }
        
        # 获取软件识别规则
        rules = self.get_software_rules()
        
        # 转换为小写进行匹配
        ua_lower = user_agent.lower()
        
        # 匹配软件规则
        for rule in rules:
            if rule['user_agent_pattern'].lower() in ua_lower:
                result['software_name'] = rule['software_name']
                result['software_category'] = rule['software_category']
                break
        
        # 解析操作系统信息
        os_info = self._parse_os_info(user_agent)
        result.update(os_info)
        
        # 解析设备信息
        device_info = self._parse_device_info(user_agent)
        result.update(device_info)
        
        # 解析软件版本
        version_info = self._parse_version_info(user_agent)
        result.update(version_info)
        
        return result
    
    def _parse_os_info(self, user_agent: str) -> Dict[str, str]:
        """解析操作系统信息"""
        result = {'os_name': 'Unknown', 'os_version': ''}
        
        # iOS
        if 'iphone' in user_agent.lower():
            result['os_name'] = 'iOS'
            ios_match = re.search(r'os (\d+)_(\d+)', user_agent, re.IGNORECASE)
            if ios_match:
                result['os_version'] = f"{ios_match.group(1)}.{ios_match.group(2)}"
        elif 'ipad' in user_agent.lower():
            result['os_name'] = 'iPadOS'
            ios_match = re.search(r'os (\d+)_(\d+)', user_agent, re.IGNORECASE)
            if ios_match:
                result['os_version'] = f"{ios_match.group(1)}.{ios_match.group(2)}"
        elif 'macintosh' in user_agent.lower() or 'mac os' in user_agent.lower():
            result['os_name'] = 'macOS'
            mac_match = re.search(r'mac os x (\d+)[._](\d+)', user_agent, re.IGNORECASE)
            if mac_match:
                result['os_version'] = f"{mac_match.group(1)}.{mac_match.group(2)}"
        elif 'windows' in user_agent.lower():
            result['os_name'] = 'Windows'
            win_match = re.search(r'windows nt (\d+\.\d+)', user_agent, re.IGNORECASE)
            if win_match:
                result['os_version'] = win_match.group(1)
        elif 'android' in user_agent.lower():
            result['os_name'] = 'Android'
            android_match = re.search(r'android (\d+\.\d+)', user_agent, re.IGNORECASE)
            if android_match:
                result['os_version'] = android_match.group(1)
        elif 'linux' in user_agent.lower():
            result['os_name'] = 'Linux'
        
        return result
    
    def _parse_device_info(self, user_agent: str) -> Dict[str, str]:
        """解析设备信息"""
        result = {'device_model': '', 'device_brand': ''}
        
        # iPhone
        iphone_match = re.search(r'iphone(\d+,\d+)', user_agent, re.IGNORECASE)
        if iphone_match:
            result['device_brand'] = 'Apple'
            result['device_model'] = f"iPhone {iphone_match.group(1).replace(',', '.')}"
        
        # iPad
        ipad_match = re.search(r'ipad(\d+,\d+)', user_agent, re.IGNORECASE)
        if ipad_match:
            result['device_brand'] = 'Apple'
            result['device_model'] = f"iPad {ipad_match.group(1).replace(',', '.')}"
        
        # Android设备
        if 'android' in user_agent.lower():
            # 尝试提取设备型号
            device_match = re.search(r';\s*([^;]+)\s*build', user_agent, re.IGNORECASE)
            if device_match:
                device_name = device_match.group(1).strip()
                # 常见品牌识别
                if any(brand in device_name.lower() for brand in ['samsung', 'galaxy']):
                    result['device_brand'] = 'Samsung'
                elif any(brand in device_name.lower() for brand in ['huawei', 'honor']):
                    result['device_brand'] = 'Huawei'
                elif any(brand in device_name.lower() for brand in ['xiaomi', 'redmi', 'mi ']):
                    result['device_brand'] = 'Xiaomi'
                elif any(brand in device_name.lower() for brand in ['oppo', 'oneplus']):
                    result['device_brand'] = 'OPPO'
                elif any(brand in device_name.lower() for brand in ['vivo', 'iqoo']):
                    result['device_brand'] = 'vivo'
                elif any(brand in device_name.lower() for brand in ['realme']):
                    result['device_brand'] = 'Realme'
                elif any(brand in device_name.lower() for brand in ['meizu']):
                    result['device_brand'] = 'Meizu'
                elif any(brand in device_name.lower() for brand in ['lenovo']):
                    result['device_brand'] = 'Lenovo'
                elif any(brand in device_name.lower() for brand in ['motorola']):
                    result['device_brand'] = 'Motorola'
                elif any(brand in device_name.lower() for brand in ['sony']):
                    result['device_brand'] = 'Sony'
                elif any(brand in device_name.lower() for brand in ['lg']):
                    result['device_brand'] = 'LG'
                elif any(brand in device_name.lower() for brand in ['htc']):
                    result['device_brand'] = 'HTC'
                elif any(brand in device_name.lower() for brand in ['asus']):
                    result['device_brand'] = 'ASUS'
                elif any(brand in device_name.lower() for brand in ['nokia']):
                    result['device_brand'] = 'Nokia'
                elif any(brand in device_name.lower() for brand in ['blackberry']):
                    result['device_brand'] = 'BlackBerry'
                elif any(brand in device_name.lower() for brand in ['google', 'pixel']):
                    result['device_brand'] = 'Google'
                else:
                    result['device_brand'] = 'Unknown'
                
                result['device_model'] = device_name
        
        return result
    
    def _parse_version_info(self, user_agent: str) -> Dict[str, str]:
        """解析软件版本信息"""
        result = {'software_version': ''}
        
        # 通用版本匹配模式
        version_patterns = [
            r'(\d+\.\d+\.\d+)',
            r'(\d+\.\d+)',
            r'v(\d+\.\d+\.\d+)',
            r'version\s*(\d+\.\d+\.\d+)',
            r'(\d+\.\d+\.\d+\.\d+)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, user_agent, re.IGNORECASE)
            if match:
                result['software_version'] = match.group(1)
                break
        
        return result
    
    def get_software_rules(self) -> List[Dict[str, str]]:
        """获取软件识别规则"""
        try:
            result = self.db.execute(text("""
                SELECT software_name, software_category, user_agent_pattern, 
                       os_pattern, device_pattern, version_pattern
                FROM software_rules 
                WHERE is_active = 1
                ORDER BY software_name
            """)).fetchall()
            
            return [
                {
                    'software_name': row[0],
                    'software_category': row[1],
                    'user_agent_pattern': row[2],
                    'os_pattern': row[3],
                    'device_pattern': row[4],
                    'version_pattern': row[5]
                }
                for row in result
            ]
        except Exception as e:
            print(f"获取软件规则失败: {e}")
            return []
    
    def check_subscription_access(self, subscription_url: str, user_agent: str, ip_address: str) -> Dict[str, Any]:
        """检查订阅访问权限"""
        result = {
            'allowed': False,
            'status_code': 200,
            'message': '',
            'device_info': {},
            'access_type': 'allowed'
        }
        
        try:
            # 获取订阅信息
            subscription = self.db.execute(text("""
                SELECT s.*, u.id as user_id, u.username, u.email
                FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                WHERE s.subscription_url = :subscription_url
            """), {'subscription_url': subscription_url}).fetchone()
            
            if not subscription:
                result['status_code'] = 404
                result['message'] = '订阅地址不存在'
                result['access_type'] = 'not_found'
                return result
            
            # 检查订阅是否过期
            if subscription.expire_time and subscription.expire_time < datetime.utcnow():
                result['status_code'] = 403
                result['message'] = '订阅已过期'
                result['access_type'] = 'blocked_expired'
                self._log_access(subscription.id, None, ip_address, user_agent, 'blocked_expired', 403, '订阅已过期')
                return result
            
            # 解析设备信息
            device_info = self.parse_user_agent(user_agent)
            result['device_info'] = device_info
            
            # 生成设备哈希
            device_hash = self.generate_device_hash(user_agent, ip_address)
            
            # 检查设备是否已存在
            existing_device = self.db.execute(text("""
                SELECT id, is_allowed, access_count, first_seen, last_seen
                FROM user_devices
                WHERE device_hash = :device_hash AND subscription_id = :subscription_id
            """), {
                'device_hash': device_hash,
                'subscription_id': subscription.id
            }).fetchone()
            
            if existing_device:
                # 设备已存在，更新访问信息
                self.db.execute(text("""
                    UPDATE user_devices 
                    SET last_seen = CURRENT_TIMESTAMP, access_count = access_count + 1
                    WHERE id = :device_id
                """), {'device_id': existing_device.id})
                
                if existing_device.is_allowed:
                    result['allowed'] = True
                    result['access_type'] = 'allowed'
                    self._log_access(subscription.id, existing_device.id, ip_address, user_agent, 'allowed', 200, '访问成功')
                else:
                    result['status_code'] = 403
                    result['message'] = '设备数量已达上限'
                    result['access_type'] = 'blocked_device_limit'
                    self._log_access(subscription.id, existing_device.id, ip_address, user_agent, 'blocked_device_limit', 403, '设备数量已达上限')
                
                self.db.commit()
                return result
            
            # 新设备，检查设备数量限制
            allowed_devices_count = self.db.execute(text("""
                SELECT COUNT(*) FROM user_devices 
                WHERE subscription_id = :subscription_id AND is_allowed = 1
            """), {'subscription_id': subscription.id}).scalar()
            
            if allowed_devices_count >= subscription.device_limit:
                # 设备数量已达上限，记录但不允许
                device_id = self._create_device_record(
                    subscription.id, subscription.user_id, device_hash, 
                    ip_address, user_agent, device_info, False
                )
                
                result['status_code'] = 403
                result['message'] = f'设备数量已达上限（{subscription.device_limit}个）'
                result['access_type'] = 'blocked_device_limit'
                self._log_access(subscription.id, device_id, ip_address, user_agent, 'blocked_device_limit', 403, result['message'])
            else:
                # 允许新设备
                device_id = self._create_device_record(
                    subscription.id, subscription.user_id, device_hash, 
                    ip_address, user_agent, device_info, True
                )
                
                result['allowed'] = True
                result['access_type'] = 'allowed'
                self._log_access(subscription.id, device_id, ip_address, user_agent, 'allowed', 200, '访问成功')
            
            self.db.commit()
            
        except Exception as e:
            print(f"检查订阅访问权限失败: {e}")
            result['status_code'] = 500
            result['message'] = '服务器内部错误'
            result['access_type'] = 'error'
            self.db.rollback()
        
        return result
    
    def _create_device_record(self, subscription_id: int, user_id: int, device_hash: str, 
                            ip_address: str, user_agent: str, device_info: Dict[str, str], 
                            is_allowed: bool) -> int:
        """创建设备记录"""
        result = self.db.execute(text("""
            INSERT INTO user_devices (
                user_id, subscription_id, device_ua, device_hash, ip_address, user_agent,
                software_name, software_version, os_name, os_version, device_model, 
                device_brand, is_allowed, first_seen, last_seen, access_count
            ) VALUES (
                :user_id, :subscription_id, :device_ua, :device_hash, :ip_address, :user_agent,
                :software_name, :software_version, :os_name, :os_version, :device_model,
                :device_brand, :is_allowed, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1
            )
        """), {
            'user_id': user_id,
            'subscription_id': subscription_id,
            'device_ua': f"{user_agent}|{ip_address}",
            'device_hash': device_hash,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'software_name': device_info.get('software_name', 'Unknown'),
            'software_version': device_info.get('software_version', ''),
            'os_name': device_info.get('os_name', 'Unknown'),
            'os_version': device_info.get('os_version', ''),
            'device_model': device_info.get('device_model', ''),
            'device_brand': device_info.get('device_brand', ''),
            'is_allowed': is_allowed
        })
        
        return result.lastrowid
    
    def _log_access(self, subscription_id: int, device_id: Optional[int], ip_address: str, 
                   user_agent: str, access_type: str, status_code: int, message: str):
        """记录访问日志"""
        try:
            self.db.execute(text("""
                INSERT INTO subscription_access_logs (
                    subscription_id, device_id, ip_address, user_agent, 
                    access_type, response_status, response_message, access_time
                ) VALUES (
                    :subscription_id, :device_id, :ip_address, :user_agent,
                    :access_type, :response_status, :response_message, CURRENT_TIMESTAMP
                )
            """), {
                'subscription_id': subscription_id,
                'device_id': device_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'access_type': access_type,
                'response_status': status_code,
                'response_message': message
            })
        except Exception as e:
            print(f"记录访问日志失败: {e}")
    
    def get_user_devices(self, user_id: int, subscription_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取用户设备列表"""
        try:
            query = """
                SELECT d.*, s.subscription_url, u.username, u.email
                FROM user_devices d
                JOIN subscriptions s ON d.subscription_id = s.id
                JOIN users u ON d.user_id = u.id
                WHERE d.user_id = :user_id
            """
            params = {'user_id': user_id}
            
            if subscription_id:
                query += " AND d.subscription_id = :subscription_id"
                params['subscription_id'] = subscription_id
            
            query += " ORDER BY d.last_seen DESC"
            
            result = self.db.execute(text(query), params).fetchall()
            
            return [
                {
                    'id': row.id,
                    'user_id': row.user_id,
                    'subscription_id': row.subscription_id,
                    'subscription_url': row.subscription_url,
                    'username': row.username,
                    'email': row.email,
                    'device_ua': row.device_ua,
                    'device_hash': row.device_hash,
                    'ip_address': row.ip_address,
                    'user_agent': row.user_agent,
                    'software_name': row.software_name,
                    'software_version': row.software_version,
                    'os_name': row.os_name,
                    'os_version': row.os_version,
                    'device_model': row.device_model,
                    'device_brand': row.device_brand,
                    'is_allowed': bool(row.is_allowed),
                    'first_seen': row.first_seen,
                    'last_seen': row.last_seen,
                    'access_count': row.access_count,
                    'created_at': row.created_at,
                    'updated_at': row.updated_at
                }
                for row in result
            ]
        except Exception as e:
            print(f"获取用户设备列表失败: {e}")
            return []
    
    def delete_device(self, device_id: int, user_id: int) -> bool:
        """删除设备"""
        try:
            # 验证设备所有权
            device = self.db.execute(text("""
                SELECT id FROM user_devices 
                WHERE id = :device_id AND user_id = :user_id
            """), {'device_id': device_id, 'user_id': user_id}).fetchone()
            
            if not device:
                return False
            
            # 删除设备
            self.db.execute(text("""
                DELETE FROM user_devices WHERE id = :device_id
            """), {'device_id': device_id})
            
            self.db.commit()
            return True
            
        except Exception as e:
            print(f"删除设备失败: {e}")
            self.db.rollback()
            return False
    
    def get_subscription_device_stats(self, subscription_id: int) -> Dict[str, int]:
        """获取订阅设备统计"""
        try:
            result = self.db.execute(text("""
                SELECT 
                    COUNT(*) as total_devices,
                    SUM(CASE WHEN is_allowed = 1 THEN 1 ELSE 0 END) as allowed_devices,
                    SUM(CASE WHEN is_allowed = 0 THEN 1 ELSE 0 END) as blocked_devices
                FROM user_devices 
                WHERE subscription_id = :subscription_id
            """), {'subscription_id': subscription_id}).fetchone()
            
            return {
                'total_devices': result.total_devices or 0,
                'allowed_devices': result.allowed_devices or 0,
                'blocked_devices': result.blocked_devices or 0
            }
        except Exception as e:
            print(f"获取订阅设备统计失败: {e}")
            return {'total_devices': 0, 'allowed_devices': 0, 'blocked_devices': 0}
