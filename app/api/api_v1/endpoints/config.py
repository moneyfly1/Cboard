from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
import os
import yaml
from pathlib import Path

from app.core.config import settings
from app.schemas.common import ResponseBase
from app.utils.security import get_current_admin_user

router = APIRouter()

# 配置文件路径
CONFIG_DIR = Path("uploads/config")
XR_CONFIG_PATH = CONFIG_DIR / "xr"
CLASH_CONFIG_PATH = CONFIG_DIR / "clash.yaml"
WORK_CONFIG_PATH = CONFIG_DIR / "work"

# 确保配置目录存在
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/admin/config-files", response_model=ResponseBase)
def get_config_files(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取配置文件列表"""
    config_files = []
    
    # 检查各个配置文件
    files_to_check = [
        {"name": "xr", "path": XR_CONFIG_PATH, "description": "xr 客户端配置文件"},
        {"name": "clash.yaml", "path": CLASH_CONFIG_PATH, "description": "Clash 配置文件"},
        {"name": "work", "path": WORK_CONFIG_PATH, "description": "Work 配置文件"}
    ]
    
    for file_info in files_to_check:
        path = file_info["path"]
        if path.exists():
            size = path.stat().st_size
            modified_time = path.stat().st_mtime
            config_files.append({
                "name": file_info["name"],
                "path": str(path),
                "description": file_info["description"],
                "size": size,
                "size_formatted": f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB",
                "modified_time": modified_time,
                "exists": True
            })
        else:
            config_files.append({
                "name": file_info["name"],
                "path": str(path),
                "description": file_info["description"],
                "size": 0,
                "size_formatted": "0 KB",
                "modified_time": None,
                "exists": False
            })
    
    return ResponseBase(data={"config_files": config_files})

@router.get("/admin/config-files/{file_name}", response_model=ResponseBase)
def get_config_file_content(
    file_name: str,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取配置文件内容"""
    file_paths = {
        "xr": XR_CONFIG_PATH,
        "clash.yaml": CLASH_CONFIG_PATH,
        "work": WORK_CONFIG_PATH
    }
    
    if file_name not in file_paths:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置文件不存在"
        )
    
    file_path = file_paths[file_name]
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置文件不存在"
        )
    
    try:
        content = file_path.read_text(encoding='utf-8')
        return ResponseBase(data={"content": content})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取配置文件失败: {str(e)}"
        )

@router.post("/admin/config-files/{file_name}", response_model=ResponseBase)
def save_config_file(
    file_name: str,
    content: str,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """保存配置文件"""
    file_paths = {
        "xr": XR_CONFIG_PATH,
        "clash.yaml": CLASH_CONFIG_PATH,
        "work": WORK_CONFIG_PATH
    }
    
    if file_name not in file_paths:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置文件不存在"
        )
    
    file_path = file_paths[file_name]
    
    # 内容长度限制
    max_sizes = {
        "xr": 1024 * 1024,  # 1MB
        "clash.yaml": 4 * 1024 * 1024,  # 4MB
        "work": 1024 * 1024  # 1MB
    }
    
    if len(content) > max_sizes[file_name]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件内容过大，最大允许 {max_sizes[file_name] / (1024*1024)} MB"
        )
    
    # 安全检查：禁止PHP代码
    if "<?php" in content.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="禁止写入PHP代码"
        )
    
    # YAML格式校验（仅对clash.yaml）
    if file_name == "clash.yaml":
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"YAML格式错误: {str(e)}"
            )
    
    try:
        # 备份原文件
        if file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + ".backup")
            file_path.rename(backup_path)
        
        # 写入新内容
        file_path.write_text(content, encoding='utf-8')
        
        return ResponseBase(message="配置文件保存成功")
    except Exception as e:
        # 恢复备份
        backup_path = file_path.with_suffix(file_path.suffix + ".backup")
        if backup_path.exists():
            backup_path.rename(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存配置文件失败: {str(e)}"
        )

@router.post("/admin/config-files/{file_name}/backup", response_model=ResponseBase)
def backup_config_file(
    file_name: str,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """备份配置文件"""
    file_paths = {
        "xr": XR_CONFIG_PATH,
        "clash.yaml": CLASH_CONFIG_PATH,
        "work": WORK_CONFIG_PATH
    }
    
    if file_name not in file_paths:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置文件不存在"
        )
    
    file_path = file_paths[file_name]
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置文件不存在"
        )
    
    try:
        backup_path = file_path.with_suffix(file_path.suffix + ".backup")
        import shutil
        shutil.copy2(file_path, backup_path)
        
        return ResponseBase(message="配置文件备份成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"备份配置文件失败: {str(e)}"
        )

@router.post("/admin/config-files/{file_name}/restore", response_model=ResponseBase)
def restore_config_file(
    file_name: str,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """恢复配置文件"""
    file_paths = {
        "xr": XR_CONFIG_PATH,
        "clash.yaml": CLASH_CONFIG_PATH,
        "work": WORK_CONFIG_PATH
    }
    
    if file_name not in file_paths:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置文件不存在"
        )
    
    file_path = file_paths[file_name]
    backup_path = file_path.with_suffix(file_path.suffix + ".backup")
    
    if not backup_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="备份文件不存在"
        )
    
    try:
        import shutil
        shutil.copy2(backup_path, file_path)
        
        return ResponseBase(message="配置文件恢复成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复配置文件失败: {str(e)}"
        )

@router.get("/admin/system-config", response_model=ResponseBase)
def get_system_config(
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取系统配置"""
    config = {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_prefix": settings.API_V1_STR,
        "cors_origins": settings.BACKEND_CORS_ORIGINS,
        "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "***",
        "smtp_server": settings.SMTP_SERVER,
        "smtp_port": settings.SMTP_PORT,
        "smtp_username": settings.SMTP_USERNAME,
        "upload_dir": settings.UPLOAD_DIR,
        "subscription_default_days": settings.SUBSCRIPTION_DEFAULT_DAYS,
        "subscription_default_device_limit": settings.SUBSCRIPTION_DEFAULT_DEVICE_LIMIT
    }
    
    return ResponseBase(data={"config": config})

@router.post("/admin/system-config", response_model=ResponseBase)
def update_system_config(
    config_data: dict,
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新系统配置"""
    # 这里应该实现配置文件的更新逻辑
    # 由于配置通常存储在环境变量或配置文件中，这里只是示例
    
    return ResponseBase(message="系统配置更新成功（需要重启服务生效）") 