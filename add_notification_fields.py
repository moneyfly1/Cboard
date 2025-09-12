#!/usr/bin/env python3
"""
添加用户通知设置字段的数据库迁移脚本
"""

import sqlite3
import json
from datetime import datetime

def add_notification_fields():
    """添加通知设置字段到用户表"""
    db_path = 'xboard.db'
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("开始添加通知设置字段...")
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 添加通知设置字段
        fields_to_add = [
            ("email_notifications", "BOOLEAN DEFAULT 1"),
            ("notification_types", "TEXT"),
            ("sms_notifications", "BOOLEAN DEFAULT 0"),
            ("push_notifications", "BOOLEAN DEFAULT 1")
        ]
        
        for field_name, field_type in fields_to_add:
            if field_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {field_name} {field_type}")
                    print(f"✅ 添加字段 {field_name}")
                except sqlite3.Error as e:
                    print(f"❌ 添加字段 {field_name} 失败: {e}")
            else:
                print(f"⚠️  字段 {field_name} 已存在，跳过")
        
        # 为现有用户设置默认通知类型
        cursor.execute("""
            UPDATE users 
            SET notification_types = ? 
            WHERE notification_types IS NULL
        """, (json.dumps(['subscription', 'payment', 'system']),))
        
        updated_count = cursor.rowcount
        print(f"✅ 为 {updated_count} 个用户设置了默认通知类型")
        
        # 提交更改
        conn.commit()
        print("✅ 数据库迁移完成")
        
    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_notification_fields()
