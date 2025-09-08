"""
订阅相关定时任务
"""
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.subscription_manager import SubscriptionManager


async def check_expired_subscriptions():
    """检查并处理过期的订阅"""
    db = next(get_db())
    try:
        subscription_manager = SubscriptionManager(db)
        expired_count = subscription_manager.check_expired_subscriptions()
        
        if expired_count > 0:
            print(f"处理了 {expired_count} 个过期订阅")
        
        return expired_count
    except Exception as e:
        print(f"检查过期订阅失败: {e}")
        return 0
    finally:
        db.close()


def run_subscription_check():
    """运行订阅检查任务（同步版本，用于定时任务）"""
    db = next(get_db())
    try:
        subscription_manager = SubscriptionManager(db)
        expired_count = subscription_manager.check_expired_subscriptions()
        
        if expired_count > 0:
            print(f"处理了 {expired_count} 个过期订阅")
        
        return expired_count
    except Exception as e:
        print(f"检查过期订阅失败: {e}")
        return 0
    finally:
        db.close()
