"""
配置更新管理API端点
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils.security import get_current_admin_user
from app.schemas.common import ResponseBase
from app.models.user import User
from app.services.config_update_service import ConfigUpdateService
import asyncio
import threading
import time
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/status", response_model=ResponseBase)
def get_config_update_status(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取配置更新状态"""
    try:
        service = ConfigUpdateService(db)
        status_info = service.get_status()
        return ResponseBase(data=status_info)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取状态失败: {str(e)}")

@router.post("/start", response_model=ResponseBase)
def start_config_update(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """启动配置更新"""
    try:
        service = ConfigUpdateService(db)
        
        # 检查是否已经在运行
        if service.is_running():
            return ResponseBase(success=False, message="配置更新任务已在运行中")
        
        # 启动后台任务
        background_tasks.add_task(service.run_update_task)
        
        return ResponseBase(message="配置更新任务已启动")
    except Exception as e:
        return ResponseBase(success=False, message=f"启动失败: {str(e)}")

@router.post("/stop", response_model=ResponseBase)
def stop_config_update(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """停止配置更新"""
    try:
        service = ConfigUpdateService(db)
        service.stop_update_task()
        return ResponseBase(message="配置更新任务已停止")
    except Exception as e:
        return ResponseBase(success=False, message=f"停止失败: {str(e)}")

@router.get("/logs", response_model=ResponseBase)
def get_update_logs(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取更新日志"""
    try:
        service = ConfigUpdateService(db)
        logs = service.get_logs(limit=limit)
        return ResponseBase(data=logs)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取日志失败: {str(e)}")

@router.get("/config", response_model=ResponseBase)
def get_update_config(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取更新配置"""
    try:
        service = ConfigUpdateService(db)
        config = service.get_config()
        return ResponseBase(data=config)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取配置失败: {str(e)}")

@router.put("/config", response_model=ResponseBase)
def update_config(
    config_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新配置"""
    try:
        service = ConfigUpdateService(db)
        service.update_config(config_data)
        return ResponseBase(message="配置已更新")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新配置失败: {str(e)}")

@router.get("/node-sources", response_model=ResponseBase)
def get_node_sources(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取节点源配置"""
    try:
        service = ConfigUpdateService(db)
        sources = service.get_node_sources()
        return ResponseBase(data=sources)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取节点源配置失败: {str(e)}")

@router.put("/node-sources", response_model=ResponseBase)
def update_node_sources(
    sources_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新节点源配置"""
    try:
        service = ConfigUpdateService(db)
        service.update_node_sources(sources_data)
        return ResponseBase(message="节点源配置已更新")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新节点源配置失败: {str(e)}")

@router.get("/filter-keywords", response_model=ResponseBase)
def get_filter_keywords(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取过滤关键词配置"""
    try:
        service = ConfigUpdateService(db)
        keywords = service.get_filter_keywords()
        return ResponseBase(data=keywords)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取过滤关键词配置失败: {str(e)}")

@router.put("/filter-keywords", response_model=ResponseBase)
def update_filter_keywords(
    keywords_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新过滤关键词配置"""
    try:
        service = ConfigUpdateService(db)
        service.update_filter_keywords(keywords_data)
        return ResponseBase(message="过滤关键词配置已更新")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新过滤关键词配置失败: {str(e)}")

@router.get("/files", response_model=ResponseBase)
def get_generated_files(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取生成的文件信息"""
    try:
        service = ConfigUpdateService(db)
        files = service.get_generated_files()
        return ResponseBase(data=files)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取文件信息失败: {str(e)}")

@router.post("/test", response_model=ResponseBase)
def test_config_update(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """测试配置更新（不保存文件）"""
    try:
        service = ConfigUpdateService(db)
        
        # 检查是否已经在运行
        if service.is_running():
            return ResponseBase(success=False, message="配置更新任务已在运行中")
        
        # 启动测试任务
        background_tasks.add_task(service.run_test_task)
        
        return ResponseBase(message="测试任务已启动")
    except Exception as e:
        return ResponseBase(success=False, message=f"启动测试失败: {str(e)}")

@router.get("/schedule", response_model=ResponseBase)
def get_schedule_config(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取定时任务配置"""
    try:
        service = ConfigUpdateService(db)
        schedule = service.get_schedule_config()
        return ResponseBase(data=schedule)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取定时配置失败: {str(e)}")

@router.put("/schedule", response_model=ResponseBase)
def update_schedule_config(
    schedule_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新定时任务配置"""
    try:
        service = ConfigUpdateService(db)
        service.update_schedule_config(schedule_data)
        return ResponseBase(message="定时配置已更新")
    except Exception as e:
        return ResponseBase(success=False, message=f"更新定时配置失败: {str(e)}")

@router.post("/schedule/start", response_model=ResponseBase)
def start_scheduled_task(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """启动定时任务"""
    try:
        service = ConfigUpdateService(db)
        service.start_scheduled_task()
        return ResponseBase(message="定时任务已启动")
    except Exception as e:
        return ResponseBase(success=False, message=f"启动定时任务失败: {str(e)}")

@router.post("/schedule/stop", response_model=ResponseBase)
def stop_scheduled_task(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """停止定时任务"""
    try:
        service = ConfigUpdateService(db)
        service.stop_scheduled_task()
        return ResponseBase(message="定时任务已停止")
    except Exception as e:
        return ResponseBase(success=False, message=f"停止定时任务失败: {str(e)}")

@router.post("/logs/clear", response_model=ResponseBase)
def clear_logs(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """手动清理日志"""
    try:
        service = ConfigUpdateService(db)
        service._cleanup_logs()
        return ResponseBase(message="日志已清理")
    except Exception as e:
        return ResponseBase(success=False, message=f"清理日志失败: {str(e)}")

@router.post("/logs/cleanup/start", response_model=ResponseBase)
def start_log_cleanup_timer(
    interval_data: dict = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """启动日志清理定时器"""
    try:
        service = ConfigUpdateService(db)
        
        # 如果提供了间隔时间，先设置间隔
        if interval_data and "interval_minutes" in interval_data:
            interval_minutes = interval_data["interval_minutes"]
            if isinstance(interval_minutes, int) and interval_minutes > 0:
                service.set_cleanup_interval(interval_minutes)
        
        service._start_log_cleanup_timer()
        interval = service.get_cleanup_interval()
        return ResponseBase(message=f"日志清理定时器已启动，间隔{interval}分钟")
    except Exception as e:
        return ResponseBase(success=False, message=f"启动日志清理定时器失败: {str(e)}")

@router.post("/logs/cleanup/stop", response_model=ResponseBase)
def stop_log_cleanup_timer(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """停止日志清理定时器"""
    try:
        service = ConfigUpdateService(db)
        service.stop_log_cleanup_timer()
        return ResponseBase(message="日志清理定时器已停止")
    except Exception as e:
        return ResponseBase(success=False, message=f"停止日志清理定时器失败: {str(e)}")

@router.put("/logs/cleanup/interval", response_model=ResponseBase)
def set_cleanup_interval(
    interval_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """设置日志清理间隔"""
    try:
        service = ConfigUpdateService(db)
        interval_minutes = interval_data.get("interval_minutes")
        if not interval_minutes or not isinstance(interval_minutes, int):
            return ResponseBase(success=False, message="请提供有效的间隔时间（分钟）")
        
        service.set_cleanup_interval(interval_minutes)
        return ResponseBase(message=f"日志清理间隔已设置为{interval_minutes}分钟")
    except Exception as e:
        return ResponseBase(success=False, message=f"设置清理间隔失败: {str(e)}")

@router.get("/logs/cleanup/interval", response_model=ResponseBase)
def get_cleanup_interval(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取日志清理间隔"""
    try:
        service = ConfigUpdateService(db)
        interval = service.get_cleanup_interval()
        return ResponseBase(data={"interval_minutes": interval})
    except Exception as e:
        return ResponseBase(success=False, message=f"获取清理间隔失败: {str(e)}")
