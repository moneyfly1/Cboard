from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ResponseBase
from app.utils.security import get_current_user, get_current_admin_user

router = APIRouter()

@router.get("/", response_model=ResponseBase)
def get_announcements(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取公告列表"""
    try:
        # 查询公告列表 - 包括系统公告和通知
        announcements = db.execute("""
            SELECT id, title, content, 'announcement' as type, created_at, updated_at
            FROM announcements 
            WHERE is_active = 1 
            ORDER BY created_at DESC 
            LIMIT 10
        """).fetchall()
        
        # 查询系统通知
        notifications = db.execute("""
            SELECT id, title, content, type, created_at, NULL as updated_at
            FROM notifications 
            WHERE type = 'system' OR type = 'announcement'
            ORDER BY created_at DESC 
            LIMIT 10
        """).fetchall()
        
        # 合并公告和通知
        all_items = []
        
        # 添加公告
        for announcement in announcements:
            all_items.append({
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content,
                "type": announcement.type,
                "created_at": announcement.created_at.isoformat() if announcement.created_at else None,
                "updated_at": announcement.updated_at.isoformat() if announcement.updated_at else None
            })
        
        # 添加通知
        for notification in notifications:
            all_items.append({
                "id": notification.id,
                "title": notification.title,
                "content": notification.content,
                "type": notification.type,
                "created_at": notification.created_at.isoformat() if notification.created_at else None,
                "updated_at": notification.updated_at.isoformat() if notification.updated_at else None
            })
        
        # 按创建时间排序
        all_items.sort(key=lambda x: x['created_at'] or '', reverse=True)
        
        return ResponseBase(data=all_items[:10])  # 返回最新的10条
        
    except Exception as e:
        print(f"获取公告列表失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取公告列表失败: {str(e)}"
        )

@router.get("/{announcement_id}", response_model=ResponseBase)
def get_announcement_detail(
    announcement_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取公告详情"""
    try:
        # 查询公告详情
        announcement = db.execute("""
            SELECT id, title, content, created_at, updated_at
            FROM announcements 
            WHERE id = :announcement_id AND is_active = 1
        """, {'announcement_id': announcement_id}).fetchone()
        
        if not announcement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="公告不存在"
            )
        
        announcement_detail = {
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content,
            "created_at": announcement.created_at.isoformat() if announcement.created_at else None,
            "updated_at": announcement.updated_at.isoformat() if announcement.updated_at else None
        }
        
        return ResponseBase(data=announcement_detail)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取公告详情失败: {str(e)}"
        )

# ==================== 管理员公告管理 ====================

@router.post("/admin/publish", response_model=ResponseBase)
def publish_announcement(
    announcement_data: dict,
    current_admin = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """发布公告（管理员）"""
    try:
        title = announcement_data.get('title', '')
        content = announcement_data.get('content', '')
        announcement_type = announcement_data.get('type', 'system')
        status = announcement_data.get('status', 'published')
        send_email = announcement_data.get('send_email', False)
        
        if not title or not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="标题和内容不能为空"
            )
        
        # 插入到notifications表（系统通知）
        db.execute("""
            INSERT INTO notifications (user_id, title, content, type, is_read, created_at)
            VALUES (NULL, :title, :content, :type, 0, datetime('now'))
        """, {
            'title': title,
            'content': content,
            'type': announcement_type
        })
        
        # 如果状态是发布，也插入到announcements表
        if status == 'published':
            db.execute("""
                INSERT INTO announcements (title, content, type, is_active, is_pinned, 
                                         target_users, created_by, created_at, updated_at)
                VALUES (:title, :content, :type, 1, 0, 'all', :created_by, datetime('now'), datetime('now'))
            """, {
                'title': title,
                'content': content,
                'type': announcement_type,
                'created_by': current_admin.id
            })
        
        db.commit()
        
        return ResponseBase(message="公告发布成功")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"发布公告失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发布公告失败: {str(e)}"
        )

@router.get("/admin/list", response_model=ResponseBase)
def get_admin_announcements(
    page: int = 1,
    size: int = 20,
    current_admin = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取公告列表（管理员）"""
    try:
        skip = (page - 1) * size
        
        # 查询公告列表
        announcements = db.execute("""
            SELECT id, title, content, type, is_active, created_at, updated_at
            FROM announcements 
            ORDER BY created_at DESC 
            LIMIT :limit OFFSET :offset
        """, {'limit': size, 'offset': skip}).fetchall()
        
        # 查询总数
        total = db.execute("SELECT COUNT(*) FROM announcements").fetchone()[0]
        
        announcement_list = []
        for announcement in announcements:
            announcement_list.append({
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content,
                "type": announcement.type,
                "is_active": announcement.is_active,
                "created_at": announcement.created_at.isoformat() if announcement.created_at else None,
                "updated_at": announcement.updated_at.isoformat() if announcement.updated_at else None
            })
        
        return ResponseBase(data={
            "announcements": announcement_list,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        })
        
    except Exception as e:
        print(f"获取公告列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取公告列表失败: {str(e)}"
        )
