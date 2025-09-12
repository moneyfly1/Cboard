#!/usr/bin/env python3
"""
清空数据库中所有用户的订单记录脚本
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.order import Order
from app.models.payment import PaymentTransaction
from app.models.user import User

def clear_all_orders():
    """清空所有用户的订单记录"""
    db = SessionLocal()
    
    try:
        print("开始清空所有订单记录...")
        print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 统计删除前的数据
        total_orders = db.query(Order).count()
        total_payments = db.query(PaymentTransaction).count()
        total_users = db.query(User).count()
        
        print(f"删除前统计:")
        print(f"  - 订单总数: {total_orders}")
        print(f"  - 支付交易总数: {total_payments}")
        print(f"  - 用户总数: {total_users}")
        
        if total_orders == 0:
            print("数据库中没有订单记录，无需清空。")
            return
        
        # 2. 确认操作
        confirm = input(f"\n确定要删除所有 {total_orders} 个订单记录吗？(输入 'yes' 确认): ")
        if confirm.lower() != 'yes':
            print("操作已取消。")
            return
        
        # 3. 删除所有支付交易记录（先删除外键依赖）
        print("\n正在删除支付交易记录...")
        payment_count = db.query(PaymentTransaction).count()
        db.query(PaymentTransaction).delete()
        print(f"已删除 {payment_count} 个支付交易记录")
        
        # 4. 删除所有订单记录
        print("正在删除订单记录...")
        order_count = db.query(Order).count()
        db.query(Order).delete()
        print(f"已删除 {order_count} 个订单记录")
        
        # 5. 提交事务
        db.commit()
        print("\n✅ 所有订单记录已成功清空！")
        
        # 6. 验证删除结果
        remaining_orders = db.query(Order).count()
        remaining_payments = db.query(PaymentTransaction).count()
        
        print(f"\n删除后统计:")
        print(f"  - 剩余订单数: {remaining_orders}")
        print(f"  - 剩余支付交易数: {remaining_payments}")
        print(f"  - 用户总数: {total_users} (保持不变)")
        
        if remaining_orders == 0 and remaining_payments == 0:
            print("✅ 验证成功：所有订单和支付记录已完全清空")
        else:
            print("⚠️  警告：仍有部分记录未删除")
            
    except Exception as e:
        print(f"❌ 清空订单记录时发生错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def show_order_statistics():
    """显示订单统计信息"""
    db = SessionLocal()
    
    try:
        print("=== 订单统计信息 ===")
        print(f"统计时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 基本统计
        total_orders = db.query(Order).count()
        total_payments = db.query(PaymentTransaction).count()
        total_users = db.query(User).count()
        
        print(f"\n基本统计:")
        print(f"  - 订单总数: {total_orders}")
        print(f"  - 支付交易总数: {total_payments}")
        print(f"  - 用户总数: {total_users}")
        
        if total_orders > 0:
            # 按状态统计订单
            from sqlalchemy import func
            status_stats = db.query(
                Order.status, 
                func.count(Order.id).label('count')
            ).group_by(Order.status).all()
            
            print(f"\n订单状态统计:")
            for status, count in status_stats:
                print(f"  - {status}: {count}")
            
            # 按用户统计订单
            user_order_stats = db.query(
                Order.user_id,
                func.count(Order.id).label('order_count')
            ).group_by(Order.user_id).order_by(func.count(Order.id).desc()).limit(10).all()
            
            print(f"\n用户订单数量排行 (前10名):")
            for user_id, count in user_order_stats:
                user = db.query(User).filter(User.id == user_id).first()
                username = user.username if user else f"用户ID:{user_id}"
                print(f"  - {username}: {count} 个订单")
        
    except Exception as e:
        print(f"❌ 获取统计信息时发生错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("=== 订单管理工具 ===")
    print("1. 显示订单统计信息")
    print("2. 清空所有订单记录")
    print("3. 退出")
    
    while True:
        choice = input("\n请选择操作 (1-3): ").strip()
        
        if choice == "1":
            show_order_statistics()
        elif choice == "2":
            clear_all_orders()
        elif choice == "3":
            print("退出程序。")
            break
        else:
            print("无效选择，请输入 1-3。")
