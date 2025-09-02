from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from sqlalchemy import or_

from app.models.user import User
from app.models.user_activity import UserActivity, LoginHistory, SubscriptionReset
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
        # 对密码进行哈希处理
        hashed_password = get_password_hash(user_in.password)
        
        user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,  # 临时设置为已验证，跳过邮箱验证
            is_admin=False
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # 自动创建默认订阅
        try:
            from app.services.subscription import SubscriptionService
            from app.schemas.subscription import SubscriptionCreate
            from datetime import datetime, timedelta
            
            subscription_service = SubscriptionService(self.db)
            
            # 创建默认订阅（30天试用期）
            default_subscription = SubscriptionCreate(
                user_id=user.id,
                package_name="试用套餐",
                duration_days=30,
                device_limit=3,
                status="active",
                expire_time=datetime.utcnow() + timedelta(days=30)
            )
            
            subscription_service.create(default_subscription)
            
        except Exception as e:
            # 如果创建订阅失败，记录错误但不影响用户创建
            print(f"创建默认订阅失败: {e}")
        
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
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
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

    # 新增方法：获取用户操作历史
    def get_user_activities(self, user_id: int, limit: int = 50) -> List[UserActivity]:
        """获取用户操作历史"""
        return self.db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).order_by(UserActivity.created_at.desc()).limit(limit).all()

    # 新增方法：获取用户登录历史
    def get_login_history(self, user_id: int, limit: int = 50) -> List[LoginHistory]:
        """获取用户登录历史"""
        return self.db.query(LoginHistory).filter(
            LoginHistory.user_id == user_id
        ).order_by(LoginHistory.login_time.desc()).limit(limit).all()

    # 新增方法：获取用户订阅重置记录
    def get_subscription_resets(self, user_id: int, limit: int = 50) -> List[SubscriptionReset]:
        """获取用户订阅重置记录"""
        return self.db.query(SubscriptionReset).filter(
            SubscriptionReset.user_id == user_id
        ).order_by(SubscriptionReset.created_at.desc()).limit(limit).all()

    # 新增方法：记录用户活动
    def log_user_activity(
        self, 
        user_id: int, 
        activity_type: str, 
        description: str = None,
        ip_address: str = None,
        user_agent: str = None,
        location: str = None,
        metadata: dict = None
    ) -> UserActivity:
        """记录用户操作活动"""
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            location=location,
            metadata=metadata
        )
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    # 新增方法：记录登录历史
    def log_login(
        self,
        user_id: int,
        ip_address: str = None,
        user_agent: str = None,
        location: str = None,
        device_fingerprint: str = None,
        login_status: str = "success",
        failure_reason: str = None
    ) -> LoginHistory:
        """记录用户登录历史"""
        login_record = LoginHistory(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            location=location,
            device_fingerprint=device_fingerprint,
            login_status=login_status,
            failure_reason=failure_reason
        )
        self.db.add(login_record)
        self.db.commit()
        self.db.refresh(login_record)
        return login_record

    # 新增方法：记录订阅重置
    def log_subscription_reset(
        self,
        user_id: int,
        subscription_id: int,
        reset_type: str,
        reason: str = None,
        old_subscription_url: str = None,
        new_subscription_url: str = None,
        device_count_before: int = 0,
        device_count_after: int = 0,
        reset_by: str = "user"
    ) -> SubscriptionReset:
        """记录订阅重置操作"""
        reset_record = SubscriptionReset(
            user_id=user_id,
            subscription_id=subscription_id,
            reset_type=reset_type,
            reason=reason,
            old_subscription_url=old_subscription_url,
            new_subscription_url=new_subscription_url,
            device_count_before=device_count_before,
            device_count_after=device_count_after,
            reset_by=reset_by
        )
        self.db.add(reset_record)
        self.db.commit()
        self.db.refresh(reset_record)
        return reset_record 