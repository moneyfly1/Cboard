from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.order import Order
from app.models.package import Package
from app.models.user import User
from app.models.payment_config import PaymentConfig
from app.schemas.order import OrderCreate, OrderUpdate
from app.utils.security import generate_order_no

class OrderService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, order_id: int) -> Optional[Order]:
        """根据ID获取订单"""
        return self.db.query(Order).filter(Order.id == order_id).first()

    def get_by_order_no(self, order_no: str) -> Optional[Order]:
        """根据订单号获取订单"""
        return self.db.query(Order).filter(Order.order_no == order_no).first()

    def create_order(
        self,
        user_id: int,
        package_id: int,
        payment_method: str = "alipay",
        payment_config_id: Optional[int] = None,
        amount: float = None
    ) -> Order:
        """创建订单"""
        order_no = generate_order_no()

        # 获取套餐信息
        package = self.db.query(Package).filter(Package.id == package_id).first()
        if not package:
            raise ValueError("套餐不存在")

        # 如果没有指定金额，使用套餐价格
        if amount is None:
            amount = float(package.price)

        # 设置支付方式名称
        payment_method_name = payment_method

        order = Order(
            order_no=order_no,
            user_id=user_id,
            package_id=package_id,
            amount=amount,
            status="pending",
            payment_method_id=payment_config_id,
            payment_method_name=payment_method_name
        )

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def get_user_orders(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Order], int]:
        """获取用户订单列表"""
        query = self.db.query(Order).filter(Order.user_id == user_id)
        total = query.count()
        orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
        return orders, total

    def get_orders_with_pagination(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        date_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Order], int]:
        """获取订单列表（分页）"""
        query = self.db.query(Order)
        
        # 状态筛选
        if status:
            query = query.filter(Order.status == status)
        
        # 日期筛选
        if date_filter:
            now = datetime.utcnow()
            if date_filter == "today":
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today_start + timedelta(days=1)
                query = query.filter(
                    and_(Order.created_at >= today_start, Order.created_at < today_end)
                )
            elif date_filter == "yesterday":
                yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                yesterday_end = yesterday_start + timedelta(days=1)
                query = query.filter(
                    and_(Order.created_at >= yesterday_start, Order.created_at < yesterday_end)
                )
            elif date_filter == "week":
                week_start = now - timedelta(days=7)
                query = query.filter(Order.created_at >= week_start)
            elif date_filter == "month":
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Order.created_at >= month_start)
        
        # 搜索条件
        if search:
            query = query.join(User).filter(
                or_(
                    User.username.contains(search),
                    User.email.contains(search),
                    Order.order_no.contains(search)
                )
            )
        
        total = query.count()
        orders = query.offset(skip).limit(limit).order_by(Order.created_at.desc()).all()
        return orders, total

    def update(self, order_id: int, order_update: OrderUpdate) -> Optional[Order]:
        """更新订单"""
        order = self.get(order_id)
        if not order:
            return None
        
        update_data = order_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(order, field, value)
        
        self.db.commit()
        self.db.refresh(order)
        return order

    def cancel_order(self, order_no: str) -> bool:
        """取消订单"""
        order = self.get_by_order_no(order_no)
        if not order:
            return False
        
        if order.status != "pending":
            return False
        
        order.status = "cancelled"
        self.db.commit()
        return True

    def complete_payment(self, order_no: str, payment_time: datetime) -> bool:
        """完成支付"""
        order = self.get_by_order_no(order_no)
        if not order:
            return False
        
        if order.status != "pending":
            return False
        
        # 更新订单状态
        order.status = "paid"
        order.payment_time = payment_time
        
        # 延长用户订阅
        self._extend_user_subscription(order)
        
        self.db.commit()
        return True

    def _extend_user_subscription(self, order: Order):
        """延长用户订阅"""
        from app.services.subscription import SubscriptionService
        
        subscription_service = SubscriptionService(self.db)
        
        # 获取用户订阅
        subscription = subscription_service.get_by_user_id(order.user_id)
        
        if subscription:
            # 延长现有订阅
            subscription_service.extend_subscription(subscription.id, order.package.duration)
        else:
            # 创建新订阅
            from app.schemas.subscription import SubscriptionCreate
            
            subscription_data = SubscriptionCreate(
                user_id=order.user_id,
                url="",  # 这里应该生成订阅URL
                device_limit=order.package.device_limit,
                expire_time=datetime.utcnow() + timedelta(days=order.package.duration)
            )
            subscription_service.create(subscription_data)

    def generate_payment_url(self, order: Order) -> str:
        """生成支付URL"""
        # 这里应该根据支付方式生成不同的支付URL
        # 示例：支付宝支付
        if order.payment_method_name == "alipay":
            return f"https://openapi.alipay.com/gateway.do?order_no={order.order_no}&amount={order.amount}"
        elif order.payment_method_name == "wechat":
            return f"weixin://wxpay/bizpayurl?order_no={order.order_no}&amount={order.amount}"
        else:
            return f"https://example.com/payment?order_no={order.order_no}&amount={order.amount}"

    def count(self) -> int:
        """统计订单数量"""
        return self.db.query(Order).count()

    def count_by_status(self, status: str) -> int:
        """根据状态统计订单数量"""
        return self.db.query(Order).filter(Order.status == status).count()

    def count_orders_since(self, start_date: datetime, end_date: Optional[datetime] = None) -> int:
        """统计指定时间段内的订单数量"""
        query = self.db.query(Order).filter(Order.created_at >= start_date)
        if end_date:
            query = query.filter(Order.created_at < end_date)
        return query.count()

    def get_revenue_since(self, start_date: datetime, end_date: Optional[datetime] = None) -> float:
        """获取指定时间段内的收入"""
        query = self.db.query(func.sum(Order.amount)).filter(
            and_(Order.status == "paid", Order.created_at >= start_date)
        )
        if end_date:
            query = query.filter(Order.created_at < end_date)
        
        result = query.scalar()
        return float(result) if result else 0.0

    def get_total_revenue(self) -> float:
        """获取总收入"""
        result = self.db.query(func.sum(Order.amount)).filter(
            Order.status == "paid"
        ).scalar()
        return float(result) if result else 0.0

    def get_recent_orders(self, days: int = 7) -> List[Order]:
        """获取最近订单"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(Order).filter(
            Order.created_at >= cutoff_date
        ).order_by(Order.created_at.desc()).all()

    def get_order_stats(self) -> dict:
        """获取订单统计信息"""
        total_orders = self.count()
        pending_orders = self.count_by_status("pending")
        paid_orders = self.count_by_status("paid")
        cancelled_orders = self.count_by_status("cancelled")
        
        # 计算总收入
        total_revenue = self.get_total_revenue()
        
        # 今日订单和收入
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = self.count_orders_since(today_start)
        today_revenue = self.get_revenue_since(today_start)
        
        return {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "paid_orders": paid_orders,
            "cancelled_orders": cancelled_orders,
            "total_revenue": total_revenue,
            "today_orders": today_orders,
            "today_revenue": today_revenue
        } 