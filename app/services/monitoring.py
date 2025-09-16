"""
系统监控服务
"""
import psutil
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.order import Order
from app.models.payment import Payment
import logging

logger = logging.getLogger(__name__)


class SystemMonitor:
    """系统监控类"""
    
    def __init__(self):
        self.metrics_history = []
        self.max_history = 1000  # 保留最近1000条记录
    
    def get_system_metrics(self) -> Dict:
        """获取系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_used = disk.used
            disk_total = disk.total
            
            # 网络IO
            network = psutil.net_io_counters()
            
            # 进程信息
            process = psutil.Process()
            process_memory = process.memory_info().rss
            process_cpu = process.cpu_percent()
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                "memory": {
                    "percent": memory_percent,
                    "used": memory_used,
                    "total": memory_total,
                    "available": memory.available
                },
                "disk": {
                    "percent": disk_percent,
                    "used": disk_used,
                    "total": disk_total,
                    "free": disk.free
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "process": {
                    "memory": process_memory,
                    "cpu_percent": process_cpu,
                    "pid": process.pid
                }
            }
            
            # 保存到历史记录
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return {}
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict]:
        """获取历史指标"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            metric for metric in self.metrics_history
            if datetime.fromisoformat(metric["timestamp"]) > cutoff_time
        ]
    
    def check_system_health(self) -> Dict:
        """检查系统健康状态"""
        metrics = self.get_system_metrics()
        
        if not metrics:
            return {
                "status": "error",
                "message": "无法获取系统指标"
            }
        
        warnings = []
        errors = []
        
        # CPU检查
        if metrics["cpu"]["percent"] > 90:
            errors.append(f"CPU使用率过高: {metrics['cpu']['percent']:.1f}%")
        elif metrics["cpu"]["percent"] > 80:
            warnings.append(f"CPU使用率较高: {metrics['cpu']['percent']:.1f}%")
        
        # 内存检查
        if metrics["memory"]["percent"] > 95:
            errors.append(f"内存使用率过高: {metrics['memory']['percent']:.1f}%")
        elif metrics["memory"]["percent"] > 85:
            warnings.append(f"内存使用率较高: {metrics['memory']['percent']:.1f}%")
        
        # 磁盘检查
        if metrics["disk"]["percent"] > 95:
            errors.append(f"磁盘使用率过高: {metrics['disk']['percent']:.1f}%")
        elif metrics["disk"]["percent"] > 85:
            warnings.append(f"磁盘使用率较高: {metrics['disk']['percent']:.1f}%")
        
        # 确定整体状态
        if errors:
            status = "error"
            message = "系统存在严重问题"
        elif warnings:
            status = "warning"
            message = "系统存在潜在问题"
        else:
            status = "healthy"
            message = "系统运行正常"
        
        return {
            "status": status,
            "message": message,
            "warnings": warnings,
            "errors": errors,
            "metrics": metrics
        }


class DatabaseMonitor:
    """数据库监控类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        try:
            # 用户统计
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            admin_users = self.db.query(User).filter(User.is_admin == True).count()
            
            # 订阅统计
            total_subscriptions = self.db.query(Subscription).count()
            active_subscriptions = self.db.query(Subscription).filter(Subscription.is_active == True).count()
            
            # 订单统计
            total_orders = self.db.query(Order).count()
            paid_orders = self.db.query(Order).filter(Order.status == "paid").count()
            
            # 支付统计
            total_payments = self.db.query(Payment).count()
            successful_payments = self.db.query(Payment).filter(Payment.status == "success").count()
            
            return {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "admins": admin_users
                },
                "subscriptions": {
                    "total": total_subscriptions,
                    "active": active_subscriptions
                },
                "orders": {
                    "total": total_orders,
                    "paid": paid_orders
                },
                "payments": {
                    "total": total_payments,
                    "successful": successful_payments
                }
            }
            
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
            return {}
    
    def check_database_health(self) -> Dict:
        """检查数据库健康状态"""
        try:
            # 测试数据库连接
            self.db.execute("SELECT 1")
            
            # 获取数据库大小（SQLite）
            result = self.db.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = result.fetchone()[0] if result else 0
            
            # 检查表数量
            result = self.db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = result.fetchone()[0] if result else 0
            
            return {
                "status": "healthy",
                "message": "数据库连接正常",
                "size_bytes": db_size,
                "table_count": table_count
            }
            
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return {
                "status": "error",
                "message": f"数据库连接失败: {str(e)}"
            }


class APIMonitor:
    """API监控类"""
    
    def __init__(self):
        self.request_counts = {}
        self.response_times = {}
        self.error_counts = {}
    
    def record_request(self, endpoint: str, method: str, response_time: float, status_code: int):
        """记录API请求"""
        key = f"{method}:{endpoint}"
        
        # 记录请求次数
        if key not in self.request_counts:
            self.request_counts[key] = 0
        self.request_counts[key] += 1
        
        # 记录响应时间
        if key not in self.response_times:
            self.response_times[key] = []
        self.response_times[key].append(response_time)
        
        # 只保留最近100次响应时间
        if len(self.response_times[key]) > 100:
            self.response_times[key] = self.response_times[key][-100:]
        
        # 记录错误
        if status_code >= 400:
            if key not in self.error_counts:
                self.error_counts[key] = 0
            self.error_counts[key] += 1
    
    def get_api_stats(self) -> Dict:
        """获取API统计信息"""
        stats = {}
        
        for key in self.request_counts:
            method, endpoint = key.split(":", 1)
            
            if endpoint not in stats:
                stats[endpoint] = {
                    "endpoint": endpoint,
                    "methods": {},
                    "total_requests": 0,
                    "total_errors": 0,
                    "avg_response_time": 0
                }
            
            # 计算平均响应时间
            avg_time = sum(self.response_times.get(key, [0])) / len(self.response_times.get(key, [1]))
            
            stats[endpoint]["methods"][method] = {
                "requests": self.request_counts[key],
                "errors": self.error_counts.get(key, 0),
                "avg_response_time": avg_time
            }
            
            stats[endpoint]["total_requests"] += self.request_counts[key]
            stats[endpoint]["total_errors"] += self.error_counts.get(key, 0)
        
        # 计算总体平均响应时间
        for endpoint in stats:
            total_time = 0
            total_count = 0
            for method_data in stats[endpoint]["methods"].values():
                total_time += method_data["avg_response_time"] * method_data["requests"]
                total_count += method_data["requests"]
            
            if total_count > 0:
                stats[endpoint]["avg_response_time"] = total_time / total_count
        
        return list(stats.values())


# 全局监控实例
system_monitor = SystemMonitor()
api_monitor = APIMonitor()


async def monitoring_middleware(request: Request, call_next):
    """监控中间件"""
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 计算响应时间
    response_time = time.time() - start_time
    
    # 记录API统计
    api_monitor.record_request(
        endpoint=request.url.path,
        method=request.method,
        response_time=response_time,
        status_code=response.status_code
    )
    
    # 添加监控头信息
    response.headers["X-Response-Time"] = f"{response_time:.3f}s"
    
    return response
