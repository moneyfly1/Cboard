from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from sqlalchemy import or_

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import get_password_hash, verify_password
from app.utils.email import send_verification_email, send_password_reset_email
from app.utils.security import create_access_token

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表"""
        return self.db.query(User).offset(skip).limit(limit).all()

    def create(self, user_in: UserCreate) -> User:
        """创建用户"""
        user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=user_in.hashed_password,
            is_active=user_in.is_active,
            is_verified=user_in.is_verified,
            is_admin=user_in.is_admin
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user_id: int, user_in: UserUpdate) -> Optional[User]:
        """更新用户"""
        user = self.get(user_id)
        if not user:
            return None
        
        update_data = user_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_password(self, user_id: int, new_password: str) -> bool:
        """更新用户密码"""
        from app.utils.security import get_password_hash
        
        user = self.get(user_id)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        return True

    def update_last_login(self, user_id: int) -> bool:
        """更新最后登录时间"""
        user = self.get(user_id)
        if not user:
            return False
        
        user.last_login = datetime.utcnow()
        self.db.commit()
        return True

    def verify_email(self, user_id: int) -> bool:
        """验证邮箱"""
        user = self.get(user_id)
        if not user:
            return False
        
        user.is_verified = True
        self.db.commit()
        return True

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """用户认证（用户名）"""
        from app.utils.security import verify_password
        
        user = self.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def authenticate_by_email(self, email: str, password: str) -> Optional[User]:
        """用户认证（邮箱）"""
        from app.utils.security import verify_password
        
        user = self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def send_verification_email(self, user_id: int) -> bool:
        """发送验证邮件"""
        from app.utils.email import send_verification_email
        
        user = self.get(user_id)
        if not user:
            return False
        
        return send_verification_email(user.email, user.username)

    def send_password_reset_email(self, email: str) -> bool:
        """发送密码重置邮件"""
        from app.utils.email import send_password_reset_email
        
        user = self.get_by_email(email)
        if not user:
            return False
        
        return send_password_reset_email(email, user.username)

    def delete(self, user_id: int) -> bool:
        """删除用户"""
        user = self.get(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True

    def count(self) -> int:
        """统计用户总数"""
        return self.db.query(User).count()

    def get_active_users(self, days: int = 30) -> List[User]:
        """获取活跃用户"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(User).filter(
            User.last_login >= cutoff_date
        ).all()

    def get_recent_users(self, days: int = 7) -> List[User]:
        """获取最近注册的用户"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(User).filter(
            User.created_at >= cutoff_date
        ).all()

    def count_active_users(self, days: int = 30) -> int:
        """统计活跃用户数量"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(User).filter(
            User.last_login >= cutoff_date
        ).count()

    def count_recent_users(self, days: int = 7) -> int:
        """统计最近注册用户数量"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(User).filter(
            User.created_at >= cutoff_date
        ).count()

    def count_users_since(self, start_date: datetime, end_date: Optional[datetime] = None) -> int:
        """统计指定时间段内注册的用户数量"""
        query = self.db.query(User).filter(User.created_at >= start_date)
        if end_date:
            query = query.filter(User.created_at < end_date)
        return query.count()

    def get_users_with_pagination(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """分页获取用户列表"""
        query = self.db.query(User)
        
        # 搜索条件
        if search:
            query = query.filter(
                or_(
                    User.username.contains(search),
                    User.email.contains(search)
                )
            )
        
        # 状态筛选
        if status == "active":
            query = query.filter(User.is_active == True)
        elif status == "inactive":
            query = query.filter(User.is_active == False)
        elif status == "verified":
            query = query.filter(User.is_verified == True)
        elif status == "unverified":
            query = query.filter(User.is_verified == False)
        
        total = query.count()
        users = query.offset(skip).limit(limit).order_by(User.created_at.desc()).all()
        
        return users, total

    def get_user_stats(self) -> dict:
        """获取用户统计信息"""
        total_users = self.count()
        active_users = self.count_active_users(30)
        recent_users = self.count_recent_users(7)
        
        # 今日注册用户
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_users = self.count_users_since(today_start)
        
        # 昨日注册用户
        yesterday_start = today_start - timedelta(days=1)
        yesterday_users = self.count_users_since(yesterday_start, today_start)
        
        return {
            "total": total_users,
            "active": active_users,
            "recent_7_days": recent_users,
            "today": today_users,
            "yesterday": yesterday_users
        } 