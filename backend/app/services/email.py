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

from app.models.email import EmailQueue
from app.schemas.email import EmailQueueCreate, EmailQueueUpdate
from app.core.settings_manager import settings_manager

class EmailService:
    def __init__(self, db: Session):
        self.db = db

    def get_smtp_config(self) -> Dict[str, Any]:
        """获取SMTP配置"""
        return settings_manager.get_smtp_config(self.db)

    def is_email_enabled(self) -> bool:
        """检查邮件功能是否启用"""
        return settings_manager.is_email_enabled(self.db)

    def create_email_queue(self, email_data: EmailQueueCreate) -> EmailQueue:
        """创建邮件队列"""
        if not self.is_email_enabled():
            raise Exception("邮件服务未配置或未启用")
        
        email_queue = EmailQueue(**email_data.dict())
        self.db.add(email_queue)
        self.db.commit()
        self.db.refresh(email_queue)
        return email_queue

    def get_pending_emails(self, limit: int = 10) -> List[EmailQueue]:
        """获取待发送邮件"""
        return self.db.query(EmailQueue).filter(
            EmailQueue.status == 'pending'
        ).order_by(EmailQueue.created_at).limit(limit).all()

    def send_email(self, email_queue: EmailQueue) -> bool:
        """发送邮件"""
        try:
            smtp_config = self.get_smtp_config()
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
            msg['To'] = email_queue.to_email
            msg['Subject'] = email_queue.subject
            
            # 添加邮件内容
            if email_queue.content_type == 'html':
                msg.attach(MIMEText(email_queue.content, 'html'))
            else:
                msg.attach(MIMEText(email_queue.content, 'plain'))
            
            # 添加附件
            if email_queue.attachments:
                for attachment in email_queue.attachments:
                    if isinstance(attachment, dict) and 'filename' in attachment and 'content' in attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment['content'])
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment["filename"]}'
                        )
                        msg.attach(part)
            
            # 发送邮件
            context = ssl.create_default_context()
            
            if smtp_config['encryption'] == 'ssl':
                server = smtplib.SMTP_SSL(smtp_config['host'], smtp_config['port'], context=context)
            else:
                server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
                if smtp_config['encryption'] == 'tls':
                    server.starttls(context=context)
            
            server.login(smtp_config['username'], smtp_config['password'])
            server.send_message(msg)
            server.quit()
            
            # 更新邮件状态
            email_queue.status = 'sent'
            email_queue.sent_at = datetime.now()
            self.db.commit()
            
            return True
            
        except Exception as e:
            # 更新邮件状态为失败
            email_queue.status = 'failed'
            email_queue.error_message = str(e)
            self.db.commit()
            return False

    def send_verification_email(self, user_email: str, token: str) -> bool:
        """发送验证邮件"""
        if not self.is_email_enabled():
            return False
        
        site_name = settings_manager.get_site_name(self.db)
        verification_url = f"http://localhost:3000/verify-email?token={token}"
        
        subject = f"验证您的 {site_name} 账户"
        content = f"""
        <html>
        <body>
            <h2>欢迎使用 {site_name}</h2>
            <p>请点击下面的链接验证您的邮箱地址：</p>
            <p><a href="{verification_url}">验证邮箱</a></p>
            <p>如果您没有注册 {site_name} 账户，请忽略此邮件。</p>
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
        
        email_queue = self.create_email_queue(email_data)
        return self.send_email(email_queue)

    def send_reset_password_email(self, user_email: str, token: str) -> bool:
        """发送重置密码邮件"""
        if not self.is_email_enabled():
            return False
        
        site_name = settings_manager.get_site_name(self.db)
        reset_url = f"http://localhost:3000/reset-password?token={token}"
        
        subject = f"重置您的 {site_name} 密码"
        content = f"""
        <html>
        <body>
            <h2>密码重置请求</h2>
            <p>您请求重置 {site_name} 账户的密码。</p>
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
        
        email_queue = self.create_email_queue(email_data)
        return self.send_email(email_queue)

    def send_welcome_email(self, user_email: str, username: str) -> bool:
        """发送欢迎邮件"""
        if not self.is_email_enabled():
            return False
        
        site_name = settings_manager.get_site_name(self.db)
        
        subject = f"欢迎使用 {site_name}"
        content = f"""
        <html>
        <body>
            <h2>欢迎使用 {site_name}</h2>
            <p>亲爱的 {username}，</p>
            <p>感谢您注册 {site_name}！您的账户已成功创建。</p>
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
        
        email_queue = self.create_email_queue(email_data)
        return self.send_email(email_queue)

    def send_subscription_email(self, user_email: str, subscription_data: Dict[str, Any]) -> bool:
        """发送订阅相关邮件"""
        if not self.is_email_enabled():
            return False
        
        site_name = settings_manager.get_site_name(self.db)
        
        subject = f"您的 {site_name} 订阅信息"
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
            <p>感谢您使用 {site_name}！</p>
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
        
        email_queue = self.create_email_queue(email_data)
        return self.send_email(email_queue)

    def send_announcement_email(self, user_email: str, announcement_data: Dict[str, Any]) -> bool:
        """发送公告邮件"""
        if not self.is_email_enabled():
            return False
        
        site_name = settings_manager.get_site_name(self.db)
        
        subject = f"{site_name} - {announcement_data.get('title')}"
        content = f"""
        <html>
        <body>
            <h2>{announcement_data.get('title')}</h2>
            <div>{announcement_data.get('content')}</div>
            <p>此邮件来自 {site_name}</p>
        </body>
        </html>
        """
        
        email_data = EmailQueueCreate(
            to_email=user_email,
            subject=subject,
            content=content,
            content_type='html',
            email_type='announcement'
        )
        
        email_queue = self.create_email_queue(email_data)
        return self.send_email(email_queue)

    def process_email_queue(self) -> Dict[str, int]:
        """处理邮件队列"""
        if not self.is_email_enabled():
            return {"sent": 0, "failed": 0, "total": 0}
        
        pending_emails = self.get_pending_emails(limit=50)
        sent_count = 0
        failed_count = 0
        
        for email_queue in pending_emails:
            if self.send_email(email_queue):
                sent_count += 1
            else:
                failed_count += 1
        
        return {
            "sent": sent_count,
            "failed": failed_count,
            "total": len(pending_emails)
        }

    def cleanup_old_emails(self, days: int = 30) -> int:
        """清理旧邮件"""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = self.db.query(EmailQueue).filter(
            EmailQueue.created_at < cutoff_date,
            EmailQueue.status.in_(['sent', 'failed'])
        ).delete()
        self.db.commit()
        return deleted_count

    def get_email_stats(self) -> Dict[str, int]:
        """获取邮件统计"""
        total = self.db.query(EmailQueue).count()
        pending = self.db.query(EmailQueue).filter(EmailQueue.status == 'pending').count()
        sent = self.db.query(EmailQueue).filter(EmailQueue.status == 'sent').count()
        failed = self.db.query(EmailQueue).filter(EmailQueue.status == 'failed').count()
        
        return {
            "total": total,
            "pending": pending,
            "sent": sent,
            "failed": failed
        } 