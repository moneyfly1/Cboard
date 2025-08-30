from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.subscription import Subscription, Device
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from app.utils.security import generate_subscription_key

class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, subscription_id: int) -> Optional[Subscription]:
        """根据ID获取订阅"""
        return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()

    def get_by_user_id(self, user_id: int) -> Optional[Subscription]:
        """根据用户ID获取订阅"""
        return self.db.query(Subscription).filter(Subscription.user_id == user_id).first()

    def create(self, subscription_in: SubscriptionCreate) -> Subscription:
        """创建订阅"""
        subscription = Subscription(
            user_id=subscription_in.user_id,
            url=subscription_in.url,
            device_limit=subscription_in.device_limit,
            expire_time=subscription_in.expire_time
        )
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def update(self, subscription_id: int, subscription_in: SubscriptionUpdate) -> Optional[Subscription]:
        """更新订阅"""
        subscription = self.get(subscription_id)
        if not subscription:
            return None
        
        update_data = subscription_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(subscription, field, value)
        
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def update_subscription_key(self, subscription_id: int) -> bool:
        """更新订阅密钥"""
        subscription = self.get(subscription_id)
        if not subscription:
            return False
        
        new_key = generate_subscription_key()
        subscription.url = new_key
        self.db.commit()
        return True

    def delete(self, subscription_id: int) -> bool:
        """删除订阅"""
        subscription = self.get(subscription_id)
        if not subscription:
            return False
        
        self.db.delete(subscription)
        self.db.commit()
        return True

    def get_devices_by_subscription_id(self, subscription_id: int) -> List[Device]:
        """获取订阅的所有设备"""
        return self.db.query(Device).filter(Device.subscription_id == subscription_id).all()

    def get_device(self, device_id: int) -> Optional[Device]:
        """根据ID获取设备"""
        return self.db.query(Device).filter(Device.id == device_id).first()

    def record_device_access(self, subscription_id: int, device_info: dict) -> Device:
        """记录设备访问"""
        # 检查设备是否已存在
        existing_device = self.db.query(Device).filter(
            and_(
                Device.subscription_id == subscription_id,
                Device.fingerprint == device_info["fingerprint"]
            )
        ).first()
        
        if existing_device:
            # 更新现有设备信息
            existing_device.name = device_info.get("name", existing_device.name)
            existing_device.ip = device_info.get("ip", existing_device.ip)
            existing_device.user_agent = device_info.get("user_agent", existing_device.user_agent)
            existing_device.last_access = datetime.utcnow()
            self.db.commit()
            return existing_device
        else:
            # 创建新设备记录
            device = Device(
                subscription_id=subscription_id,
                fingerprint=device_info["fingerprint"],
                name=device_info.get("name", "未知设备"),
                type=device_info.get("type", "unknown"),
                ip=device_info.get("ip", ""),
                user_agent=device_info.get("user_agent", ""),
                last_access=datetime.utcnow()
            )
            
            self.db.add(device)
            self.db.commit()
            self.db.refresh(device)
            return device

    def delete_device(self, device_id: int) -> bool:
        """删除设备"""
        device = self.get_device(device_id)
        if not device:
            return False
        
        self.db.delete(device)
        self.db.commit()
        return True

    def delete_devices_by_subscription_id(self, subscription_id: int) -> bool:
        """删除订阅的所有设备"""
        devices = self.get_devices_by_subscription_id(subscription_id)
        for device in devices:
            self.db.delete(device)
        self.db.commit()
        return True

    def get_device_count(self, subscription_id: int) -> int:
        """获取设备数量"""
        return self.db.query(Device).filter(Device.subscription_id == subscription_id).count()

    def is_device_limit_reached(self, subscription_id: int) -> bool:
        """检查是否达到设备限制"""
        subscription = self.get(subscription_id)
        if not subscription:
            return True
        
        device_count = self.get_device_count(subscription_id)
        return device_count >= subscription.device_limit

    def get_expiring_subscriptions(self, days: int = 7) -> List[Subscription]:
        """获取即将过期的订阅"""
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        return self.db.query(Subscription).filter(
            and_(
                Subscription.expire_time <= cutoff_date,
                Subscription.expire_time > datetime.utcnow()
            )
        ).all()

    def get_expired_subscriptions(self) -> List[Subscription]:
        """获取已过期的订阅"""
        return self.db.query(Subscription).filter(
            Subscription.expire_time <= datetime.utcnow()
        ).all()

    def extend_subscription(self, subscription_id: int, days: int) -> bool:
        """延长订阅"""
        subscription = self.get(subscription_id)
        if not subscription:
            return False
        
        if subscription.expire_time and subscription.expire_time > datetime.utcnow():
            # 从当前到期时间延长
            subscription.expire_time = subscription.expire_time + timedelta(days=days)
        else:
            # 从当前时间开始计算
            subscription.expire_time = datetime.utcnow() + timedelta(days=days)
        
        self.db.commit()
        return True

    def get_subscription_stats(self) -> dict:
        """获取订阅统计信息"""
        total_subscriptions = self.count()
        active_subscriptions = self.count_active()
        expired_subscriptions = self.count_expired()
        expiring_soon = self.count_expiring_soon(7)
        
        return {
            "total": total_subscriptions,
            "active": active_subscriptions,
            "expired": expired_subscriptions,
            "expiring_soon": expiring_soon
        }

    def count(self) -> int:
        """统计订阅总数"""
        return self.db.query(Subscription).count()

    def count_active(self) -> int:
        """统计活跃订阅数量"""
        return self.db.query(Subscription).filter(
            Subscription.expire_time > datetime.utcnow()
        ).count()

    def count_expired(self) -> int:
        """统计过期订阅数量"""
        return self.db.query(Subscription).filter(
            Subscription.expire_time <= datetime.utcnow()
        ).count()

    def count_expiring_soon(self, days: int = 7) -> int:
        """统计即将过期的订阅数量"""
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        return self.db.query(Subscription).filter(
            and_(
                Subscription.expire_time <= cutoff_date,
                Subscription.expire_time > datetime.utcnow()
            )
        ).count()

    def count_total_devices(self) -> int:
        """统计总设备数量"""
        return self.db.query(Device).count()

    def count_online_devices(self) -> int:
        """统计在线设备数量（24小时内访问过）"""
        cutoff_date = datetime.utcnow() - timedelta(hours=24)
        return self.db.query(Device).filter(
            Device.last_access >= cutoff_date
        ).count()

    def reset_subscription(self, subscription_id: int) -> bool:
        """重置订阅"""
        subscription = self.get(subscription_id)
        if not subscription:
            return False
        
        # 生成新的订阅密钥
        new_key = generate_subscription_key()
        subscription.url = new_key
        
        # 删除所有设备
        self.delete_devices_by_subscription_id(subscription_id)
        
        self.db.commit()
        return True

    def get_subscriptions_with_pagination(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Subscription], int]:
        """分页获取订阅列表"""
        query = self.db.query(Subscription)
        
        # 搜索条件
        if search:
            query = query.join(User).filter(
                or_(
                    User.username.contains(search),
                    User.email.contains(search)
                )
            )
        
        # 状态筛选
        if status == "active":
            query = query.filter(Subscription.expire_time > datetime.utcnow())
        elif status == "expired":
            query = query.filter(Subscription.expire_time <= datetime.utcnow())
        elif status == "expiring_soon":
            cutoff_date = datetime.utcnow() + timedelta(days=7)
            query = query.filter(
                and_(
                    Subscription.expire_time <= cutoff_date,
                    Subscription.expire_time > datetime.utcnow()
                )
            )
        
        total = query.count()
        subscriptions = query.offset(skip).limit(limit).order_by(Subscription.created_at.desc()).all()
        
        return subscriptions, total 