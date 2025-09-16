"""
日志管理服务
"""
import logging
import logging.handlers
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings


class LogManager:
    """日志管理器"""
    
    def __init__(self):
        self.log_dir = Path("uploads/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志配置"""
        # 创建日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 应用日志
        app_logger = logging.getLogger('app')
        app_logger.setLevel(logging.INFO)
        
        # 文件处理器 - 按日期轮转
        app_handler = logging.handlers.TimedRotatingFileHandler(
            self.log_dir / 'app.log',
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        app_handler.setFormatter(formatter)
        app_logger.addHandler(app_handler)
        
        # 错误日志
        error_handler = logging.handlers.TimedRotatingFileHandler(
            self.log_dir / 'error.log',
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        app_logger.addHandler(error_handler)
        
        # 访问日志
        access_logger = logging.getLogger('access')
        access_logger.setLevel(logging.INFO)
        
        access_handler = logging.handlers.TimedRotatingFileHandler(
            self.log_dir / 'access.log',
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        access_handler.setFormatter(formatter)
        access_logger.addHandler(access_handler)
        
        # 安全日志
        security_logger = logging.getLogger('security')
        security_logger.setLevel(logging.WARNING)
        
        security_handler = logging.handlers.TimedRotatingFileHandler(
            self.log_dir / 'security.log',
            when='midnight',
            interval=1,
            backupCount=90,  # 保留90天
            encoding='utf-8'
        )
        security_handler.setFormatter(formatter)
        security_logger.addHandler(security_handler)
        
        # 控制台输出（仅开发环境）
        if settings.DEBUG:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            app_logger.addHandler(console_handler)
    
    def log_user_activity(self, user_id: int, activity: str, details: Dict = None):
        """记录用户活动"""
        logger = logging.getLogger('app')
        log_data = {
            "user_id": user_id,
            "activity": activity,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"USER_ACTIVITY: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_security_event(self, event_type: str, details: Dict = None):
        """记录安全事件"""
        logger = logging.getLogger('security')
        log_data = {
            "event_type": event_type,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        logger.warning(f"SECURITY_EVENT: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_api_access(self, method: str, path: str, status_code: int, 
                      response_time: float, user_id: Optional[int] = None,
                      ip_address: str = None):
        """记录API访问"""
        logger = logging.getLogger('access')
        log_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": response_time,
            "user_id": user_id,
            "ip_address": ip_address,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"API_ACCESS: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_error(self, error: Exception, context: Dict = None):
        """记录错误"""
        logger = logging.getLogger('app')
        log_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        logger.error(f"ERROR: {json.dumps(log_data, ensure_ascii=False)}", exc_info=True)
    
    def get_log_files(self) -> List[Dict]:
        """获取日志文件列表"""
        log_files = []
        
        for log_file in self.log_dir.iterdir():
            if log_file.is_file() and log_file.suffix == '.log':
                stat = log_file.stat()
                log_files.append({
                    "filename": log_file.name,
                    "path": str(log_file),
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return sorted(log_files, key=lambda x: x["modified_at"], reverse=True)
    
    def read_log_file(self, filename: str, lines: int = 100) -> List[str]:
        """读取日志文件"""
        log_path = self.log_dir / filename
        
        if not log_path.exists():
            return []
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if lines > 0 else all_lines
        except Exception as e:
            logging.getLogger('app').error(f"读取日志文件失败: {e}")
            return []
    
    def search_logs(self, query: str, log_type: str = "app", 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> List[Dict]:
        """搜索日志"""
        results = []
        
        # 确定要搜索的日志文件
        if log_type == "all":
            log_files = [f for f in self.log_dir.iterdir() if f.suffix == '.log']
        else:
            log_file = self.log_dir / f"{log_type}.log"
            log_files = [log_file] if log_file.exists() else []
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if query.lower() in line.lower():
                            # 解析时间戳
                            try:
                                timestamp_str = line.split(' - ')[0]
                                timestamp = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
                                
                                # 时间过滤
                                if start_date and timestamp < start_date:
                                    continue
                                if end_date and timestamp > end_date:
                                    continue
                                
                                results.append({
                                    "file": log_file.name,
                                    "line": line_num,
                                    "timestamp": timestamp.isoformat(),
                                    "content": line.strip()
                                })
                            except:
                                # 如果无法解析时间戳，仍然包含结果
                                results.append({
                                    "file": log_file.name,
                                    "line": line_num,
                                    "timestamp": None,
                                    "content": line.strip()
                                })
            except Exception as e:
                logging.getLogger('app').error(f"搜索日志文件失败 {log_file.name}: {e}")
        
        return sorted(results, key=lambda x: x["timestamp"] or "", reverse=True)
    
    def cleanup_old_logs(self, days: int = 30) -> Dict:
        """清理旧日志文件"""
        try:
            deleted_count = 0
            deleted_files = []
            
            # 如果days=0，清理所有日志文件
            if days == 0:
                cutoff_date = None
                for log_file in self.log_dir.iterdir():
                    if log_file.is_file() and log_file.suffix == '.log':
                        log_file.unlink()
                        deleted_count += 1
                        deleted_files.append(log_file.name)
            else:
                cutoff_date = datetime.now() - timedelta(days=days)
                for log_file in self.log_dir.iterdir():
                    if log_file.is_file() and log_file.suffix == '.log':
                        file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                        if file_time < cutoff_date:
                            log_file.unlink()
                            deleted_count += 1
                            deleted_files.append(log_file.name)
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "deleted_files": deleted_files,
                "cutoff_date": cutoff_date.isoformat() if cutoff_date else "所有日志"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_log_stats(self) -> Dict:
        """获取日志统计信息"""
        try:
            # 获取所有日志来计算统计，与筛选使用相同的数据源
            all_logs = self.get_recent_logs(limit=10000)  # 增加限制到10000条
            
            # 统计各级别日志数量
            total = len(all_logs)
            error = len([log for log in all_logs if log.get("level", "").upper() == "ERROR"])
            warning = len([log for log in all_logs if log.get("level", "").upper() == "WARNING"])
            info = len([log for log in all_logs if log.get("level", "").upper() == "INFO"])
            debug = len([log for log in all_logs if log.get("level", "").upper() == "DEBUG"])
            
            # 文件统计
            file_stats = {
                "total_files": 0,
                "total_size": 0,
                "file_types": {},
                "oldest_log": None,
                "newest_log": None
            }
            
            for log_file in self.log_dir.iterdir():
                if log_file.is_file() and log_file.suffix == '.log':
                    stat = log_file.stat()
                    file_stats["total_files"] += 1
                    file_stats["total_size"] += stat.st_size
                    
                    # 按类型统计
                    log_type = log_file.stem
                    if log_type not in file_stats["file_types"]:
                        file_stats["file_types"][log_type] = {"count": 0, "size": 0}
                    file_stats["file_types"][log_type]["count"] += 1
                    file_stats["file_types"][log_type]["size"] += stat.st_size
                    
                    # 时间范围
                    file_time = datetime.fromtimestamp(stat.st_mtime)
                    if not file_stats["newest_log"] or file_time > datetime.fromisoformat(file_stats["newest_log"]):
                        file_stats["newest_log"] = file_time.isoformat()
                    if not file_stats["oldest_log"] or file_time < datetime.fromisoformat(file_stats["oldest_log"]):
                        file_stats["oldest_log"] = file_time.isoformat()
            
            return {
                "total": total,
                "error": error,
                "warning": warning,
                "info": info,
                "debug": debug,
                "file_stats": file_stats,
                "debug_info": {
                    "files_read": len(list(self.log_dir.glob("*.log"))),
                    "total_files_available": len(list(self.log_dir.glob("*.log"))),
                    "logs_processed": len(all_logs)
                }
            }
        except Exception as e:
            return {
                "total": 0,
                "error": 0,
                "warning": 0,
                "info": 0,
                "debug": 0,
                "error": str(e)
            }
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """获取最近的日志记录"""
        try:
            results = []
            
            # 获取所有日志文件
            log_files = list(self.log_dir.glob("*.log"))
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 读取更多日志文件，确保能获取足够的日志
            files_to_read = min(len(log_files), 20)  # 最多读取20个日志文件
            
            for log_file in log_files[:files_to_read]:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    # 如果文件很大，只读取最后的部分行
                    if len(lines) > 1000:
                        recent_lines = lines[-1000:]  # 每个文件最多读取1000行
                    else:
                        recent_lines = lines
                    
                    for line in recent_lines:
                        if line.strip():
                            # 解析日志行
                            log_entry = self._parse_log_line(line.strip())
                            if log_entry:
                                results.append(log_entry)
                                
                except Exception as e:
                    logging.getLogger('app').error(f"读取日志文件失败 {log_file.name}: {e}")
            
            # 按时间排序并限制数量
            def sort_key(log_entry):
                timestamp = log_entry.get("timestamp", "")
                # 如果是字符串，尝试转换为datetime对象进行比较
                if isinstance(timestamp, str):
                    try:
                        from datetime import datetime
                        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        return datetime.min
                return timestamp
            
            results.sort(key=sort_key, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logging.getLogger('app').error(f"获取最近日志失败: {e}")
            return []
    
    def _parse_log_line(self, line: str) -> Optional[Dict]:
        """解析单行日志"""
        try:
            # 简单的日志解析，可以根据实际日志格式调整
            import re
            
            # 匹配常见的日志格式
            patterns = [
                # 格式: 2025-09-16 23:41:00,894 - app - INFO - 测试信息日志 1
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3} - (\w+) - (\w+) - (.+)',
                # 格式: 2024-01-15T10:30:00Z - INFO - module - message
                r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) - (\w+) - (\w+) - (.+)',
                # 格式: [2024-01-15 10:30:00] INFO: message
                r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+): (.+)',
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    if len(groups) >= 3:
                        timestamp = groups[0]
                        # 对于第一个模式：timestamp, module, level, message
                        if pattern.startswith(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3} - (\w+) - (\w+) - (.+)'):
                            module = groups[1]
                            level = groups[2]
                            message = groups[3]
                        else:
                            # 其他模式保持原有逻辑
                            level = groups[1] if len(groups) > 1 else "INFO"
                            module = groups[2] if len(groups) > 2 else "system"
                            message = groups[3] if len(groups) > 3 else line
                        
                        return {
                            "timestamp": timestamp,
                            "level": level,
                            "module": module,
                            "message": message,
                            "username": "system",
                            "ip_address": "127.0.0.1",
                            "user_agent": "System/1.0",
                            "details": ""
                        }
            
            # 如果无法解析，返回基本信息
            return {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "module": "system",
                "message": line[:100] + "..." if len(line) > 100 else line,
                "username": "system",
                "ip_address": "127.0.0.1",
                "user_agent": "System/1.0",
                "details": ""
            }
            
        except Exception as e:
            return None


# 全局日志管理器实例
log_manager = LogManager()


def get_logger(name: str = 'app') -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)
