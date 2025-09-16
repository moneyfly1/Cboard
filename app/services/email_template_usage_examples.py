"""
邮件模板使用示例
展示如何正确调用更新后的邮件模板函数
"""
from fastapi import Request
from sqlalchemy.orm import Session
from app.services.email_template_enhanced import EmailTemplateEnhanced


class EmailTemplateUsageExamples:
    """邮件模板使用示例类"""
    
    @staticmethod
    def send_subscription_email_example(subscription_id: int, request: Request, db: Session):
        """发送订阅邮件示例"""
        try:
            # 使用数据库数据生成邮件内容
            email_content = EmailTemplateEnhanced.get_subscription_template(
                subscription_id=subscription_id,
                request=request,
                db=db
            )
            
            # 检查是否生成成功
            if email_content in ["数据库连接不可用", "订阅信息不存在"]:
                print(f"邮件生成失败: {email_content}")
                return False
            
            # 这里可以调用邮件发送服务
            # send_email_service.send_email(email_content)
            print("订阅邮件生成成功")
            return True
            
        except Exception as e:
            print(f"发送订阅邮件失败: {str(e)}")
            return False
    
    @staticmethod
    def send_subscription_reset_email_example(subscription_id: int, reset_reason: str, request: Request, db: Session):
        """发送订阅重置邮件示例"""
        try:
            from datetime import datetime
            
            reset_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 使用数据库数据生成邮件内容
            email_content = EmailTemplateEnhanced.get_subscription_reset_template(
                subscription_id=subscription_id,
                reset_time=reset_time,
                reset_reason=reset_reason,
                request=request,
                db=db
            )
            
            # 检查是否生成成功
            if email_content in ["数据库连接不可用", "订阅信息不存在"]:
                print(f"邮件生成失败: {email_content}")
                return False
            
            # 这里可以调用邮件发送服务
            # send_email_service.send_email(email_content)
            print("订阅重置邮件生成成功")
            return True
            
        except Exception as e:
            print(f"发送订阅重置邮件失败: {str(e)}")
            return False
    
    @staticmethod
    def send_payment_success_email_example(order_id: int, request: Request, db: Session):
        """发送支付成功邮件示例"""
        try:
            # 使用数据库数据生成邮件内容
            email_content = EmailTemplateEnhanced.get_payment_success_template(
                order_id=order_id,
                request=request,
                db=db
            )
            
            # 检查是否生成成功
            if email_content in ["数据库连接不可用", "订单信息不存在"]:
                print(f"邮件生成失败: {email_content}")
                return False
            
            # 这里可以调用邮件发送服务
            # send_email_service.send_email(email_content)
            print("支付成功邮件生成成功")
            return True
            
        except Exception as e:
            print(f"发送支付成功邮件失败: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email_example(user_id: int, request: Request, db: Session):
        """发送欢迎邮件示例"""
        try:
            # 使用数据库数据生成邮件内容
            email_content = EmailTemplateEnhanced.get_welcome_template(
                user_id=user_id,
                request=request,
                db=db
            )
            
            # 检查是否生成成功
            if email_content in ["数据库连接不可用", "用户信息不存在"]:
                print(f"邮件生成失败: {email_content}")
                return False
            
            # 这里可以调用邮件发送服务
            # send_email_service.send_email(email_content)
            print("欢迎邮件生成成功")
            return True
            
        except Exception as e:
            print(f"发送欢迎邮件失败: {str(e)}")
            return False
    
    @staticmethod
    def send_expiration_email_example(subscription_id: int, is_expired: bool, request: Request, db: Session):
        """发送到期提醒邮件示例"""
        try:
            # 使用数据库数据生成邮件内容
            email_content = EmailTemplateEnhanced.get_expiration_template(
                subscription_id=subscription_id,
                is_expired=is_expired,
                request=request,
                db=db
            )
            
            # 检查是否生成成功
            if email_content in ["数据库连接不可用", "订阅信息不存在"]:
                print(f"邮件生成失败: {email_content}")
                return False
            
            # 这里可以调用邮件发送服务
            # send_email_service.send_email(email_content)
            print("到期提醒邮件生成成功")
            return True
            
        except Exception as e:
            print(f"发送到期提醒邮件失败: {str(e)}")
            return False
    
    @staticmethod
    def send_subscription_created_email_example(subscription_id: int, request: Request, db: Session):
        """发送订阅创建成功邮件示例"""
        try:
            # 使用数据库数据生成邮件内容
            email_content = EmailTemplateEnhanced.get_subscription_created_template(
                subscription_id=subscription_id,
                request=request,
                db=db
            )
            
            # 检查是否生成成功
            if email_content in ["数据库连接不可用", "订阅信息不存在"]:
                print(f"邮件生成失败: {email_content}")
                return False
            
            # 这里可以调用邮件发送服务
            # send_email_service.send_email(email_content)
            print("订阅创建成功邮件生成成功")
            return True
            
        except Exception as e:
            print(f"发送订阅创建成功邮件失败: {str(e)}")
            return False


# 使用示例
def example_usage():
    """使用示例"""
    # 这些函数现在需要以下参数：
    # 1. ID参数（subscription_id, order_id, user_id）
    # 2. request对象（用于获取域名信息）
    # 3. db会话（用于数据库查询）
    
    # 示例调用：
    # EmailTemplateUsageExamples.send_subscription_email_example(
    #     subscription_id=123,
    #     request=request,
    #     db=db
    # )
    
    # EmailTemplateUsageExamples.send_payment_success_email_example(
    #     order_id=456,
    #     request=request,
    #     db=db
    # )
    
    # EmailTemplateUsageExamples.send_welcome_email_example(
    #     user_id=789,
    #     request=request,
    #     db=db
    # )
    
    pass
