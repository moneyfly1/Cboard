"""
通知服务 - 处理各种类型的通知发送
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User
from app.models.subscription import Subscription
from app.models.order import Order
from app.services.email import EmailService
from app.services.email_template_enhanced import EmailTemplateEnhanced


class NotificationService:
    """通知服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService(db)
    
    def should_send_notification(self, user: User, notification_type: str) -> bool:
        """检查是否应该发送通知"""
        # 检查用户是否启用邮件通知
        if not user.email_notifications:
            return False
        
        # 检查通知类型是否在用户设置中
        if user.notification_types:
            try:
                allowed_types = json.loads(user.notification_types)
                if notification_type not in allowed_types:
                    return False
            except:
                # 如果解析失败，使用默认设置
                pass
        
        return True
    
    def send_subscription_expiry_reminder(self, days_before: int = 7) -> int:
        """发送订阅到期提醒"""
        sent_count = 0
        
        try:
            # 计算到期日期范围
            now = datetime.now()
            target_date = now + timedelta(days=days_before)
            
            # 查找即将到期的订阅
            subscriptions = self.db.query(Subscription).join(User).filter(
                and_(
                    Subscription.status == 'active',
                    Subscription.expire_time.isnot(None),
                    Subscription.expire_time >= target_date - timedelta(hours=1),
                    Subscription.expire_time <= target_date + timedelta(hours=1)
                )
            ).all()
            
            for subscription in subscriptions:
                user = subscription.user
                
                # 检查是否应该发送通知
                if not self.should_send_notification(user, 'subscription'):
                    continue
                
                # 发送到期提醒邮件
                expiry_date = subscription.expire_time.strftime('%Y-%m-%d %H:%M:%S')
                success = self.email_service.send_subscription_expiry_reminder(
                    user_email=user.email,
                    username=user.username,
                    days_left=days_before,
                    package_name="网络服务",
                    expiry_date=expiry_date,
                    is_expired=False
                )
                
                if success:
                    sent_count += 1
                    print(f"发送到期提醒邮件成功: {user.email}")
                else:
                    print(f"发送到期提醒邮件失败: {user.email}")
            
            return sent_count
            
        except Exception as e:
            print(f"发送订阅到期提醒失败: {e}")
            return 0
    
    def send_subscription_expired_notification(self) -> int:
        """发送订阅已过期通知"""
        sent_count = 0
        
        try:
            # 查找已过期的订阅
            now = datetime.now()
            expired_subscriptions = self.db.query(Subscription).join(User).filter(
                and_(
                    Subscription.status == 'active',
                    Subscription.expire_time.isnot(None),
                    Subscription.expire_time < now
                )
            ).all()
            
            for subscription in expired_subscriptions:
                user = subscription.user
                
                # 检查是否应该发送通知
                if not self.should_send_notification(user, 'subscription'):
                    continue
                
                # 发送过期通知邮件
                expiry_date = subscription.expire_time.strftime('%Y-%m-%d %H:%M:%S')
                success = self.email_service.send_subscription_expiry_reminder(
                    user_email=user.email,
                    username=user.username,
                    days_left=0,
                    package_name="网络服务",
                    expiry_date=expiry_date,
                    is_expired=True
                )
                
                if success:
                    sent_count += 1
                    print(f"发送过期通知邮件成功: {user.email}")
                else:
                    print(f"发送过期通知邮件失败: {user.email}")
            
            return sent_count
            
        except Exception as e:
            print(f"发送订阅过期通知失败: {e}")
            return 0
    
    def send_payment_success_notification(self, order: Order) -> bool:
        """发送支付成功通知"""
        try:
            user = order.user
            
            # 检查是否应该发送通知
            if not self.should_send_notification(user, 'payment'):
                return False
            
            # 准备邮件内容
            subject = "支付成功通知 - 网络服务"
            content = EmailTemplateEnhanced.get_payment_success_template(
                username=user.username,
                order_id=str(order.id),
                amount=str(order.amount),
                package_name=order.package.name if order.package else "网络服务"
            )
            
            # 创建邮件队列
            from app.schemas.email import EmailQueueCreate
            email_data = EmailQueueCreate(
                to_email=user.email,
                subject=subject,
                content=content,
                content_type='html',
                email_type='payment_success'
            )
            
            email_queue = self.email_service.create_email_queue(email_data)
            return self.email_service.send_email(email_queue)
            
        except Exception as e:
            print(f"发送支付成功通知失败: {e}")
            return False
    
    def send_new_user_welcome_notification(self, user: User) -> bool:
        """发送新用户欢迎通知"""
        try:
            # 检查是否应该发送通知
            if not self.should_send_notification(user, 'system'):
                return False
            
            # 准备邮件内容
            subject = "欢迎注册 - 网络服务"
            content = EmailTemplateEnhanced.get_welcome_template(
                username=user.username,
                login_url="http://localhost:5173/login"
            )
            
            # 创建邮件队列
            from app.schemas.email import EmailQueueCreate
            email_data = EmailQueueCreate(
                to_email=user.email,
                subject=subject,
                content=content,
                content_type='html',
                email_type='welcome'
            )
            
            email_queue = self.email_service.create_email_queue(email_data)
            return self.email_service.send_email(email_queue)
            
        except Exception as e:
            print(f"发送新用户欢迎通知失败: {e}")
            return False
    
    def send_subscription_created_notification(self, subscription: Subscription) -> bool:
        """发送订阅创建通知"""
        try:
            user = subscription.user
            
            # 检查是否应该发送通知
            if not self.should_send_notification(user, 'subscription'):
                return False
            
            # 准备邮件内容
            subject = "订阅创建成功 - 网络服务"
            content = EmailTemplateEnhanced.get_subscription_created_template(
                username=user.username,
                subscription_url=subscription.subscription_url,
                expire_time=subscription.expire_time.strftime('%Y-%m-%d %H:%M:%S') if subscription.expire_time else "永久"
            )
            
            # 创建邮件队列
            from app.schemas.email import EmailQueueCreate
            email_data = EmailQueueCreate(
                to_email=user.email,
                subject=subject,
                content=content,
                content_type='html',
                email_type='subscription_created'
            )
            
            email_queue = self.email_service.create_email_queue(email_data)
            return self.email_service.send_email(email_queue)
            
        except Exception as e:
            print(f"发送订阅创建通知失败: {e}")
            return False
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """获取通知统计信息"""
        try:
            total_users = self.db.query(User).count()
            email_enabled_users = self.db.query(User).filter(User.email_notifications == True).count()
            
            # 统计各种通知类型的用户数量
            subscription_notifications = 0
            payment_notifications = 0
            system_notifications = 0
            
            users = self.db.query(User).all()
            for user in users:
                if user.notification_types:
                    try:
                        types = json.loads(user.notification_types)
                        if 'subscription' in types:
                            subscription_notifications += 1
                        if 'payment' in types:
                            payment_notifications += 1
                        if 'system' in types:
                            system_notifications += 1
                    except:
                        pass
            
            return {
                "total_users": total_users,
                "email_enabled_users": email_enabled_users,
                "subscription_notifications": subscription_notifications,
                "payment_notifications": payment_notifications,
                "system_notifications": system_notifications
            }
            
        except Exception as e:
            print(f"获取通知统计失败: {e}")
            return {}
