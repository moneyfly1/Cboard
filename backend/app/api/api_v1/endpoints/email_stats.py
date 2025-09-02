from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.services.email import EmailService
from app.services.email_queue_processor import get_email_queue_processor
from app.utils.security import get_current_admin_user
from app.schemas.common import ResponseBase

router = APIRouter()

@router.get("/overview")
def get_email_overview_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取邮件概览统计"""
    email_service = EmailService(db)
    queue_processor = get_email_queue_processor()
    
    try:
        # 基础邮件统计
        basic_stats = email_service.get_email_stats()
        
        # 队列处理器统计
        queue_stats = queue_processor.get_queue_stats()
        
        # 合并统计信息
        overview = {
            "basic_stats": basic_stats,
            "queue_stats": queue_stats,
            "system_status": {
                "email_enabled": email_service.is_email_enabled(),
                "queue_processor_running": queue_processor.is_running,
                "smtp_configured": bool(email_service.get_smtp_config())
            }
        }
        
        return ResponseBase(data=overview)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取邮件概览统计失败: {str(e)}")

@router.get("/daily")
def get_daily_email_stats(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取每日邮件发送统计"""
    email_service = EmailService(db)
    
    try:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="天数必须在1-365之间")
        
        daily_stats = email_service.get_daily_email_stats(days)
        return ResponseBase(data=daily_stats)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取每日统计失败: {str(e)}")

@router.get("/by-type")
def get_email_stats_by_type(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """按邮件类型统计"""
    email_service = EmailService(db)
    
    try:
        type_stats = email_service.get_email_stats_by_type()
        return ResponseBase(data=type_stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取类型统计失败: {str(e)}")

@router.get("/queue/status")
def get_queue_processor_status(
    current_user = Depends(get_current_admin_user)
):
    """获取队列处理器状态"""
    queue_processor = get_email_queue_processor()
    
    try:
        status_info = {
            "is_running": queue_processor.is_running,
            "batch_size": queue_processor.batch_size,
            "processing_interval": queue_processor.processing_interval,
            "max_retries": queue_processor.max_retries,
            "retry_delays": queue_processor.retry_delays
        }
        
        return ResponseBase(data=status_info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取队列状态失败: {str(e)}")

@router.post("/queue/start")
def start_queue_processor(
    current_user = Depends(get_current_admin_user)
):
    """启动邮件队列处理器"""
    queue_processor = get_email_queue_processor()
    
    try:
        queue_processor.start_processing()
        return ResponseBase(message="邮件队列处理器已启动")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动队列处理器失败: {str(e)}")

@router.post("/queue/stop")
def stop_queue_processor(
    current_user = Depends(get_current_admin_user)
):
    """停止邮件队列处理器"""
    queue_processor = get_email_queue_processor()
    
    try:
        queue_processor.stop_processing()
        return ResponseBase(message="邮件队列处理器已停止")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止队列处理器失败: {str(e)}")

@router.post("/queue/pause")
def pause_queue_processor(
    duration_minutes: int = 0,
    current_user = Depends(get_current_admin_user)
):
    """暂停邮件队列处理器"""
    queue_processor = get_email_queue_processor()
    
    try:
        queue_processor.pause_processing(duration_minutes)
        message = f"邮件队列处理器已暂停"
        if duration_minutes > 0:
            message += f"，将在 {duration_minutes} 分钟后自动恢复"
        
        return ResponseBase(message=message)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"暂停队列处理器失败: {str(e)}")

@router.post("/queue/resume")
def resume_queue_processor(
    current_user = Depends(get_current_admin_user)
):
    """恢复邮件队列处理器"""
    queue_processor = get_email_queue_processor()
    
    try:
        queue_processor.resume_processing()
        return ResponseBase(message="邮件队列处理器已恢复")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复队列处理器失败: {str(e)}")

@router.post("/queue/retry-failed")
def retry_failed_emails(
    email_ids: List[int] = None,
    current_user = Depends(get_current_admin_user)
):
    """重试失败的邮件"""
    queue_processor = get_email_queue_processor()
    
    try:
        result = queue_processor.retry_failed_emails(email_ids)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        message = f"成功重试 {result['retried']} 封失败邮件"
        if email_ids:
            message += f"（共 {len(email_ids)} 封）"
        else:
            message += f"（共 {result['total_failed']} 封）"
        
        return ResponseBase(message=message, data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重试失败邮件失败: {str(e)}")

@router.get("/queue/stats")
def get_queue_detailed_stats(
    current_user = Depends(get_current_admin_user)
):
    """获取队列详细统计"""
    queue_processor = get_email_queue_processor()
    
    try:
        queue_stats = queue_processor.get_queue_stats()
        return ResponseBase(data=queue_stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取队列统计失败: {str(e)}")

@router.post("/cleanup")
def cleanup_old_emails(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """清理旧邮件"""
    email_service = EmailService(db)
    
    try:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="天数必须在1-365之间")
        
        deleted_count = email_service.cleanup_old_emails(days)
        return ResponseBase(message=f"成功清理 {deleted_count} 封旧邮件")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理旧邮件失败: {str(e)}")

@router.get("/smtp/config")
def get_smtp_config(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取SMTP配置信息（隐藏敏感信息）"""
    email_service = EmailService(db)
    
    try:
        smtp_config = email_service.get_smtp_config()
        
        # 隐藏敏感信息
        safe_config = {
            "host": smtp_config.get("host"),
            "port": smtp_config.get("port"),
            "encryption": smtp_config.get("encryption"),
            "from_name": smtp_config.get("from_name"),
            "from_email": smtp_config.get("from_email"),
            "username": smtp_config.get("username", "")[:3] + "***" if smtp_config.get("username") else "",
            "password": "***" if smtp_config.get("password") else "",
            "enabled": email_service.is_email_enabled()
        }
        
        return ResponseBase(data=safe_config)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取SMTP配置失败: {str(e)}")

@router.get("/performance")
def get_email_performance_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """获取邮件性能统计"""
    email_service = EmailService(db)
    queue_processor = get_email_queue_processor()
    
    try:
        # 基础统计
        basic_stats = email_service.get_email_stats()
        
        # 队列统计
        queue_stats = queue_processor.get_queue_stats()
        
        # 计算性能指标
        total_emails = basic_stats["total"]
        success_rate = 0
        if total_emails > 0:
            success_rate = (basic_stats["sent"] / total_emails) * 100
        
        performance_stats = {
            "total_emails": total_emails,
            "success_rate": round(success_rate, 2),
            "pending_rate": round((basic_stats["pending"] / total_emails) * 100, 2) if total_emails > 0 else 0,
            "failure_rate": round((basic_stats["failed"] / total_emails) * 100, 2) if total_emails > 0 else 0,
            "average_retry_count": queue_stats.get("retry_distribution", {}),
            "queue_health": "healthy" if queue_stats.get("pending", 0) < 100 else "warning" if queue_stats.get("pending", 0) < 500 else "critical"
        }
        
        return ResponseBase(data=performance_stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")
