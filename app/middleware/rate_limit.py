"""
请求频率限制中间件
"""
import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from collections import defaultdict, deque
import asyncio
from app.core.config import settings


class RateLimiter:
    def __init__(self):
        # 存储每个IP的请求记录
        self.requests: Dict[str, deque] = defaultdict(deque)
        # 清理过期记录的锁
        self.cleanup_lock = asyncio.Lock()
    
    async def is_allowed(self, ip: str, limit: int = 100, window: int = 60) -> bool:
        """
        检查IP是否允许请求
        
        Args:
            ip: 客户端IP地址
            limit: 时间窗口内允许的最大请求数
            window: 时间窗口（秒）
        
        Returns:
            bool: 是否允许请求
        """
        current_time = time.time()
        
        # 获取该IP的请求记录
        ip_requests = self.requests[ip]
        
        # 清理过期的请求记录
        while ip_requests and ip_requests[0] <= current_time - window:
            ip_requests.popleft()
        
        # 检查是否超过限制
        if len(ip_requests) >= limit:
            return False
        
        # 记录当前请求
        ip_requests.append(current_time)
        return True
    
    async def cleanup_expired_records(self):
        """清理过期的请求记录"""
        async with self.cleanup_lock:
            current_time = time.time()
            expired_ips = []
            
            for ip, requests in self.requests.items():
                # 清理过期记录
                while requests and requests[0] <= current_time - 3600:  # 1小时过期
                    requests.popleft()
                
                # 如果没有请求记录，标记为过期
                if not requests:
                    expired_ips.append(ip)
            
            # 删除过期的IP记录
            for ip in expired_ips:
                del self.requests[ip]


# 全局速率限制器实例
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """
    速率限制中间件
    """
    # 获取客户端IP
    client_ip = request.client.host
    
    # 检查X-Forwarded-For头（用于代理环境）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    # 检查X-Real-IP头
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        client_ip = real_ip
    
    # 根据路径设置不同的限制
    path = request.url.path
    
    # 登录接口更严格的限制
    if path in ["/api/v1/auth/login", "/api/v1/auth/register"]:
        limit = 10  # 每分钟10次
        window = 60
    # 管理员接口限制
    elif path.startswith("/api/v1/admin"):
        limit = 200  # 每分钟200次
        window = 60
    # 普通API限制
    elif path.startswith("/api/v1"):
        limit = 100  # 每分钟100次
        window = 60
    # 静态资源不限制
    elif path.startswith("/static") or path.startswith("/uploads"):
        return await call_next(request)
    else:
        limit = 50  # 其他请求每分钟50次
        window = 60
    
    # 检查速率限制
    if not await rate_limiter.is_allowed(client_ip, limit, window):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "success": False,
                "message": f"请求过于频繁，请稍后再试。限制：{limit}次/{window}秒",
                "code": 429
            }
        )
    
    # 定期清理过期记录（每1000次请求清理一次）
    if len(rate_limiter.requests) > 1000:
        await rate_limiter.cleanup_expired_records()
    
    # 继续处理请求
    response = await call_next(request)
    
    # 添加速率限制头信息
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Window"] = str(window)
    
    return response


class IPWhitelist:
    """IP白名单管理"""
    
    def __init__(self):
        self.whitelist = set()
        self.blacklist = set()
    
    def add_to_whitelist(self, ip: str):
        """添加到白名单"""
        self.whitelist.add(ip)
    
    def add_to_blacklist(self, ip: str):
        """添加到黑名单"""
        self.blacklist.add(ip)
    
    def is_allowed(self, ip: str) -> bool:
        """检查IP是否被允许"""
        if ip in self.blacklist:
            return False
        if self.whitelist and ip not in self.whitelist:
            return False
        return True


# 全局IP白名单实例
ip_manager = IPWhitelist()


async def ip_filter_middleware(request: Request, call_next):
    """
    IP过滤中间件
    """
    # 获取客户端IP
    client_ip = request.client.host
    
    # 检查X-Forwarded-For头
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    # 检查X-Real-IP头
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        client_ip = real_ip
    
    # 检查IP是否被允许
    if not ip_manager.is_allowed(client_ip):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "message": "访问被拒绝",
                "code": 403
            }
        )
    
    return await call_next(request)
