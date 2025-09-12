#!/usr/bin/env python3
"""
清理孤立订单脚本
删除用户已删除但订单仍然存在的记录
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.order import Order
from app.models.user import User
from app.models.subscription import Subscription
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, text

def cleanup_orphaned_orders():
    """清理孤立的订单"""
    db = next(get_db())
    try:
        print("=== 开始清理孤立订单 ===")
        
        # 查找用户已删除的订单
        orders_with_deleted_users = db.query(Order).outerjoin(User).filter(
            and_(Order.user_id.isnot(None), User.id.is_(None))
        ).all()
        
        print(f"找到 {len(orders_with_deleted_users)} 个孤立订单")
        
        if not orders_with_deleted_users:
            print("没有需要清理的孤立订单")
            return
        
        # 显示要删除的订单信息
        print("\n=== 要删除的订单列表 ===")
        for order in orders_with_deleted_users:
            print(f"订单ID: {order.id}, 订单号: {order.order_no}, 用户ID: {order.user_id}, 金额: {order.amount}")
        
        # 确认删除
        confirm = input(f"\n确认删除这 {len(orders_with_deleted_users)} 个孤立订单吗？(y/N): ")
        if confirm.lower() != 'y':
            print("取消删除操作")
            return
        
        # 删除孤立订单（包括相关的支付交易记录）
        deleted_count = 0
        for order in orders_with_deleted_users:
            try:
                # 先删除相关的支付交易记录
                db.execute(text(f"DELETE FROM payment_transactions WHERE order_id = {order.id}"))
                
                # 删除订单
                db.delete(order)
                deleted_count += 1
                print(f"删除订单: {order.order_no}")
            except Exception as e:
                print(f"删除订单 {order.order_no} 失败: {e}")
        
        # 提交事务
        db.commit()
        print(f"\n=== 清理完成 ===")
        print(f"成功删除 {deleted_count} 个孤立订单")
        
        # 验证清理结果
        remaining_orphaned = db.query(Order).outerjoin(User).filter(
            and_(Order.user_id.isnot(None), User.id.is_(None))
        ).count()
        
        print(f"剩余孤立订单: {remaining_orphaned}")
        
    except Exception as e:
        db.rollback()
        print(f"清理过程中发生错误: {e}")
        raise
    finally:
        db.close()

def cleanup_orphaned_subscriptions():
    """清理孤立的订阅"""
    db = next(get_db())
    try:
        print("\n=== 开始清理孤立订阅 ===")
        
        # 查找用户已删除的订阅
        subscriptions_with_deleted_users = db.query(Subscription).outerjoin(User).filter(
            and_(Subscription.user_id.isnot(None), User.id.is_(None))
        ).all()
        
        print(f"找到 {len(subscriptions_with_deleted_users)} 个孤立订阅")
        
        if not subscriptions_with_deleted_users:
            print("没有需要清理的孤立订阅")
            return
        
        # 显示要删除的订阅信息
        print("\n=== 要删除的订阅列表 ===")
        for subscription in subscriptions_with_deleted_users:
            print(f"订阅ID: {subscription.id}, 用户ID: {subscription.user_id}, 状态: {subscription.status}")
        
        # 确认删除
        confirm = input(f"\n确认删除这 {len(subscriptions_with_deleted_users)} 个孤立订阅吗？(y/N): ")
        if confirm.lower() != 'y':
            print("取消删除操作")
            return
        
        # 删除孤立订阅
        deleted_count = 0
        for subscription in subscriptions_with_deleted_users:
            try:
                db.delete(subscription)
                deleted_count += 1
                print(f"删除订阅ID: {subscription.id}")
            except Exception as e:
                print(f"删除订阅 {subscription.id} 失败: {e}")
        
        # 提交事务
        db.commit()
        print(f"\n=== 订阅清理完成 ===")
        print(f"成功删除 {deleted_count} 个孤立订阅")
        
        # 验证清理结果
        remaining_orphaned = db.query(Subscription).outerjoin(User).filter(
            and_(Subscription.user_id.isnot(None), User.id.is_(None))
        ).count()
        
        print(f"剩余孤立订阅: {remaining_orphaned}")
        
    except Exception as e:
        db.rollback()
        print(f"清理订阅过程中发生错误: {e}")
        raise
    finally:
        db.close()

def main():
    """主函数"""
    print("孤立数据清理工具")
    print("=" * 50)
    
    try:
        # 清理孤立订单
        cleanup_orphaned_orders()
        
        # 清理孤立订阅
        cleanup_orphaned_subscriptions()
        
        print("\n=== 清理完成 ===")
        print("所有孤立数据已清理完毕")
        
    except Exception as e:
        print(f"清理过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
