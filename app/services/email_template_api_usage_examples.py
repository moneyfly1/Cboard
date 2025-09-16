"""
邮件模板API使用示例
展示如何使用新的EmailAPIClient来获取邮件模板数据
"""
from fastapi import Request
from sqlalchemy.orm import Session
from app.services.email_template_enhanced import EmailTemplateEnhanced
from app.services.email_api_client import EmailAPIClient


def example_usage():
    """使用示例"""
    
    # 假设我们有request和db对象
    request = None  # 实际的Request对象
    db = None       # 实际的Session对象
    
    # 1. 订阅重置通知邮件
    subscription_id = 123
    reset_time = "2024-01-15 10:30:00"
    reset_reason = "管理员重置"
    
    reset_email = EmailTemplateEnhanced.get_subscription_reset_template(
        subscription_id=subscription_id,
        reset_time=reset_time,
        reset_reason=reset_reason,
        request=request,
        db=db
    )
    print("订阅重置邮件:", reset_email)
    
    # 2. 订阅创建成功邮件
    created_email = EmailTemplateEnhanced.get_subscription_created_template(
        subscription_id=subscription_id,
        request=request,
        db=db
    )
    print("订阅创建邮件:", created_email)
    
    # 3. 订阅信息邮件
    subscription_email = EmailTemplateEnhanced.get_subscription_template(
        subscription_id=subscription_id,
        request=request,
        db=db
    )
    print("订阅信息邮件:", subscription_email)
    
    # 4. 支付成功通知邮件
    order_id = 456
    payment_email = EmailTemplateEnhanced.get_payment_success_template(
        order_id=order_id,
        request=request,
        db=db
    )
    print("支付成功邮件:", payment_email)
    
    # 5. 新用户欢迎邮件
    user_id = 789
    welcome_email = EmailTemplateEnhanced.get_welcome_template(
        user_id=user_id,
        request=request,
        db=db
    )
    print("欢迎邮件:", welcome_email)
    
    # 6. 到期提醒邮件
    expiration_email = EmailTemplateEnhanced.get_expiration_template(
        subscription_id=subscription_id,
        is_expired=False,
        request=request,
        db=db
    )
    print("到期提醒邮件:", expiration_email)


def direct_api_usage():
    """直接使用API客户端的示例"""
    
    request = None  # 实际的Request对象
    db = None       # 实际的Session对象
    
    # 创建API客户端
    api_client = EmailAPIClient(request, db)
    
    # 获取用户信息
    user_id = 123
    user_info = api_client.get_user_info(user_id)
    print("用户信息:", user_info)
    
    # 获取订阅信息
    subscription_id = 456
    subscription_info = api_client.get_subscription_info(subscription_id)
    print("订阅信息:", subscription_info)
    
    # 获取订阅地址
    subscription_urls = api_client.get_subscription_urls(subscription_id)
    print("订阅地址:", subscription_urls)
    
    # 获取完整订阅数据
    complete_data = api_client.get_complete_subscription_data(subscription_id)
    print("完整订阅数据:", complete_data)
    
    # 获取订单信息
    order_id = 789
    order_info = api_client.get_order_info(order_id)
    print("订单信息:", order_info)


def api_endpoints_used():
    """使用的API端点列表"""
    
    endpoints = {
        "用户信息": "/api/v1/users/{user_id}",
        "订阅信息": "/api/v1/subscriptions/{subscription_id}",
        "用户仪表板": "/api/v1/users/dashboard",
        "订单信息": "/api/v1/orders/{order_id}",
        "V2Ray订阅": "/api/v1/subscriptions/{subscription_id}/v2ray",
        "Clash订阅": "/api/v1/subscriptions/{subscription_id}/clash",
        "SSR订阅": "/api/v1/subscriptions/{subscription_id}/ssr"
    }
    
    print("使用的API端点:")
    for name, endpoint in endpoints.items():
        print(f"  {name}: {endpoint}")


def data_structure_example():
    """数据结构示例"""
    
    # 用户信息数据结构
    user_data_example = {
        "id": 123,
        "username": "testuser",
        "email": "test@example.com",
        "nickname": "测试用户",
        "status": "active",
        "is_verified": True,
        "created_at": "2024-01-01 00:00:00",
        "last_login": "2024-01-15 10:30:00",
        "avatar_url": "",
        "phone": "",
        "country": "",
        "timezone": ""
    }
    
    # 订阅信息数据结构
    subscription_data_example = {
        "id": 456,
        "user_id": 123,
        "subscription_url": "abc123def456",
        "device_limit": 3,
        "current_devices": 1,
        "max_devices": 3,
        "is_active": True,
        "expire_time": "2024-12-31 23:59:59",
        "remaining_days": 350,
        "created_at": "2024-01-01 00:00:00",
        "updated_at": "2024-01-15 10:30:00",
        "username": "testuser",
        "user_email": "test@example.com",
        "package_name": "基础套餐",
        "package_description": "适合个人使用",
        "package_price": 29.9,
        "package_duration": 30,
        "package_bandwidth_limit": 100,
        "v2ray_url": "https://yourdomain.com/api/v1/subscriptions/ssr/abc123def456",
        "clash_url": "https://yourdomain.com/api/v1/subscriptions/clash/abc123def456",
        "ssr_url": "https://yourdomain.com/api/v1/subscriptions/ssr/abc123def456",
        "base_url": "https://yourdomain.com"
    }
    
    # 订单信息数据结构
    order_data_example = {
        "id": 789,
        "order_no": "ORD20240115001",
        "user_id": 123,
        "amount": 29.9,
        "status": "completed",
        "payment_method_name": "支付宝",
        "created_at": "2024-01-15 10:00:00",
        "updated_at": "2024-01-15 10:05:00",
        "username": "testuser",
        "user_email": "test@example.com",
        "package_name": "基础套餐",
        "package_description": "适合个人使用",
        "package_price": 29.9,
        "package_duration": 30,
        "base_url": "https://yourdomain.com"
    }
    
    print("用户信息数据结构示例:")
    print(user_data_example)
    print("\n订阅信息数据结构示例:")
    print(subscription_data_example)
    print("\n订单信息数据结构示例:")
    print(order_data_example)


if __name__ == "__main__":
    print("=== 邮件模板API使用示例 ===")
    example_usage()
    
    print("\n=== 直接API客户端使用示例 ===")
    direct_api_usage()
    
    print("\n=== 使用的API端点 ===")
    api_endpoints_used()
    
    print("\n=== 数据结构示例 ===")
    data_structure_example()
