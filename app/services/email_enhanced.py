from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ssl
import json

from app.models.email import EmailQueue
from app.schemas.email import EmailQueueCreate
from app.services.email_template import EmailTemplateService
from app.core.settings_manager import settings_manager

class EnhancedEmailService:
    def __init__(self, db: Session):
        self.db = db
        self.template_service = EmailTemplateService(db)

    def send_template_email(self, template_name: str, to_email: str, variables: Dict[str, Any], 
                          email_type: str = None, attachments: List[Dict] = None) -> bool:
        """使用模板发送邮件"""
        try:
            # 渲染模板
            subject, content = self.template_service.render_template(template_name, variables)
            
            # 创建邮件队列
            email_data = EmailQueueCreate(
                to_email=to_email,
                subject=subject,
                content=content,
                content_type='html',
                email_type=email_type or template_name,
                attachments=json.dumps(attachments) if attachments else None
            )
            
            email_queue = EmailQueue(**email_data.dict())
            self.db.add(email_queue)
            self.db.commit()
            self.db.refresh(email_queue)
            
            return True
            
        except Exception as e:
            print(f"发送模板邮件失败: {e}")
            return False

    def send_verification_email(self, user_email: str, token: str) -> bool:
        """发送验证邮件"""
        try:
            variables = {
                "verification_url": f"http://localhost:3000/verify-email?token={token}",
                "site_name": "XBoard Modern"
            }
            return self.send_template_email("verification", user_email, variables, "verification")
        except:
            return self._send_default_verification_email(user_email, token)

    def send_reset_password_email(self, user_email: str, token: str) -> bool:
        """发送重置密码邮件"""
        try:
            variables = {
                "reset_url": f"http://localhost:3000/reset-password?token={token}",
                "site_name": "XBoard Modern"
            }
            return self.send_template_email("reset_password", user_email, variables, "reset_password")
        except:
            return self._send_default_reset_password_email(user_email, token)

    def send_welcome_email(self, user_email: str, username: str) -> bool:
        """发送欢迎邮件"""
        try:
            variables = {
                "username": username,
                "site_name": "XBoard Modern"
            }
            return self.send_template_email("welcome", user_email, variables, "welcome")
        except:
            return self._send_default_welcome_email(user_email, username)

    def send_subscription_email(self, user_email: str, subscription_data: Dict[str, Any]) -> bool:
        """发送订阅相关邮件"""
        try:
            variables = {
                "site_name": "XBoard Modern",
                **subscription_data
            }
            return self.send_template_email("subscription", user_email, variables, "subscription")
        except:
            return self._send_default_subscription_email(user_email, subscription_data)

    def send_subscription_expiry_reminder(self, user_email: str, username: str, days_left: int, 
                                       package_name: str, expiry_date: str) -> bool:
        """发送订阅到期提醒"""
        try:
            variables = {
                "username": username,
                "days_left": days_left,
                "package_name": package_name,
                "expiry_date": expiry_date,
                "site_name": "XBoard Modern"
            }
            return self.send_template_email("subscription_expiry", user_email, variables, "subscription_expiry")
        except:
            return self._send_default_expiry_reminder(user_email, username, days_left, package_name, expiry_date)

    def send_subscription_reset_notification(self, user_email: str, username: str, 
                                           new_subscription_url: str, reset_time: str, 
                                           reset_reason: str) -> bool:
        """发送订阅重置通知"""
        try:
            variables = {
                "username": username,
                "new_subscription_url": new_subscription_url,
                "reset_time": reset_time,
                "reset_reason": reset_reason,
                "site_name": "XBoard Modern"
            }
            return self.send_template_email("subscription_reset", user_email, variables, "subscription_reset")
        except:
            return self._send_default_reset_notification(user_email, username, new_subscription_url, reset_time, reset_reason)

    # 默认邮件内容（模板不存在时的备用方案）
    def _send_default_verification_email(self, user_email: str, token: str) -> bool:
        """发送默认验证邮件"""
        verification_url = f"http://localhost:3000/verify-email?token={token}"
        
        subject = "验证您的 XBoard Modern 账户"
        content = f"""
        <html>
        <body>
            <h2>欢迎使用 XBoard Modern</h2>
            <p>请点击下面的链接验证您的邮箱地址：</p>
            <p><a href="{verification_url}">验证邮箱</a></p>
            <p>如果您没有注册 XBoard Modern 账户，请忽略此邮件。</p>
            <p>此链接将在24小时后失效。</p>
        </body>
        </html>
        """
        
        email_data = EmailQueueCreate(
            to_email=user_email,
            subject=subject,
            content=content,
            content_type='html',
            email_type='verification'
        )
        
        email_queue = EmailQueue(**email_data.dict())
        self.db.add(email_queue)
        self.db.commit()
        return True

    def _send_default_reset_password_email(self, user_email: str, token: str) -> bool:
        """发送默认重置密码邮件"""
        reset_url = f"http://localhost:3000/reset-password?token={token}"
        
        subject = "重置您的 XBoard Modern 密码"
        content = f"""
        <html>
        <body>
            <h2>密码重置请求</h2>
            <p>您请求重置 XBoard Modern 账户的密码。</p>
            <p>请点击下面的链接重置密码：</p>
            <p><a href="{reset_url}">重置密码</a></p>
            <p>如果您没有请求重置密码，请忽略此邮件。</p>
            <p>此链接将在1小时后失效。</p>
        </body>
        </html>
        """
        
        email_data = EmailQueueCreate(
            to_email=user_email,
            subject=subject,
            content=content,
            content_type='html',
            email_type='reset_password'
        )
        
        email_queue = EmailQueue(**email_data.dict())
        self.db.add(email_queue)
        self.db.commit()
        return True

    def _send_default_welcome_email(self, user_email: str, username: str) -> bool:
        """发送默认欢迎邮件"""
        subject = "欢迎使用 XBoard Modern"
        content = f"""
        <html>
        <body>
            <h2>欢迎使用 XBoard Modern</h2>
            <p>亲爱的 {username}，</p>
            <p>感谢您注册 XBoard Modern！您的账户已成功创建。</p>
            <p>现在您可以开始使用我们的服务了。</p>
            <p>如果您有任何问题，请随时联系我们的客服团队。</p>
            <p>祝您使用愉快！</p>
        </body>
        </html>
        """
        
        email_data = EmailQueueCreate(
            to_email=user_email,
            subject=subject,
            content=content,
            content_type='html',
            email_type='welcome'
        )
        
        email_queue = EmailQueue(**email_data.dict())
        self.db.add(email_queue)
        self.db.commit()
        return True

    def _send_default_subscription_email(self, user_email: str, subscription_data: Dict[str, Any]) -> bool:
        """发送默认订阅邮件"""
        subject = "您的 XBoard Modern 订阅信息"
        content = f"""
        <html>
        <body>
            <h2>订阅信息</h2>
            <p>您的订阅详情如下：</p>
            <ul>
                <li>订阅ID: {subscription_data.get('id')}</li>
                <li>套餐名称: {subscription_data.get('package_name')}</li>
                <li>到期时间: {subscription_data.get('expires_at')}</li>
                <li>状态: {subscription_data.get('status')}</li>
            </ul>
            <p>感谢您使用 XBoard Modern！</p>
        </body>
        </html>
        """
        
        email_data = EmailQueueCreate(
            to_email=user_email,
            subject=subject,
            content=content,
            content_type='html',
            email_type='subscription'
        )
        
        email_queue = EmailQueue(**email_data.dict())
        self.db.add(email_queue)
        self.db.commit()
        return True

    def _send_default_expiry_reminder(self, user_email: str, username: str, days_left: int, 
                                    package_name: str, expiry_date: str) -> bool:
        """发送默认到期提醒"""
        subject = "XBoard Modern - 订阅到期提醒"
        content = f"""
        <html>
        <body>
            <h2>订阅到期提醒</h2>
            <p>亲爱的 {username}，</p>
            <p>您的订阅将在 {expiry_date} 到期，剩余 {days_left} 天。</p>
            <p>当前套餐：{package_name}</p>
            <p>为了避免服务中断，请及时续费。</p>
            <p>感谢您使用 XBoard Modern！</p>
        </body>
        </html>
        """
        
        email_data = EmailQueueCreate(
            to_email=user_email,
            subject=subject,
            content=content,
            content_type='html',
            email_type='subscription_expiry'
        )
        
        email_queue = EmailQueue(**email_data.dict())
        self.db.add(email_queue)
        self.db.commit()
        return True

    def _send_default_reset_notification(self, user_email: str, username: str, 
                                       new_subscription_url: str, reset_time: str, 
                                       reset_reason: str) -> bool:
        """发送默认重置通知"""
        subject = "XBoard Modern - 订阅重置通知"
        content = f"""
        <html>
        <body>
            <h2>订阅重置通知</h2>
            <p>亲爱的 {username}，</p>
            <p>您的订阅已重置，新的订阅地址：</p>
            <p><a href="{new_subscription_url}">{new_subscription_url}</a></p>
            <p>重置时间：{reset_time}</p>
            <p>重置原因：{reset_reason}</p>
            <p>感谢您使用 XBoard Modern！</p>
        </body>
        </html>
        """
        
        email_data = EmailQueueCreate(
            to_email=user_email,
            subject=subject,
            content=content,
            content_type='html',
            email_type='subscription_reset'
        )
        
        email_queue = EmailQueue(**email_data.dict())
        self.db.add(email_queue)
        self.db.commit()
        return True
