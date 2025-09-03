#!/usr/bin/env python3
"""
添加50个测试普通用户
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.subscription import Subscription
from datetime import datetime, timedelta
import random
import string

def generate_random_string(length=8):
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def add_test_users():
    """添加50个测试普通用户"""
    db = SessionLocal()
    
    try:
        print("开始添加测试用户...")
        
        # 检查是否已有测试用户
        existing_test_users = db.query(User).filter(User.username.like('testuser%')).count()
        if existing_test_users > 0:
            print(f"发现已有 {existing_test_users} 个测试用户，跳过创建")
            return
        
        users_created = 0
        for i in range(1, 51):
            # 生成随机用户名和邮箱
            username = f"testuser{i:02d}"
            email = f"testuser{i:02d}@example.com"
            
            # 检查是否已存在
            if db.query(User).filter(User.username == username).first():
                print(f"用户 {username} 已存在，跳过")
                continue
                
            if db.query(User).filter(User.email == email).first():
                print(f"邮箱 {email} 已存在，跳过")
                continue
            
            # 创建用户
            user = User(
                username=username,
                email=email,
                hashed_password="test123",  # 简单密码用于测试
                is_active=True,
                is_admin=False,  # 普通用户，不是管理员
                is_verified=True,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # 为部分用户创建订阅（模拟真实情况）
            if random.random() < 0.7:  # 70%的用户有订阅
                subscription = Subscription(
                    user_id=user.id,
                    subscription_url=generate_random_string(16),
                    device_limit=random.randint(1, 5),
                    current_devices=random.randint(0, 3),
                    is_active=True,
                    expire_time=datetime.utcnow() + timedelta(days=random.randint(30, 365))
                )
                db.add(subscription)
            
            users_created += 1
            if i % 10 == 0:
                print(f"已创建 {i} 个用户...")
        
        db.commit()
        print(f"成功创建 {users_created} 个测试用户")
        
        # 显示统计信息
        total_users = db.query(User).count()
        admin_users = db.query(User).filter(User.is_admin == True).count()
        regular_users = db.query(User).filter(User.is_admin == False).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        
        print(f"\n数据库统计:")
        print(f"总用户数: {total_users}")
        print(f"管理员用户: {admin_users}")
        print(f"普通用户: {regular_users}")
        print(f"激活用户: {active_users}")
        
    except Exception as e:
        print(f"创建用户时出错: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_users()
