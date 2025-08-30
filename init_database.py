#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XBoard Modern 数据库初始化脚本
用于创建数据库表结构和初始数据
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app.core.database import engine, Base
from backend.app.core.config import settings
from backend.app.models import (
    User, Subscription, Device, Order, Package, 
    EmailQueue, Notification, EmailTemplate,
    SystemConfig, PaymentConfig,
    PaymentTransaction, PaymentCallback,
    Announcement, ThemeConfig
)
from backend.app.services.settings import SettingsService
from backend.app.core.database import get_db
from sqlalchemy.orm import sessionmaker

def create_tables():
    """创建数据库表"""
    print("正在创建数据库表...")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")

def init_default_settings():
    """初始化默认系统设置"""
    print("正在初始化默认系统设置...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        settings_service = SettingsService(db)
        
        # 初始化默认配置
        settings_service.initialize_default_configs()
        
        print("✅ 默认系统设置初始化完成")
        
    except Exception as e:
        print(f"❌ 初始化系统设置失败: {e}")
        db.rollback()
    finally:
        db.close()

def create_admin_user():
    """创建管理员用户"""
    print("正在创建管理员用户...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        from backend.app.services.user import UserService
        from backend.app.schemas.user import UserCreate
        
        user_service = UserService(db)
        
        # 检查是否已存在管理员用户
        admin_user = user_service.get_user_by_email("admin@xboard.com")
        if admin_user:
            print("✅ 管理员用户已存在")
            return
        
        # 创建管理员用户
        admin_data = UserCreate(
            email="admin@xboard.com",
            username="admin",
            password="admin123456",
            is_admin=True,
            is_active=True,
            email_verified=True
        )
        
        admin_user = user_service.create_user(admin_data)
        print(f"✅ 管理员用户创建成功: {admin_user.email}")
        print("   用户名: admin")
        print("   密码: admin123456")
        print("   请及时修改密码！")
        
    except Exception as e:
        print(f"❌ 创建管理员用户失败: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_data():
    """创建示例数据"""
    print("正在创建示例数据...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 创建示例套餐
        from backend.app.services.package import PackageService
        from backend.app.schemas.package import PackageCreate
        
        package_service = PackageService(db)
        
        packages = [
            {
                "name": "基础套餐",
                "description": "适合个人用户的基础套餐",
                "price": 9.90,
                "duration_days": 30,
                "traffic_limit_gb": 10,
                "device_limit": 1,
                "is_active": True
            },
            {
                "name": "标准套餐",
                "description": "适合家庭用户的标准套餐",
                "price": 19.90,
                "duration_days": 30,
                "traffic_limit_gb": 50,
                "device_limit": 3,
                "is_active": True
            },
            {
                "name": "高级套餐",
                "description": "适合企业用户的高级套餐",
                "price": 39.90,
                "duration_days": 30,
                "traffic_limit_gb": 200,
                "device_limit": 10,
                "is_active": True
            }
        ]
        
        for package_data in packages:
            package_create = PackageCreate(**package_data)
            package_service.create_package(package_create)
        
        print("✅ 示例套餐创建完成")
        
        # 创建示例节点
        from backend.app.services.node import NodeService
        from backend.app.schemas.node import NodeCreate
        
        node_service = NodeService(db)
        
        nodes = [
            {
                "name": "香港节点01",
                "description": "香港优质线路",
                "server": "hk01.xboard.com",
                "port": 443,
                "protocol": "vmess",
                "is_active": True
            },
            {
                "name": "新加坡节点01",
                "description": "新加坡优质线路",
                "server": "sg01.xboard.com",
                "port": 443,
                "protocol": "vmess",
                "is_active": True
            },
            {
                "name": "美国节点01",
                "description": "美国优质线路",
                "server": "us01.xboard.com",
                "port": 443,
                "protocol": "vmess",
                "is_active": True
            }
        ]
        
        for node_data in nodes:
            node_create = NodeCreate(**node_data)
            node_service.create_node(node_create)
        
        print("✅ 示例节点创建完成")
        
        # 创建示例公告
        from backend.app.services.settings import SettingsService
        
        settings_service = SettingsService(db)
        
        announcements = [
            {
                "title": "欢迎使用XBoard Modern",
                "content": "感谢您选择XBoard Modern面板系统，我们将为您提供优质的服务！",
                "type": "info",
                "is_active": True,
                "is_pinned": True,
                "target_users": "all",
                "created_by": 1
            },
            {
                "title": "系统维护通知",
                "content": "系统将于每周日凌晨2:00-4:00进行例行维护，期间可能影响服务使用。",
                "type": "warning",
                "is_active": True,
                "is_pinned": False,
                "target_users": "all",
                "created_by": 1
            }
        ]
        
        for announcement_data in announcements:
            settings_service.create_announcement(announcement_data)
        
        print("✅ 示例公告创建完成")
        
    except Exception as e:
        print(f"❌ 创建示例数据失败: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """主函数"""
    print("=" * 50)
    print("XBoard Modern 数据库初始化")
    print("=" * 50)
    
    # 检查环境变量文件
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ 未找到 .env 文件，请先配置环境变量")
        print("   复制 env.example 为 .env 并修改配置")
        return
    
    try:
        # 创建数据库表
        create_tables()
        
        # 初始化默认设置
        init_default_settings()
        
        # 创建管理员用户
        create_admin_user()
        
        # 创建示例数据
        create_sample_data()
        
        print("\n" + "=" * 50)
        print("✅ 数据库初始化完成！")
        print("=" * 50)
        print("\n下一步操作:")
        print("1. 启动后端服务: python -m uvicorn main:app --host 0.0.0.0 --port 8000")
        print("2. 访问管理后台: http://localhost:8000/admin")
        print("3. 使用管理员账号登录: admin@xboard.com / admin123456")
        print("4. 及时修改管理员密码")
        print("5. 配置邮件服务器和支付设置")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 