import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings

def send_email(
    to_email: str,
    subject: str,
    content: str,
    html_content: Optional[str] = None
) -> bool:
    """发送邮件"""
    try:
        # 创建邮件对象
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        # 添加纯文本内容
        text_part = MIMEText(content, 'plain', 'utf-8')
        msg.attach(text_part)

        # 添加HTML内容（如果提供）
        if html_content:
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

        # 连接SMTP服务器并发送
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"发送邮件失败: {e}")
        return False

def send_verification_email(to_email: str, username: str, verification_url: str) -> bool:
    """发送验证邮件"""
    subject = "XBoard Modern - 邮箱验证"
    content = f"""
    您好 {username}，

    感谢您注册 XBoard Modern！

    请点击以下链接验证您的邮箱：
    {verification_url}

    如果您没有注册账户，请忽略此邮件。

    此链接将在24小时后失效。

    祝好，
    XBoard Modern 团队
    """
    
    html_content = f"""
    <html>
    <body>
        <h2>XBoard Modern - 邮箱验证</h2>
        <p>您好 {username}，</p>
        <p>感谢您注册 XBoard Modern！</p>
        <p>请点击以下按钮验证您的邮箱：</p>
        <p><a href="{verification_url}" style="background-color: #1677ff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">验证邮箱</a></p>
        <p>或者复制以下链接到浏览器：</p>
        <p>{verification_url}</p>
        <p>如果您没有注册账户，请忽略此邮件。</p>
        <p>此链接将在24小时后失效。</p>
        <br>
        <p>祝好，<br>XBoard Modern 团队</p>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, content, html_content)

def send_password_reset_email(to_email: str, username: str, reset_url: str) -> bool:
    """发送密码重置邮件"""
    subject = "XBoard Modern - 密码重置"
    content = f"""
    您好 {username}，

    我们收到了您的密码重置请求。

    请点击以下链接重置您的密码：
    {reset_url}

    如果您没有请求重置密码，请忽略此邮件。

    此链接将在1小时后失效。

    祝好，
    XBoard Modern 团队
    """
    
    html_content = f"""
    <html>
    <body>
        <h2>XBoard Modern - 密码重置</h2>
        <p>您好 {username}，</p>
        <p>我们收到了您的密码重置请求。</p>
        <p>请点击以下按钮重置您的密码：</p>
        <p><a href="{reset_url}" style="background-color: #1677ff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">重置密码</a></p>
        <p>或者复制以下链接到浏览器：</p>
        <p>{reset_url}</p>
        <p>如果您没有请求重置密码，请忽略此邮件。</p>
        <p>此链接将在1小时后失效。</p>
        <br>
        <p>祝好，<br>XBoard Modern 团队</p>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, content, html_content)

def send_subscription_expiry_reminder(to_email: str, username: str, days_left: int) -> bool:
    """发送订阅到期提醒邮件"""
    subject = f"XBoard Modern - 订阅即将到期提醒"
    content = f"""
    您好 {username}，

    您的订阅将在 {days_left} 天后到期。

    请及时续费以继续使用我们的服务。

    登录地址：https://yourdomain.com

    祝好，
    XBoard Modern 团队
    """
    
    html_content = f"""
    <html>
    <body>
        <h2>XBoard Modern - 订阅即将到期提醒</h2>
        <p>您好 {username}，</p>
        <p>您的订阅将在 <strong>{days_left}</strong> 天后到期。</p>
        <p>请及时续费以继续使用我们的服务。</p>
        <p><a href="https://yourdomain.com" style="background-color: #1677ff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">立即续费</a></p>
        <br>
        <p>祝好，<br>XBoard Modern 团队</p>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, content, html_content) 