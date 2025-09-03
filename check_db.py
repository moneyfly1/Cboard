#!/usr/bin/env python3
"""
检查数据库中的用户数据
"""

import sqlite3
import os

def check_database():
    """检查数据库"""
    
    db_path = "xboard.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("数据库连接成功")
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"数据库中的表: {[table[0] for table in tables]}")
        
        # 检查用户表
        if ('users',) in tables:
            print("\n检查用户表...")
            cursor.execute("SELECT * FROM users LIMIT 5")
            users = cursor.fetchall()
            
            if users:
                print(f"用户表中有 {len(users)} 条记录")
                for user in users:
                    print(f"  用户ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 是否激活: {user[4]}, 是否管理员: {user[5]}")
            else:
                print("用户表中没有数据")
                
            # 获取用户总数
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            print(f"用户总数: {total_users}")
            
            # 获取管理员用户
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
            admin_users = cursor.fetchone()[0]
            print(f"管理员用户数: {admin_users}")
            
        else:
            print("用户表不存在")
        
        # 检查订阅表
        if ('subscriptions',) in tables:
            print("\n检查订阅表...")
            cursor.execute("SELECT COUNT(*) FROM subscriptions")
            total_subscriptions = cursor.fetchone()[0]
            print(f"订阅总数: {total_subscriptions}")
            
            if total_subscriptions > 0:
                cursor.execute("SELECT * FROM subscriptions LIMIT 3")
                subscriptions = cursor.fetchall()
                for sub in subscriptions:
                    print(f"  订阅ID: {sub[0]}, 用户ID: {sub[1]}, 状态: {sub[4]}")
        
        # 检查设备表
        if ('devices',) in tables:
            print("\n检查设备表...")
            cursor.execute("SELECT COUNT(*) FROM devices")
            total_devices = cursor.fetchone()[0]
            print(f"设备总数: {total_devices}")
        
        conn.close()
        print("\n数据库检查完成")
        
    except Exception as e:
        print(f"检查数据库时出错: {e}")

def create_test_admin():
    """创建测试管理员用户"""
    
    db_path = "xboard.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查是否已有管理员用户
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        admin_count = cursor.fetchone()[0]
        
        if admin_count > 0:
            print(f"数据库中已有 {admin_count} 个管理员用户")
            conn.close()
            return
        
        # 创建测试管理员用户
        from app.utils.security import get_password_hash
        
        admin_password = get_password_hash("admin123")
        
        cursor.execute("""
            INSERT INTO users (username, email, hashed_password, is_active, is_verified, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, ("admin", "admin@example.com", admin_password, True, True, True))
        
        conn.commit()
        print("测试管理员用户创建成功")
        print("用户名: admin")
        print("密码: admin123")
        print("邮箱: admin@example.com")
        
        conn.close()
        
    except Exception as e:
        print(f"创建测试管理员用户时出错: {e}")

if __name__ == "__main__":
    print("开始检查数据库...")
    check_database()
    
    print("\n是否需要创建测试管理员用户？(y/n): ", end="")
    choice = input().strip().lower()
    
    if choice == 'y':
        create_test_admin()
    
    print("程序结束")
