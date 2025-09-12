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
from app.schemas.email import EmailQueueCreate, EmailQueueUpdate
from app.services.email_template import EmailTemplateService
from app.services.email_template_enhanced import EmailTemplateEnhanced
from app.core.settings_manager import settings_manager

class EmailService:
    def __init__(self, db: Session):
        self.db = db
        self.template_service = EmailTemplateService(db)

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
        
        try:
            email_queue = EmailQueue(**email_data.dict())
            self.db.add(email_queue)
            self.db.commit()
            self.db.refresh(email_queue)
            return email_queue
        except Exception as e:
            print(f"创建邮件队列失败: {e}")
            raise

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
                msg.attach(MIMEText(email_queue.content, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(email_queue.content, 'plain', 'utf-8'))
            
            # 添加附件
            if email_queue.attachments:
                try:
                    attachments_data = json.loads(email_queue.attachments)
                    for attachment in attachments_data:
                        if isinstance(attachment, dict) and 'filename' in attachment and 'content' in attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment['content'])
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {attachment["filename"]}'
                            )
                            msg.attach(part)
                except json.JSONDecodeError:
                    # 附件数据格式错误，跳过附件
                    pass
            
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
            print(f"邮件发送失败: {email_queue.to_email}, 错误: {str(e)}")
            email_queue.status = 'failed'
            email_queue.error_message = str(e)
            self.db.commit()
            return False

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
            
            email_queue = self.create_email_queue(email_data)
            return self.send_email(email_queue)
            
        except Exception as e:
            # 记录错误日志
            print(f"发送模板邮件失败: {e}")
            return False

    def send_verification_email(self, user_email: str, token: str, username: str = None) -> bool:
        """发送验证邮件"""
        if not self.is_email_enabled():
            print(f"邮件服务未启用，无法发送验证邮件到: {user_email}")
            return False
        
        try:
            # 使用动态BASE_URL构建验证链接
            from app.core.config import settings
            verification_url = f"{settings.BASE_URL}/verify-email?token={token}"
            html_content = EmailTemplateEnhanced.get_activation_template(username or "用户", verification_url)
            
            # 创建邮件队列
            email_data = EmailQueueCreate(
                to_email=user_email,
                subject="账户激活 - 网络服务",
                content=html_content,
                content_type='html',
                email_type='verification'
            )
            
            email_queue = self.create_email_queue(email_data)
            success = self.send_email(email_queue)
            if success:
                print(f"验证邮件发送成功: {user_email}")
                return True
            else:
                print(f"验证邮件发送失败: {user_email}")
                return False
            
        except Exception as e:
            # 如果增强模板失败，使用默认内容
            print(f"使用增强模板发送验证邮件失败，使用默认内容: {e}")
            try:
                return self._send_default_verification_email(user_email, token)
            except Exception as e2:
                print(f"默认验证邮件发送也失败: {e2}")
                return False

    def send_reset_password_email(self, user_email: str, token: str, username: str = None) -> bool:
        """发送重置密码邮件"""
        if not self.is_email_enabled():
            return False
        
        try:
            # 使用增强版模板发送重置密码邮件
            reset_url = f"http://localhost:5173/reset-password?token={token}"
            html_content = EmailTemplateEnhanced.get_password_reset_template(username or "用户", reset_url)
            
            # 创建邮件队列
            email_data = EmailQueueCreate(
                to_email=user_email,
                subject="密码重置 - 网络服务",
                content=html_content,
                content_type='html',
                email_type='reset_password'
            )
            
            email_queue = self.create_email_queue(email_data)
            return self.send_email(email_queue)
            
        except Exception as e:
            # 如果增强模板失败，使用默认内容
            print(f"使用增强模板发送重置密码邮件失败，使用默认内容: {e}")
            return self._send_default_reset_password_email(user_email, token)

    def send_welcome_email(self, user_email: str, username: str) -> bool:
        """发送欢迎邮件"""
        if not self.is_email_enabled():
            return False
        
        try:
            # 使用模板发送欢迎邮件
            variables = {
                "username": username,
                "site_name": settings_manager.get_site_name(self.db)
            }
            
            return self.send_template_email("welcome", user_email, variables, "welcome")
            
        except Exception as e:
            # 如果模板不存在，使用默认内容
            print(f"使用模板发送欢迎邮件失败，使用默认内容: {e}")
            return self._send_default_welcome_email(user_email, username)

    def send_subscription_email(self, user_email: str, subscription_data: Dict[str, Any]) -> bool:
        """发送订阅相关邮件"""
        if not self.is_email_enabled():
            return False
        
        try:
            # 使用增强版模板发送订阅邮件
            username = subscription_data.get('username', '用户')
            html_content = EmailTemplateEnhanced.get_subscription_template(username, subscription_data)
            
            # 创建邮件队列
            email_queue_data = EmailQueueCreate(
                to_email=user_email,
                subject="您的服务配置信息 - 网络服务",
                content=html_content,
                content_type='html',
                email_type="subscription"
            )
            
            email_queue = self.create_email_queue(email_queue_data)
            return self.send_email(email_queue)
            
        except Exception as e:
            print(f"发送订阅邮件失败: {e}")
            return False

    def send_subscription_expiry_reminder(self, user_email: str, username: str, days_left: int, 
                                       package_name: str, expiry_date: str, is_expired: bool = False) -> bool:
        """发送订阅到期提醒"""
        if not self.is_email_enabled():
            return False
        
        try:
            # 使用增强版模板发送到期提醒
            html_content = EmailTemplateEnhanced.get_expiration_template(username, expiry_date, is_expired)
            
            # 创建邮件队列
            email_data = EmailQueueCreate(
                to_email=user_email,
                subject=f"{'服务已到期' if is_expired else '服务即将到期'} - 网络服务",
                content=html_content,
                content_type='html',
                email_type='subscription_expiry'
            )
            
            email_queue = self.create_email_queue(email_data)
            return self.send_email(email_queue)
            
        except Exception as e:
            # 如果增强模板失败，使用默认内容
            print(f"使用增强模板发送到期提醒失败，使用默认内容: {e}")
            return self._send_default_expiry_reminder(user_email, username, days_left, package_name, expiry_date)

    def send_subscription_reset_notification(self, user_email: str, username: str, 
                                           new_subscription_url: str, reset_time: str, 
                                           reset_reason: str) -> bool:
        """发送订阅重置通知"""
        if not self.is_email_enabled():
            return False
        
        try:
            # 使用增强模板发送重置通知
            from app.services.email_template_enhanced import EmailTemplateEnhanced
            
            content = EmailTemplateEnhanced.get_subscription_reset_template(
                username=username,
                new_subscription_url=new_subscription_url,
                reset_time=reset_time,
                reset_reason=reset_reason
            )
            
            subject = f"{settings_manager.get_site_name(self.db)} - 订阅重置通知"
            
            email_data = EmailQueueCreate(
                to_email=user_email,
                subject=subject,
                content=content,
                content_type='html',
                email_type='subscription_reset'
            )
            
            email_queue = self.create_email_queue(email_data)
            return self.send_email(email_queue)
            
        except Exception as e:
            # 如果模板不存在，使用默认内容
            print(f"使用模板发送重置通知失败，使用默认内容: {e}")
            return self._send_default_reset_notification(user_email, username, new_subscription_url, reset_time, reset_reason)

    def send_announcement_email(self, user_email: str, announcement_data: Dict[str, Any]) -> bool:
        """发送公告邮件"""
        if not self.is_email_enabled():
            return False
        
        try:
            # 使用模板发送公告邮件
            variables = {
                "site_name": settings_manager.get_site_name(self.db),
                **announcement_data
            }
            
            return self.send_template_email("announcement", user_email, variables, "announcement")
            
        except Exception as e:
            # 如果模板不存在，使用默认内容
            print(f"使用模板发送公告邮件失败，使用默认内容: {e}")
            return self._send_default_announcement_email(user_email, announcement_data)

    # 默认邮件内容（模板不存在时的备用方案）
    def _send_default_verification_email(self, user_email: str, token: str) -> bool:
        """发送默认验证邮件"""
        site_name = settings_manager.get_site_name(self.db)
        verification_url = f"http://localhost:3000/verify-email?token={token}"
        
        subject = f"验证您的 {site_name} 账户"
        content = f"""<html>
<body>
    <h2>欢迎使用 {site_name}</h2>
    <p>请点击下面的链接验证您的邮箱地址：</p>
    <p><a href="{verification_url}">验证邮箱</a></p>
    <p>如果您没有注册 {site_name} 账户，请忽略此邮件。</p>
    <p>此链接将在24小时后失效。</p>
</body>
</html>"""
        
        email_data = EmailQueueCreate(
            to_email=user_email,
            subject=subject,
            content=content,
            content_type='html',
            email_type='verification'
        )
        
        email_queue = self.create_email_queue(email_data)
        return self.send_email(email_queue)

    def _send_default_reset_password_email(self, user_email: str, token: str) -> bool:
        """发送默认重置密码邮件"""
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

    def _send_default_welcome_email(self, user_email: str, username: str) -> bool:
        """发送默认欢迎邮件"""
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

    def _send_default_subscription_email(self, user_email: str, subscription_data: Dict[str, Any]) -> bool:
        """发送默认订阅邮件"""
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

    def _send_default_expiry_reminder(self, user_email: str, username: str, days_left: int, 
                                    package_name: str, expiry_date: str) -> bool:
        """发送默认到期提醒"""
        site_name = settings_manager.get_site_name(self.db)
        
        subject = f"{site_name} - 订阅到期提醒"
        content = f"""
        <html>
        <body>
            <h2>订阅到期提醒</h2>
            <p>亲爱的 {username}，</p>
            <p>您的订阅将在 {expiry_date} 到期，剩余 {days_left} 天。</p>
            <p>当前套餐：{package_name}</p>
            <p>为了避免服务中断，请及时续费。</p>
            <p>感谢您使用 {site_name}！</p>
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
        
        email_queue = self.create_email_queue(email_data)
        return self.send_email(email_queue)

    def _send_default_reset_notification(self, user_email: str, username: str, 
                                       new_subscription_url: str, reset_time: str, 
                                       reset_reason: str) -> bool:
        """发送默认重置通知"""
        site_name = settings_manager.get_site_name(self.db)
        
        subject = f"{site_name} - 订阅重置通知"
        content = f"""
        <html>
        <body>
            <h2>订阅重置通知</h2>
            <p>亲爱的 {username}，</p>
            <p>您的订阅已重置，新的订阅地址：</p>
            <p><a href="{new_subscription_url}">{new_subscription_url}</a></p>
            <p>重置时间：{reset_time}</p>
            <p>重置原因：{reset_reason}</p>
            <p>感谢您使用 {site_name}！</p>
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
        
        email_queue = self.create_email_queue(email_data)
        return self.send_email(email_queue)

    def _send_default_announcement_email(self, user_email: str, announcement_data: Dict[str, Any]) -> bool:
        """发送默认公告邮件"""
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

    def get_daily_email_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取每日邮件发送统计"""
        stats = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            
            total = self.db.query(EmailQueue).filter(
                EmailQueue.created_at >= start_date,
                EmailQueue.created_at < end_date
            ).count()
            
            sent = self.db.query(EmailQueue).filter(
                EmailQueue.created_at >= start_date,
                EmailQueue.created_at < end_date,
                EmailQueue.status == 'sent'
            ).count()
            
            failed = self.db.query(EmailQueue).filter(
                EmailQueue.created_at >= start_date,
                EmailQueue.created_at < end_date,
                EmailQueue.status == 'failed'
            ).count()
            
            stats.append({
                "date": start_date.strftime('%Y-%m-%d'),
                "total": total,
                "sent": sent,
                "failed": failed
            })
        
        return stats

    def get_email_stats_by_type(self) -> Dict[str, Any]:
        """按邮件类型统计"""
        type_stats = self.db.query(
            EmailQueue.email_type,
            func.count(EmailQueue.id).label('count')
        ).group_by(EmailQueue.email_type).all()
        
        return {
            "by_type": {stat.email_type or 'unknown': stat.count for stat in type_stats},
            "total_types": len(type_stats)
        }
    
    def send_verification_email(self, email: str, username: str, verification_url: str) -> bool:
        """发送邮箱验证邮件"""
        try:
            subject = "邮箱验证 - XBoard Modern"
            html_content = f"""
            <html>
            <body>
                <h2>邮箱验证</h2>
                <p>亲爱的 {username}，</p>
                <p>感谢您注册 XBoard Modern！请点击下面的链接验证您的邮箱：</p>
                <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">验证邮箱</a></p>
                <p>如果按钮无法点击，请复制以下链接到浏览器中打开：</p>
                <p>{verification_url}</p>
                <p>此链接24小时内有效。</p>
                <p>如果您没有注册此账户，请忽略此邮件。</p>
                <br>
                <p>此邮件由系统自动发送，请勿回复。</p>
            </body>
            </html>
            """
            
            text_content = f"""
            邮箱验证
            
            亲爱的 {username}，
            
            感谢您注册 XBoard Modern！请点击下面的链接验证您的邮箱：
            {verification_url}
            
            此链接24小时内有效。
            
            如果您没有注册此账户，请忽略此邮件。
            
            此邮件由系统自动发送，请勿回复。
            """
            
            # 创建邮件队列
            email_data = {
                "to_email": email,
                "subject": subject,
                "html_content": html_content,
                "text_content": text_content,
                "email_type": "verification"
            }
            
            self.create_email_queue(EmailQueueCreate(**email_data))
            return True
            
        except Exception as e:
            print(f"创建验证邮件失败: {e}")
            return False
    
    def send_password_reset_email(self, email: str, username: str, reset_url: str) -> bool:
        """发送密码重置邮件"""
        try:
            subject = "密码重置 - XBoard Modern"
            html_content = f"""
            <html>
            <body>
                <h2>密码重置</h2>
                <p>亲爱的 {username}，</p>
                <p>您请求重置密码。请点击下面的链接重置您的密码：</p>
                <p><a href="{reset_url}" style="background-color: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">重置密码</a></p>
                <p>如果按钮无法点击，请复制以下链接到浏览器中打开：</p>
                <p>{reset_url}</p>
                <p>此链接1小时内有效。</p>
                <p>如果您没有请求重置密码，请忽略此邮件。</p>
                <br>
                <p>此邮件由系统自动发送，请勿回复。</p>
            </body>
            </html>
            """
            
            text_content = f"""
            密码重置
            
            亲爱的 {username}，
            
            您请求重置密码。请点击下面的链接重置您的密码：
            {reset_url}
            
            此链接1小时内有效。
            
            如果您没有请求重置密码，请忽略此邮件。
            
            此邮件由系统自动发送，请勿回复。
            """
            
            # 创建邮件队列
            email_data = {
                "to_email": email,
                "subject": subject,
                "html_content": html_content,
                "text_content": text_content,
                "email_type": "password_reset"
            }
            
            self.create_email_queue(EmailQueueCreate(**email_data))
            return True
            
        except Exception as e:
            print(f"创建重置邮件失败: {e}")
            return False

    def send_order_confirmation_email(self, user_email: str, username: str, order_data: Dict[str, Any]) -> bool:
        """发送下单确认邮件"""
        if not self.is_email_enabled():
            return False
        
        try:
            # 使用增强版模板发送下单确认邮件
            html_content = EmailTemplateEnhanced.get_order_confirmation_template(username, order_data)
            
            # 创建邮件队列
            email_data = EmailQueueCreate(
                to_email=user_email,
                subject="订单确认 - 网络服务",
                content=html_content,
                content_type='html',
                email_type='order_confirmation'
            )
            
            email_queue = self.create_email_queue(email_data)
            return self.send_email(email_queue)
            
        except Exception as e:
            # 如果增强模板失败，使用默认内容
            print(f"使用增强模板发送下单确认邮件失败，使用默认内容: {e}")
            return self._send_default_order_confirmation_email(user_email, username, order_data)

    def send_payment_success_email(self, user_email: str, username: str, payment_data: Dict[str, Any]) -> bool:
        """发送支付成功邮件"""
        if not self.is_email_enabled():
            return False
        
        try:
            # 使用增强版模板发送支付成功邮件
            html_content = EmailTemplateEnhanced.get_payment_success_template(username, payment_data)
            
            # 创建邮件队列
            email_data = EmailQueueCreate(
                to_email=user_email,
                subject="支付成功 - 网络服务",
                content=html_content,
                content_type='html',
                email_type='payment_success'
            )
            
            email_queue = self.create_email_queue(email_data)
            return self.send_email(email_queue)
            
        except Exception as e:
            # 如果增强模板失败，使用默认内容
            print(f"使用增强模板发送支付成功邮件失败，使用默认内容: {e}")
            return self._send_default_payment_success_email(user_email, username, payment_data)

    def send_account_deletion_email(self, user_email: str, username: str, deletion_data: Dict[str, Any]) -> bool:
        """发送账号删除确认邮件"""
        if not self.is_email_enabled():
            return False
        
        try:
            # 使用增强版模板发送账号删除邮件
            html_content = EmailTemplateEnhanced.get_account_deletion_template(username, deletion_data)
            
            # 创建邮件队列
            email_data = EmailQueueCreate(
                to_email=user_email,
                subject="账号删除确认 - 网络服务",
                content=html_content,
                content_type='html',
                email_type='account_deletion'
            )
            
            email_queue = self.create_email_queue(email_data)
            return self.send_email(email_queue)
            
        except Exception as e:
            # 如果增强模板失败，使用默认内容
            print(f"使用增强模板发送账号删除邮件失败，使用默认内容: {e}")
            return self._send_default_account_deletion_email(user_email, username, deletion_data)

    def send_renewal_confirmation_email(self, user_email: str, username: str, renewal_data: Dict[str, Any]) -> bool:
        """发送续费确认邮件"""
        if not self.is_email_enabled():
            return False
        
        try:
            # 使用增强版模板发送续费确认邮件
            html_content = EmailTemplateEnhanced.get_renewal_confirmation_template(username, renewal_data)
            
            # 创建邮件队列
            email_data = EmailQueueCreate(
                to_email=user_email,
                subject="续费成功 - 网络服务",
                content=html_content,
                content_type='html',
                email_type='renewal_confirmation'
            )
            
            email_queue = self.create_email_queue(email_data)
            return self.send_email(email_queue)
            
        except Exception as e:
            # 如果增强模板失败，使用默认内容
            print(f"使用增强模板发送续费确认邮件失败，使用默认内容: {e}")
            return self._send_default_renewal_confirmation_email(user_email, username, renewal_data)

    def _send_default_order_confirmation_email(self, user_email: str, username: str, order_data: Dict[str, Any]) -> bool:
        """发送默认下单确认邮件"""
        site_name = settings_manager.get_site_name(self.db)
        
        subject = f"{site_name} - 订单确认"
        content = f"""
        <html>
        <body>
            <h2>订单确认</h2>
            <p>亲爱的 {username}，</p>
            <p>感谢您的订单！您的订单详情如下：</p>
            <ul>
                <li>订单号: {order_data.get('order_no')}</li>
                <li>套餐名称: {order_data.get('package_name')}</li>
                <li>订单金额: ¥{order_data.get('amount')}</li>
                <li>支付方式: {order_data.get('payment_method')}</li>
                <li>下单时间: {order_data.get('created_at')}</li>
            </ul>
            <p>请及时完成支付以激活服务。</p>
            <p>感谢您使用 {site_name}！</p>
        </body>
        </html>
        """
        
        email_data = EmailQueueCreate(
            to_email=user_email,
            subject=subject,
            content=content,
            content_type='html',
            email_type='order_confirmation'
        )
        
        email_queue = self.create_email_queue(email_data)
        return self.send_email(email_queue)

    def _send_default_payment_success_email(self, user_email: str, username: str, payment_data: Dict[str, Any]) -> bool:
        """发送默认支付成功邮件"""
        site_name = settings_manager.get_site_name(self.db)
        
        subject = f"{site_name} - 支付成功"
        content = f"""
        <html>
        <body>
            <h2>支付成功</h2>
            <p>亲爱的 {username}，</p>
            <p>恭喜！您的支付已成功完成。</p>
            <ul>
                <li>订单号: {payment_data.get('order_no')}</li>
                <li>套餐名称: {payment_data.get('package_name')}</li>
                <li>支付金额: ¥{payment_data.get('amount')}</li>
                <li>支付方式: {payment_data.get('payment_method')}</li>
                <li>交易时间: {payment_data.get('paid_at')}</li>
                <li>交易ID: {payment_data.get('transaction_id')}</li>
            </ul>
            <p>您的服务已激活，现在可以开始使用了！</p>
            <p>感谢您使用 {site_name}！</p>
        </body>
        </html>
        """
        
        email_data = EmailQueueCreate(
            to_email=user_email,
            subject=subject,
            content=content,
            content_type='html',
            email_type='payment_success'
        )
        
        email_queue = self.create_email_queue(email_data)
        return self.send_email(email_queue)

    def _send_default_account_deletion_email(self, user_email: str, username: str, deletion_data: Dict[str, Any]) -> bool:
        """发送默认账号删除邮件"""
        site_name = settings_manager.get_site_name(self.db)
        
        subject = f"{site_name} - 账号删除确认"
        content = f"""
        <html>
        <body>
            <h2>账号删除确认</h2>
            <p>亲爱的 {username}，</p>
            <p>您的账号删除请求已处理完成。</p>
            <ul>
                <li>删除原因: {deletion_data.get('reason')}</li>
                <li>删除时间: {deletion_data.get('deletion_date')}</li>
                <li>数据保留期: {deletion_data.get('data_retention_period', '30天')}</li>
            </ul>
            <p>您的所有数据将在保留期结束后永久删除。</p>
            <p>感谢您曾经使用 {site_name}！</p>
        </body>
        </html>
        """
        
        email_data = EmailQueueCreate(
            to_email=user_email,
            subject=subject,
            content=content,
            content_type='html',
            email_type='account_deletion'
        )
        
        email_queue = self.create_email_queue(email_data)
        return self.send_email(email_queue)

    def _send_default_renewal_confirmation_email(self, user_email: str, username: str, renewal_data: Dict[str, Any]) -> bool:
        """发送默认续费确认邮件"""
        site_name = settings_manager.get_site_name(self.db)
        
        subject = f"{site_name} - 续费成功"
        content = f"""
        <html>
        <body>
            <h2>续费成功</h2>
            <p>亲爱的 {username}，</p>
            <p>您的订阅续费已成功完成！</p>
            <ul>
                <li>套餐名称: {renewal_data.get('package_name')}</li>
                <li>原到期时间: {renewal_data.get('old_expiry_date')}</li>
                <li>新到期时间: {renewal_data.get('new_expiry_date')}</li>
                <li>续费金额: ¥{renewal_data.get('amount')}</li>
                <li>续费时间: {renewal_data.get('renewal_date')}</li>
            </ul>
            <p>您的服务已延长，可以继续正常使用。</p>
            <p>感谢您使用 {site_name}！</p>
        </body>
        </html>
        """
        
        email_data = EmailQueueCreate(
            to_email=user_email,
            subject=subject,
            content=content,
            content_type='html',
            email_type='renewal_confirmation'
        )
        
        email_queue = self.create_email_queue(email_data)
        return self.send_email(email_queue) 