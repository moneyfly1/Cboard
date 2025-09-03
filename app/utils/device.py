import hashlib
import re
from typing import Optional
from user_agents import parse

def generate_device_fingerprint(user_agent: str, ip_address: Optional[str] = None) -> str:
    """生成设备指纹"""
    # 解析User-Agent
    ua = parse(user_agent)
    
    # 提取设备信息
    device_info = {
        'browser': ua.browser.family,
        'browser_version': ua.browser.version_string,
        'os': ua.os.family,
        'os_version': ua.os.version_string,
        'device': ua.device.family,
        'ip': ip_address or 'unknown'
    }
    
    # 生成指纹字符串
    fingerprint_str = f"{device_info['browser']}_{device_info['browser_version']}_{device_info['os']}_{device_info['os_version']}_{device_info['device']}_{device_info['ip']}"
    
    # 计算哈希值
    fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    return fingerprint

def detect_device_type(user_agent: str) -> str:
    """检测设备类型"""
    ua = parse(user_agent)
    
    if ua.is_mobile:
        return "mobile"
    elif ua.is_tablet:
        return "tablet"
    else:
        return "desktop"

def extract_device_name(user_agent: str) -> str:
    """提取设备名称"""
    ua = parse(user_agent)
    
    if ua.is_mobile:
        if ua.device.family != "Other":
            return f"{ua.device.family} {ua.os.family}"
        else:
            return f"Mobile {ua.os.family}"
    elif ua.is_tablet:
        if ua.device.family != "Other":
            return f"{ua.device.family} {ua.os.family}"
        else:
            return f"Tablet {ua.os.family}"
    else:
        return f"Desktop {ua.os.family}"

def is_valid_ip_address(ip: str) -> bool:
    """验证IP地址格式"""
    # IPv4正则表达式
    ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    
    # IPv6正则表达式（简化版）
    ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    
    return bool(re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip))

def sanitize_user_agent(user_agent: str) -> str:
    """清理User-Agent字符串"""
    if not user_agent:
        return "Unknown"
    
    # 移除可能的恶意字符
    sanitized = re.sub(r'[^\w\s\-\.\/\(\)]', '', user_agent)
    
    # 限制长度
    if len(sanitized) > 500:
        sanitized = sanitized[:500]
    
    return sanitized or "Unknown" 