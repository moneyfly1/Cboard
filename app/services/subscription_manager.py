from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User
from app.models.subscription import Subscription
from app.models.package import Package
from app.models.order import Order


class SubscriptionManager:
    """订阅管理器 - 处理订单支付后的订阅和设备数量管理"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_paid_order(self, order: Order) -> bool:
        """处理已支付订单，更新用户订阅和设备数量"""
        try:
            # 获取用户和套餐信息
            user = self.db.query(User).filter(User.id == order.user_id).first()
            package = self.db.query(Package).filter(Package.id == order.package_id).first()
            
            if not user or not package:
                return False
            
            # 获取用户当前订阅
            current_subscription = self.db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.status == 'active'
            ).first()
            
            # 计算新的订阅信息
            new_device_limit = package.device_limit
            new_expire_time = self._calculate_expire_time(
                current_subscription, 
                package, 
                order.created_at
            )
            
            # 处理设备数量升级/续费
            if current_subscription and current_subscription.status == 'active':
                # 用户有活跃订阅，需要处理升级或续费
                if package.device_limit > current_subscription.device_limit:
                    # 设备数量升级，需要价格折算
                    self._handle_device_upgrade(
                        user, 
                        current_subscription, 
                        package, 
                        new_device_limit, 
                        new_expire_time
                    )
                else:
                    # 设备数量相同或更少，直接续费
                    self._handle_subscription_renewal(
                        current_subscription, 
                        new_expire_time
                    )
            else:
                # 用户没有订阅或订阅已过期，创建新订阅或重新激活
                if current_subscription:
                    # 重新激活过期订阅
                    self._reactivate_expired_subscription(
                        current_subscription,
                        package,
                        new_device_limit,
                        new_expire_time
                    )
                else:
                    # 创建新订阅
                    self._create_new_subscription(
                        user, 
                        package, 
                        new_device_limit, 
                        new_expire_time
                    )
            
            # 更新订单状态
            order.status = 'paid'
            order.payment_time = datetime.now()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"处理订单支付失败: {e}")
            return False
    
    def _calculate_expire_time(
        self, 
        current_subscription: Optional[Subscription], 
        package: Package, 
        order_time: datetime
    ) -> datetime:
        """计算新的到期时间"""
        package_duration = timedelta(days=package.duration_days)
        
        if current_subscription and current_subscription.status == 'active' and current_subscription.expire_time > order_time:
            # 用户订阅未过期，在现有到期时间基础上延长
            return current_subscription.expire_time + package_duration
        else:
            # 用户订阅已过期或没有订阅，从当前时间开始计算
            return order_time + package_duration
    
    def _handle_device_upgrade(
        self, 
        user: User, 
        current_subscription: Subscription, 
        package: Package, 
        new_device_limit: int, 
        new_expire_time: datetime
    ):
        """处理设备数量升级"""
        # 计算剩余时间比例
        remaining_time = current_subscription.expire_time - datetime.now()
        total_time = current_subscription.expire_time - current_subscription.created_at
        
        if remaining_time.total_seconds() > 0 and total_time.total_seconds() > 0:
            remaining_ratio = remaining_time.total_seconds() / total_time.total_seconds()
            
            # 按比例计算升级费用（这里简化处理，实际可能需要更复杂的计算）
            # 更新订阅信息
            current_subscription.device_limit = new_device_limit
            current_subscription.expire_time = new_expire_time
            current_subscription.updated_at = datetime.now()
        else:
            # 订阅已过期，直接更新
            current_subscription.device_limit = new_device_limit
            current_subscription.expire_time = new_expire_time
            current_subscription.updated_at = datetime.now()
    
    def _handle_subscription_renewal(
        self, 
        current_subscription: Subscription, 
        new_expire_time: datetime
    ):
        """处理订阅续费"""
        current_subscription.expire_time = new_expire_time
        current_subscription.updated_at = datetime.now()
    
    def _create_new_subscription(
        self, 
        user: User, 
        package: Package, 
        device_limit: int, 
        expire_time: datetime
    ):
        """创建新订阅"""
        subscription = Subscription(
            user_id=user.id,
            package_id=package.id,
            device_limit=device_limit,
            status='active',
            created_at=datetime.now(),
            expire_time=expire_time
        )
        self.db.add(subscription)
    
    def _reactivate_expired_subscription(
        self,
        current_subscription: Subscription,
        package: Package,
        device_limit: int,
        expire_time: datetime
    ):
        """重新激活过期订阅"""
        current_subscription.package_id = package.id
        current_subscription.device_limit = device_limit
        current_subscription.status = 'active'
        current_subscription.expire_time = expire_time
        current_subscription.updated_at = datetime.now()
        # 保持原有的subscription_url不变
    
    def check_expired_subscriptions(self):
        """检查并处理过期的订阅"""
        try:
            now = datetime.now()
            expired_subscriptions = self.db.query(Subscription).filter(
                and_(
                    Subscription.status == 'active',
                    Subscription.expire_time < now
                )
            ).all()
            
            for subscription in expired_subscriptions:
                # 将设备数量归零
                subscription.device_limit = 0
                subscription.status = 'expired'
                subscription.updated_at = now
            
            self.db.commit()
            return len(expired_subscriptions)
            
        except Exception as e:
            self.db.rollback()
            print(f"处理过期订阅失败: {e}")
            return 0
    
    def get_user_subscription_info(self, user_id: int) -> dict:
        """获取用户订阅信息"""
        subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == 'active'
        ).first()
        
        if not subscription:
            return {
                'has_subscription': False,
                'device_limit': 0,
                'expire_time': None,
                'status': 'inactive'
            }
        
        return {
            'has_subscription': True,
            'device_limit': subscription.device_limit,
            'expire_time': subscription.expire_time,
            'status': 'active' if subscription.expire_time > datetime.now() else 'expired'
        }
