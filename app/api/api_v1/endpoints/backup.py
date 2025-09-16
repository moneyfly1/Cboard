"""
备份管理API端点
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ResponseBase
from app.utils.security import get_current_admin_user
from app.services.backup import backup_service

router = APIRouter()


@router.post("/create/database", response_model=ResponseBase)
def create_database_backup(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建数据库备份"""
    try:
        result = backup_service.create_database_backup()
        if result["success"]:
            return ResponseBase(data=result, message="数据库备份创建成功")
        else:
            return ResponseBase(success=False, message=f"数据库备份失败: {result.get('error', '未知错误')}")
    except Exception as e:
        return ResponseBase(success=False, message=f"创建数据库备份失败: {str(e)}")


@router.post("/create/config", response_model=ResponseBase)
def create_config_backup(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建配置文件备份"""
    try:
        result = backup_service.create_config_backup()
        if result["success"]:
            return ResponseBase(data=result, message="配置文件备份创建成功")
        else:
            return ResponseBase(success=False, message=f"配置文件备份失败: {result.get('error', '未知错误')}")
    except Exception as e:
        return ResponseBase(success=False, message=f"创建配置文件备份失败: {str(e)}")


@router.post("/create/full", response_model=ResponseBase)
def create_full_backup(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """创建完整备份"""
    try:
        result = backup_service.create_full_backup()
        if result["success"]:
            return ResponseBase(data=result, message="完整备份创建成功")
        else:
            return ResponseBase(success=False, message=f"完整备份失败: {result.get('error', '未知错误')}")
    except Exception as e:
        return ResponseBase(success=False, message=f"创建完整备份失败: {str(e)}")


@router.get("/list", response_model=ResponseBase)
def list_backups(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """列出所有备份文件"""
    try:
        backups = backup_service.list_backups()
        return ResponseBase(data={
            "backups": backups,
            "count": len(backups)
        })
    except Exception as e:
        return ResponseBase(success=False, message=f"获取备份列表失败: {str(e)}")


@router.get("/stats", response_model=ResponseBase)
def get_backup_stats(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取备份统计信息"""
    try:
        stats = backup_service.get_backup_stats()
        return ResponseBase(data=stats)
    except Exception as e:
        return ResponseBase(success=False, message=f"获取备份统计失败: {str(e)}")


@router.post("/restore/database", response_model=ResponseBase)
def restore_database(
    backup_filename: str,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """恢复数据库"""
    try:
        result = backup_service.restore_database(backup_filename)
        if result["success"]:
            return ResponseBase(data=result, message="数据库恢复成功")
        else:
            return ResponseBase(success=False, message=f"数据库恢复失败: {result.get('error', '未知错误')}")
    except Exception as e:
        return ResponseBase(success=False, message=f"恢复数据库失败: {str(e)}")


@router.delete("/delete/{backup_filename}", response_model=ResponseBase)
def delete_backup(
    backup_filename: str,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除备份文件"""
    try:
        result = backup_service.delete_backup(backup_filename)
        if result["success"]:
            return ResponseBase(data=result, message="备份文件删除成功")
        else:
            return ResponseBase(success=False, message=f"删除备份文件失败: {result.get('error', '未知错误')}")
    except Exception as e:
        return ResponseBase(success=False, message=f"删除备份文件失败: {str(e)}")


@router.post("/cleanup", response_model=ResponseBase)
def cleanup_old_backups(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """清理旧备份文件"""
    try:
        result = backup_service.cleanup_old_backups()
        if result["success"]:
            return ResponseBase(data=result, message=result["message"])
        else:
            return ResponseBase(success=False, message=f"清理旧备份失败: {result.get('error', '未知错误')}")
    except Exception as e:
        return ResponseBase(success=False, message=f"清理旧备份失败: {str(e)}")


@router.get("/download/{backup_filename}")
def download_backup(
    backup_filename: str,
    current_admin = Depends(get_current_admin_user)
):
    """下载备份文件"""
    try:
        from fastapi.responses import FileResponse
        import os
        
        backup_path = backup_service.backup_dir / backup_filename
        
        if not backup_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="备份文件不存在"
            )
        
        return FileResponse(
            path=str(backup_path),
            filename=backup_filename,
            media_type='application/gzip'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载备份文件失败: {str(e)}"
        )
