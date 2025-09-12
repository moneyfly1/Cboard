"""
设备管理API端点
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.utils.security import get_current_admin_user
from app.schemas.common import ResponseBase
from app.services.device_manager import DeviceManager

router = APIRouter()

@router.get("/devices", response_model=ResponseBase)
def get_all_devices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    subscription_id: Optional[int] = Query(None),
    software_name: Optional[str] = Query(None),
    is_allowed: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取所有设备列表"""
    try:
        device_manager = DeviceManager(db)
        
        # 构建查询条件
        conditions = []
        params = {}
        
        if user_id:
            conditions.append("d.user_id = :user_id")
            params['user_id'] = user_id
        
        if subscription_id:
            conditions.append("d.subscription_id = :subscription_id")
            params['subscription_id'] = subscription_id
        
        if software_name:
            conditions.append("d.software_name LIKE :software_name")
            params['software_name'] = f"%{software_name}%"
        
        if is_allowed is not None:
            conditions.append("d.is_allowed = :is_allowed")
            params['is_allowed'] = is_allowed
        
        # 构建查询SQL
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 获取总数
        count_sql = f"""
            SELECT COUNT(*) 
            FROM devices d
            JOIN subscriptions s ON d.subscription_id = s.id
            JOIN users u ON d.user_id = u.id
            WHERE {where_clause}
        """
        total = db.execute(count_sql, params).scalar()
        
        # 获取分页数据
        offset = (page - 1) * size
        data_sql = f"""
            SELECT d.*, s.subscription_url, u.username, u.email
            FROM devices d
            JOIN subscriptions s ON d.subscription_id = s.id
            JOIN users u ON d.user_id = u.id
            WHERE {where_clause}
            ORDER BY d.last_seen DESC
            LIMIT :size OFFSET :offset
        """
        params.update({'size': size, 'offset': offset})
        
        result = db.execute(data_sql, params).fetchall()
        
        devices = []
        for row in result:
            devices.append({
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
            })
        
        return ResponseBase(
            data={
                'devices': devices,
                'total': total,
                'page': page,
                'size': size,
                'pages': (total + size - 1) // size
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设备列表失败: {str(e)}"
        )

@router.get("/devices/{device_id}", response_model=ResponseBase)
def get_device_detail(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取设备详情"""
    try:
        device_manager = DeviceManager(db)
        
        # 获取设备详情
        result = db.execute("""
            SELECT d.*, s.subscription_url, u.username, u.email
            FROM devices d
            JOIN subscriptions s ON d.subscription_id = s.id
            JOIN users u ON d.user_id = u.id
            WHERE d.id = :device_id
        """, {'device_id': device_id}).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
        
        device = {
            'id': result.id,
            'user_id': result.user_id,
            'subscription_id': result.subscription_id,
            'subscription_url': result.subscription_url,
            'username': result.username,
            'email': result.email,
            'device_ua': result.device_ua,
            'device_hash': result.device_hash,
            'ip_address': result.ip_address,
            'user_agent': result.user_agent,
            'software_name': result.software_name,
            'software_version': result.software_version,
            'os_name': result.os_name,
            'os_version': result.os_version,
            'device_model': result.device_model,
            'device_brand': result.device_brand,
            'is_allowed': bool(result.is_allowed),
            'first_seen': result.first_seen,
            'last_seen': result.last_seen,
            'access_count': result.access_count,
            'created_at': result.created_at,
            'updated_at': result.updated_at
        }
        
        return ResponseBase(data=device)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设备详情失败: {str(e)}"
        )

@router.put("/devices/{device_id}", response_model=ResponseBase)
def update_device(
    device_id: int,
    device_data: dict,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """更新设备状态"""
    try:
        device_manager = DeviceManager(db)
        
        # 获取设备信息
        device = db.execute("""
            SELECT id, user_id, subscription_id FROM devices WHERE id = :device_id
        """, {'device_id': device_id}).fetchone()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
        
        # 更新设备状态
        success = device_manager.update_device_status(device_id, device_data)
        
        if success:
            return ResponseBase(message="设备状态更新成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="设备状态更新失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新设备状态失败: {str(e)}"
        )

@router.delete("/devices/{device_id}", response_model=ResponseBase)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """删除设备"""
    try:
        device_manager = DeviceManager(db)
        
        # 获取设备信息
        device = db.execute("""
            SELECT id, user_id, subscription_id FROM devices WHERE id = :device_id
        """, {'device_id': device_id}).fetchone()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
        
        # 删除设备
        success = device_manager.delete_device(device_id, device.user_id)
        
        if success:
            return ResponseBase(message="设备删除成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="设备删除失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除设备失败: {str(e)}"
        )

@router.get("/users/{user_id}/devices", response_model=ResponseBase)
def get_user_devices(
    user_id: int,
    subscription_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取用户设备列表"""
    try:
        device_manager = DeviceManager(db)
        
        devices = device_manager.get_user_devices(user_id, subscription_id)
        
        return ResponseBase(data={'devices': devices})
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户设备列表失败: {str(e)}"
        )

@router.get("/user/{user_id}", response_model=ResponseBase)
def get_user_devices_alt(
    user_id: int,
    subscription_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取用户设备列表（兼容路径）"""
    try:
        device_manager = DeviceManager(db)
        
        devices = device_manager.get_user_devices(user_id, subscription_id)
        
        return ResponseBase(data=devices)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户设备列表失败: {str(e)}"
        )

@router.post("/user/{user_id}/clear", response_model=ResponseBase)
def clear_user_devices(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """清理用户所有设备"""
    try:
        device_manager = DeviceManager(db)
        
        # 获取用户的所有订阅
        subscriptions = db.execute("""
            SELECT id FROM subscriptions WHERE user_id = :user_id
        """, {'user_id': user_id}).fetchall()
        
        cleared_count = 0
        for sub in subscriptions:
            count = device_manager.clear_user_devices(sub.id)
            cleared_count += count
        
        return ResponseBase(
            message=f"成功清理 {cleared_count} 个设备",
            data={'cleared_count': cleared_count}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理用户设备失败: {str(e)}"
        )

@router.get("/subscriptions/{subscription_id}/devices", response_model=ResponseBase)
def get_subscription_devices(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取订阅设备列表"""
    try:
        device_manager = DeviceManager(db)
        
        # 获取订阅信息
        subscription = db.execute("""
            SELECT id, user_id FROM subscriptions WHERE id = :subscription_id
        """, {'subscription_id': subscription_id}).fetchone()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订阅不存在"
            )
        
        devices = device_manager.get_user_devices(subscription.user_id, subscription_id)
        stats = device_manager.get_subscription_device_stats(subscription_id)
        
        return ResponseBase(data={
            'devices': devices,
            'stats': stats
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取订阅设备列表失败: {str(e)}"
        )

@router.get("/software-rules", response_model=ResponseBase)
def get_software_rules(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取软件识别规则"""
    try:
        device_manager = DeviceManager(db)
        
        rules = device_manager.get_software_rules()
        
        return ResponseBase(data={'rules': rules})
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取软件识别规则失败: {str(e)}"
        )

@router.get("/access-logs", response_model=ResponseBase)
def get_access_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    subscription_id: Optional[int] = Query(None),
    access_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """获取访问日志"""
    try:
        # 构建查询条件
        conditions = []
        params = {}
        
        if subscription_id:
            conditions.append("l.subscription_id = :subscription_id")
            params['subscription_id'] = subscription_id
        
        if access_type:
            conditions.append("l.access_type = :access_type")
            params['access_type'] = access_type
        
        # 构建查询SQL
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 获取总数
        count_sql = f"""
            SELECT COUNT(*) 
            FROM subscription_access_logs l
            JOIN subscriptions s ON l.subscription_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE {where_clause}
        """
        total = db.execute(count_sql, params).scalar()
        
        # 获取分页数据
        offset = (page - 1) * size
        data_sql = f"""
            SELECT l.*, s.subscription_url, u.username, u.email
            FROM subscription_access_logs l
            JOIN subscriptions s ON l.subscription_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE {where_clause}
            ORDER BY l.access_time DESC
            LIMIT :size OFFSET :offset
        """
        params.update({'size': size, 'offset': offset})
        
        result = db.execute(data_sql, params).fetchall()
        
        logs = []
        for row in result:
            logs.append({
                'id': row.id,
                'subscription_id': row.subscription_id,
                'subscription_url': row.subscription_url,
                'username': row.username,
                'email': row.email,
                'device_id': row.device_id,
                'ip_address': row.ip_address,
                'user_agent': row.user_agent,
                'access_type': row.access_type,
                'response_status': row.response_status,
                'response_message': row.response_message,
                'access_time': row.access_time
            })
        
        return ResponseBase(
            data={
                'logs': logs,
                'total': total,
                'page': page,
                'size': size,
                'pages': (total + size - 1) // size
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取访问日志失败: {str(e)}"
        )

@router.post("/devices/{device_id}/allow", response_model=ResponseBase)
def allow_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """允许设备访问"""
    try:
        device_manager = DeviceManager(db)
        
        # 获取设备信息
        device = db.execute(text("""
            SELECT d.*, s.device_limit
            FROM devices d
            JOIN subscriptions s ON d.subscription_id = s.id
            WHERE d.id = :device_id
        """), {'device_id': device_id}).fetchone()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
        
        # 检查是否已达设备限制
        allowed_count = db.execute(text("""
            SELECT COUNT(*) FROM devices 
            WHERE subscription_id = :subscription_id AND is_allowed = 1
        """), {'subscription_id': device.subscription_id}).scalar()
        
        if allowed_count >= device.device_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"订阅设备数量已达上限（{device.device_limit}个）"
            )
        
        # 允许设备
        success = device_manager.update_device_status(device_id, {'is_allowed': True})
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="允许设备失败"
            )
        
        return ResponseBase(
            message="设备已允许访问",
            data={'device_id': device_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"允许设备失败: {str(e)}"
        )

@router.post("/devices/{device_id}/block", response_model=ResponseBase)
def block_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
) -> Any:
    """禁止设备访问"""
    try:
        device_manager = DeviceManager(db)
        
        # 禁止设备
        success = device_manager.update_device_status(device_id, {'is_allowed': False})
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="禁止设备失败"
            )
        
        return ResponseBase(
            message="设备已禁止访问",
            data={'device_id': device_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"禁止设备失败: {str(e)}"
        )
