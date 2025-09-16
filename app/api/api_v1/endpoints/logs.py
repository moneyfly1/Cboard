"""
日志管理API端点
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.schemas.common import ResponseBase
from app.utils.security import get_current_admin_user
from app.services.logging import log_manager

router = APIRouter()


@router.get("/files", response_model=ResponseBase)
def get_log_files(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取日志文件列表"""
    try:
        log_files = log_manager.get_log_files()
        return ResponseBase(data={
            "log_files": log_files,
            "count": len(log_files)
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取日志文件列表失败: {str(e)}")


@router.get("/read/{filename}", response_model=ResponseBase)
def read_log_file(
    filename: str,
    lines: int = Query(100, ge=1, le=1000),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """读取日志文件内容"""
    try:
        # 安全检查：只允许读取.log文件
        if not filename.endswith('.log'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能读取.log文件"
            )
        
        log_content = log_manager.read_log_file(filename, lines)
        return ResponseBase(data={
            "filename": filename,
            "lines": len(log_content),
            "content": log_content
        })
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"读取日志文件失败: {str(e)}")


@router.get("/search", response_model=ResponseBase)
def search_logs(
    query: str = Query(..., min_length=1),
    log_type: str = Query("app", regex="^(app|error|access|security|all)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """搜索日志"""
    try:
        # 解析日期参数
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="开始日期格式错误，请使用ISO格式"
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="结束日期格式错误，请使用ISO格式"
                )
        
        results = log_manager.search_logs(query, log_type, start_dt, end_dt)
        
        return ResponseBase(data={
            "query": query,
            "log_type": log_type,
            "results": results,
            "count": len(results)
        })
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"搜索日志失败: {str(e)}")


@router.get("/stats", response_model=ResponseBase)
def get_log_stats(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取日志统计信息"""
    try:
        stats = log_manager.get_log_stats()
        return ResponseBase(data=stats)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取日志统计失败: {str(e)}")


@router.post("/cleanup", response_model=ResponseBase)
def cleanup_old_logs(
    days: int = Query(30, ge=1, le=365),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """清理旧日志文件"""
    try:
        result = log_manager.cleanup_old_logs(days)
        if result["success"]:
            return ResponseBase(data=result, message=f"清理完成，删除了 {result['deleted_count']} 个旧日志文件")
        else:
            return ResponseBase(success=False, message=f"清理失败: {result.get('error', '未知错误')}")
    except Exception as e:
        return ResponseBase(success=False, message=f"清理旧日志失败: {str(e)}")


@router.delete("/delete/{filename}", response_model=ResponseBase)
def delete_log_file(
    filename: str,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除日志文件"""
    try:
        # 安全检查：只允许删除.log文件
        if not filename.endswith('.log'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能删除.log文件"
            )
        
        from pathlib import Path
        log_path = log_manager.log_dir / filename
        
        if not log_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="日志文件不存在"
            )
        
        log_path.unlink()
        
        return ResponseBase(message="日志文件删除成功")
    except HTTPException:
        raise
    except Exception as e:
        return ResponseBase(success=False, message=f"删除日志文件失败: {str(e)}")


@router.get("/download/{filename}")
def download_log_file(
    filename: str,
    current_admin = Depends(get_current_admin_user)
):
    """下载日志文件"""
    try:
        from fastapi.responses import FileResponse
        
        # 安全检查：只允许下载.log文件
        if not filename.endswith('.log'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能下载.log文件"
            )
        
        log_path = log_manager.log_dir / filename
        
        if not log_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="日志文件不存在"
            )
        
        return FileResponse(
            path=str(log_path),
            filename=filename,
            media_type='text/plain'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载日志文件失败: {str(e)}"
        )


@router.get("/realtime/{log_type}", response_model=ResponseBase)
def get_realtime_logs(
    log_type: str = Path(..., regex="^(app|error|access|security)$"),
    lines: int = Query(50, ge=1, le=200),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取实时日志"""
    try:
        filename = f"{log_type}.log"
        log_content = log_manager.read_log_file(filename, lines)
        
        return ResponseBase(data={
            "log_type": log_type,
            "lines": len(log_content),
            "content": log_content,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取实时日志失败: {str(e)}")


@router.get("/errors/recent", response_model=ResponseBase)
def get_recent_errors(
    hours: int = Query(24, ge=1, le=168),  # 最多7天
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取最近的错误日志"""
    try:
        start_date = datetime.now() - timedelta(hours=hours)
        results = log_manager.search_logs("ERROR", "error", start_date)
        
        return ResponseBase(data={
            "errors": results,
            "count": len(results),
            "hours": hours,
            "start_date": start_date.isoformat()
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取最近错误日志失败: {str(e)}")


@router.get("/security/recent", response_model=ResponseBase)
def get_recent_security_events(
    hours: int = Query(24, ge=1, le=168),  # 最多7天
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取最近的安全事件"""
    try:
        start_date = datetime.now() - timedelta(hours=hours)
        results = log_manager.search_logs("SECURITY_EVENT", "security", start_date)
        
        return ResponseBase(data={
            "security_events": results,
            "count": len(results),
            "hours": hours,
            "start_date": start_date.isoformat()
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取最近安全事件失败: {str(e)}")
