"""
通知相关定时任务
"""
import asyncio
import schedule
import time
import threading
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.notification_service import NotificationService
from app.services.subscription_manager import SubscriptionManager


class NotificationScheduler:
    """通知调度器"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """启动定时任务"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        print("通知定时任务已启动")
    
    def stop(self):
        """停止定时任务"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("通知定时任务已停止")
    
    def _run_scheduler(self):
        """运行调度器"""
        # 设置定时任务
        self._setup_schedules()
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                print(f"定时任务执行错误: {e}")
                time.sleep(60)
    
    def _setup_schedules(self):
        """设置定时任务"""
        # 每天上午9点检查订阅到期提醒（7天前）
        schedule.every().day.at("09:00").do(self._check_subscription_expiry_7_days)
        
        # 每天上午9点检查订阅到期提醒（3天前）
        schedule.every().day.at("09:00").do(self._check_subscription_expiry_3_days)
        
        # 每天上午9点检查订阅到期提醒（1天前）
        schedule.every().day.at("09:00").do(self._check_subscription_expiry_1_day)
        
        # 每天上午10点检查已过期的订阅
        schedule.every().day.at("10:00").do(self._check_expired_subscriptions)
        
        # 每小时检查一次邮件队列
        schedule.every().hour.do(self._process_email_queue)
        
        print("定时任务已设置完成")
    
    def _check_subscription_expiry_7_days(self):
        """检查7天后到期的订阅"""
        try:
            db = next(get_db())
            notification_service = NotificationService(db)
            sent_count = notification_service.send_subscription_expiry_reminder(7)
            print(f"发送7天到期提醒: {sent_count} 封邮件")
        except Exception as e:
            print(f"检查7天到期订阅失败: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    def _check_subscription_expiry_3_days(self):
        """检查3天后到期的订阅"""
        try:
            db = next(get_db())
            notification_service = NotificationService(db)
            sent_count = notification_service.send_subscription_expiry_reminder(3)
            print(f"发送3天到期提醒: {sent_count} 封邮件")
        except Exception as e:
            print(f"检查3天到期订阅失败: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    def _check_subscription_expiry_1_day(self):
        """检查1天后到期的订阅"""
        try:
            db = next(get_db())
            notification_service = NotificationService(db)
            sent_count = notification_service.send_subscription_expiry_reminder(1)
            print(f"发送1天到期提醒: {sent_count} 封邮件")
        except Exception as e:
            print(f"检查1天到期订阅失败: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    def _check_expired_subscriptions(self):
        """检查已过期的订阅"""
        try:
            db = next(get_db())
            
            # 处理过期订阅
            subscription_manager = SubscriptionManager(db)
            expired_count = subscription_manager.check_expired_subscriptions()
            print(f"处理过期订阅: {expired_count} 个")
            
            # 发送过期通知
            notification_service = NotificationService(db)
            sent_count = notification_service.send_subscription_expired_notification()
            print(f"发送过期通知: {sent_count} 封邮件")
            
        except Exception as e:
            print(f"检查过期订阅失败: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    def _process_email_queue(self):
        """处理邮件队列"""
        try:
            db = next(get_db())
            from app.services.email_queue_processor import EmailQueueProcessor
            
            processor = EmailQueueProcessor()
            processor.process_pending_emails(db)
            print("邮件队列处理完成")
            
        except Exception as e:
            print(f"处理邮件队列失败: {e}")
        finally:
            if 'db' in locals():
                db.close()


# 全局调度器实例
notification_scheduler = NotificationScheduler()


def start_notification_scheduler():
    """启动通知调度器"""
    notification_scheduler.start()


def stop_notification_scheduler():
    """停止通知调度器"""
    notification_scheduler.stop()


# 手动执行任务的函数（用于测试）
def run_subscription_expiry_check(days: int = 7):
    """手动执行订阅到期检查"""
    db = next(get_db())
    try:
        notification_service = NotificationService(db)
        sent_count = notification_service.send_subscription_expiry_reminder(days)
        print(f"手动发送{days}天到期提醒: {sent_count} 封邮件")
        return sent_count
    except Exception as e:
        print(f"手动执行订阅到期检查失败: {e}")
        return 0
    finally:
        db.close()


def run_expired_subscription_check():
    """手动执行过期订阅检查"""
    db = next(get_db())
    try:
        notification_service = NotificationService(db)
        sent_count = notification_service.send_subscription_expired_notification()
        print(f"手动发送过期通知: {sent_count} 封邮件")
        return sent_count
    except Exception as e:
        print(f"手动执行过期订阅检查失败: {e}")
        return 0
    finally:
        db.close()


def get_notification_stats():
    """获取通知统计信息"""
    db = next(get_db())
    try:
        notification_service = NotificationService(db)
        stats = notification_service.get_notification_stats()
        return stats
    except Exception as e:
        print(f"获取通知统计失败: {e}")
        return {}
    finally:
        db.close()
