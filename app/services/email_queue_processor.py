import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.email import EmailQueue
from app.services.email import EmailService
from app.services.email_template import EmailTemplateService
from app.core.database import SessionLocal
import logging
import traceback

logger = logging.getLogger(__name__)

class EmailQueueProcessor:
    """邮件队列处理器 - 支持异步处理和重试机制"""
    
    def __init__(self):
        self.is_running = False
        self.processing_thread = None
        self.batch_size = 10
        self.processing_interval = 5  # 秒
        self.max_retries = 3
        self.retry_delays = [60, 300, 1800]  # 重试延迟：1分钟、5分钟、30分钟
        self._stop_event = threading.Event()
        self._auto_restart = True  # 自动重启标志
        self._restart_timer = None
    
    def start_processing(self):
        """启动邮件队列处理"""
        if self.is_running:
            logger.warning("邮件队列处理器已在运行")
            return
        
        self.is_running = True
        self._stop_event.clear()
        self.processing_thread = threading.Thread(target=self._process_queue_loop, daemon=True)
        self.processing_thread.start()
        logger.info("邮件队列处理器已启动")
        
        # 设置健康检查定时器
        self._start_health_check()
    
    def stop_processing(self):
        """停止邮件队列处理"""
        if not self.is_running:
            return
            
        self.is_running = False
        self._auto_restart = False  # 停止自动重启
        self._stop_event.set()
        
        # 取消重启定时器
        if self._restart_timer:
            self._restart_timer.cancel()
            self._restart_timer = None
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=10)
            if self.processing_thread.is_alive():
                logger.warning("邮件队列处理器强制停止")
        
        logger.info("邮件队列处理器已停止")
    
    def _process_queue_loop(self):
        """邮件队列处理主循环"""
        while self.is_running and not self._stop_event.is_set():
            try:
                self._process_batch()
                # 使用事件等待，支持优雅停止
                if self._stop_event.wait(self.processing_interval):
                    break
            except Exception as e:
                logger.error(f"邮件队列处理错误: {e}")
                logger.error(traceback.format_exc())
                # 出错时等待30秒，但检查停止信号
                if self._stop_event.wait(30):
                    break
        
        # 如果循环退出且启用了自动重启，则安排重启
        if self._auto_restart and not self._stop_event.is_set():
            logger.warning("邮件队列处理器意外停止，将在10秒后自动重启")
            self._schedule_restart(10)
    
    def _process_batch(self):
        """处理一批邮件"""
        db = SessionLocal()
        try:
            # 获取待发送邮件
            pending_emails = self._get_pending_emails(db)
            
            if not pending_emails:
                return
            
            logger.info(f"处理 {len(pending_emails)} 封待发送邮件")
            
            # 处理每封邮件
            for email_queue in pending_emails:
                if self._stop_event.is_set():
                    break
                    
                try:
                    self._process_single_email(db, email_queue)
                except Exception as e:
                    logger.error(f"处理邮件 {email_queue.id} 失败: {e}")
                    logger.error(traceback.format_exc())
                    self._handle_email_failure(db, email_queue, str(e))
            
            # 清理已处理的邮件
            if not self._stop_event.is_set():
                self._cleanup_processed_emails(db)
            
        except Exception as e:
            logger.error(f"批处理邮件失败: {e}")
            logger.error(traceback.format_exc())
        finally:
            db.close()
    
    def _get_pending_emails(self, db: Session) -> List[EmailQueue]:
        """获取待发送邮件"""
        try:
            return db.query(EmailQueue).filter(
                EmailQueue.status == 'pending'
            ).order_by(EmailQueue.created_at).limit(self.batch_size).all()
        except Exception as e:
            logger.error(f"获取待发送邮件失败: {e}")
            return []
    
    def _process_single_email(self, db: Session, email_queue: EmailQueue):
        """处理单封邮件"""
        try:
            email_service = EmailService(db)
            
            # 检查重试次数
            if email_queue.retry_count >= self.max_retries:
                email_queue.status = 'failed'
                email_queue.error_message = f"重试{self.max_retries}次后仍然失败"
                db.commit()
                logger.warning(f"邮件 {email_queue.id} 重试次数超限，标记为失败")
                return
            
            # 尝试发送邮件
            success = email_service.send_email(email_queue)
            if success:
                email_queue.status = 'sent'
                email_queue.sent_at = datetime.now()
                email_queue.retry_count = 0
                db.commit()
                logger.info(f"邮件 {email_queue.id} 发送成功")
            else:
                self._schedule_retry(db, email_queue)
                
        except Exception as e:
            logger.error(f"发送邮件 {email_queue.id} 异常: {e}")
            logger.error(traceback.format_exc())
            self._schedule_retry(db, email_queue, str(e))
    
    def _schedule_retry(self, db: Session, email_queue: EmailQueue, error: str = None):
        """安排重试"""
        try:
            email_queue.retry_count += 1
            email_queue.status = 'pending'
            email_queue.error_message = error or "发送失败，等待重试"
            
            # 设置重试延迟
            if email_queue.retry_count <= len(self.retry_delays):
                delay = self.retry_delays[email_queue.retry_count - 1]
                # 这里可以通过修改created_at来实现延迟重试
                # 或者添加一个next_retry_at字段
            
            db.commit()
            logger.info(f"邮件 {email_queue.id} 安排重试，第 {email_queue.retry_count} 次")
        except Exception as e:
            logger.error(f"安排重试失败: {e}")
            db.rollback()
    
    def _handle_email_failure(self, db: Session, email_queue: EmailQueue, error: str):
        """处理邮件发送失败"""
        try:
            email_queue.status = 'failed'
            email_queue.error_message = error
            db.commit()
            logger.error(f"邮件 {email_queue.id} 发送失败: {error}")
        except Exception as e:
            logger.error(f"处理邮件失败状态失败: {e}")
            db.rollback()
    
    def _cleanup_processed_emails(self, db: Session):
        """清理已处理的邮件"""
        try:
            # 删除30天前的已发送邮件
            cutoff_date = datetime.now() - timedelta(days=30)
            deleted_count = db.query(EmailQueue).filter(
                and_(
                    EmailQueue.created_at < cutoff_date,
                    EmailQueue.status.in_(['sent', 'failed'])
                )
            ).delete()
            
            if deleted_count > 0:
                db.commit()
                logger.info(f"清理了 {deleted_count} 封已处理邮件")
                
        except Exception as e:
            logger.error(f"清理邮件失败: {e}")
            db.rollback()
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        db = SessionLocal()
        try:
            total = db.query(EmailQueue).count()
            pending = db.query(EmailQueue).filter(EmailQueue.status == 'pending').count()
            sent = db.query(EmailQueue).filter(EmailQueue.status == 'sent').count()
            failed = db.query(EmailQueue).filter(EmailQueue.status == 'failed').count()
            
            # 按邮件类型统计
            type_stats = db.query(
                EmailQueue.email_type,
                func.count(EmailQueue.id)
            ).group_by(EmailQueue.email_type).all()
            
            # 按状态统计重试次数
            retry_stats = db.query(
                EmailQueue.retry_count,
                func.count(EmailQueue.id)
            ).group_by(EmailQueue.retry_count).all()
            
            # 计算平均重试次数
            avg_retry_count = 0
            if total > 0:
                total_retries = sum(count * retry_count for retry_count, count in retry_stats)
                avg_retry_count = round(total_retries / total, 2)
            
            return {
                "total": total,
                "pending": pending,
                "sent": sent,
                "failed": failed,
                "type_distribution": dict(type_stats),
                "retry_distribution": dict(retry_stats),
                "avg_retry_count": avg_retry_count,
                "processor_status": "running" if self.is_running else "stopped"
            }
        except Exception as e:
            logger.error(f"获取队列统计失败: {e}")
            return {
                "total": 0,
                "pending": 0,
                "sent": 0,
                "failed": 0,
                "type_distribution": {},
                "retry_distribution": {},
                "avg_retry_count": 0,
                "processor_status": "error"
            }
        finally:
            db.close()
    
    def retry_failed_emails(self, email_ids: Optional[List[int]] = None) -> Dict[str, int]:
        """重试失败的邮件"""
        db = SessionLocal()
        try:
            if email_ids:
                # 重试指定邮件
                failed_emails = db.query(EmailQueue).filter(
                    and_(
                        EmailQueue.id.in_(email_ids),
                        EmailQueue.status == 'failed'
                    )
                ).all()
            else:
                # 重试所有失败邮件
                failed_emails = db.query(EmailQueue).filter(
                    EmailQueue.status == 'failed'
                ).all()
            
            retry_count = 0
            for email in failed_emails:
                email.status = 'pending'
                email.retry_count = 0
                email.error_message = "手动重试"
                retry_count += 1
            
            db.commit()
            logger.info(f"手动重试了 {retry_count} 封失败邮件")
            
            return {
                "retried": retry_count,
                "total_failed": len(failed_emails)
            }
            
        except Exception as e:
            logger.error(f"重试失败邮件时出错: {e}")
            db.rollback()
            return {"retried": 0, "error": str(e)}
        finally:
            db.close()
    
    def pause_processing(self, duration_minutes: int = 0):
        """暂停邮件处理"""
        if duration_minutes > 0:
            logger.info(f"暂停邮件处理 {duration_minutes} 分钟")
            self.is_running = False
            # 设置定时器重新启动
            threading.Timer(duration_minutes * 60, self.start_processing).start()
        else:
            logger.info("暂停邮件处理")
            self.is_running = False
    
    def resume_processing(self):
        """恢复邮件处理"""
        if not self.is_running:
            self.start_processing()
        else:
            logger.info("邮件处理器已在运行")
    
    def is_healthy(self) -> bool:
        """检查队列处理器是否健康"""
        try:
            # 检查线程是否存活
            if not self.processing_thread or not self.processing_thread.is_alive():
                return False
            
            # 检查是否有大量失败邮件
            db = SessionLocal()
            try:
                failed_count = db.query(EmailQueue).filter(EmailQueue.status == 'failed').count()
                total_count = db.query(EmailQueue).count()
                
                if total_count > 0 and (failed_count / total_count) > 0.5:
                    return False
                    
                return True
            finally:
                db.close()
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False
    
    def get_email_queue(self, page: int = 1, size: int = 20, status: str = None) -> List[EmailQueue]:
        """获取邮件队列列表"""
        db = SessionLocal()
        try:
            query = db.query(EmailQueue)
            if status:
                query = query.filter(EmailQueue.status == status)
            
            # 分页
            offset = (page - 1) * size
            emails = query.order_by(EmailQueue.created_at.desc()).offset(offset).limit(size).all()
            return emails
        finally:
            db.close()
    
    def get_email_queue_count(self, status: str = None) -> int:
        """获取邮件队列总数"""
        db = SessionLocal()
        try:
            query = db.query(EmailQueue)
            if status:
                query = query.filter(EmailQueue.status == status)
            return query.count()
        finally:
            db.close()
    
    def get_email_by_id(self, email_id: int) -> Optional[EmailQueue]:
        """根据ID获取邮件"""
        db = SessionLocal()
        try:
            return db.query(EmailQueue).filter(EmailQueue.id == email_id).first()
        finally:
            db.close()
    
    def retry_email(self, email_id: int) -> bool:
        """重试发送邮件"""
        db = SessionLocal()
        try:
            email = db.query(EmailQueue).filter(EmailQueue.id == email_id).first()
            if not email:
                return False
            
            # 重置状态为pending
            email.status = 'pending'
            email.retry_count += 1
            email.error_message = None
            
            db.commit()
            
            # 尝试立即发送
            email_service = EmailService(db)
            success = email_service.send_email(email)
            
            if success:
                email.status = 'sent'
                email.sent_at = datetime.now()
            else:
                email.status = 'failed'
                email.error_message = '重试发送失败'
            
            db.commit()
            return success
            
        except Exception as e:
            db.rollback()
            logger.error(f"重试邮件失败: {e}")
            return False
        finally:
            db.close()
    
    def delete_email_from_queue(self, email_id: int) -> bool:
        """从队列中删除邮件"""
        db = SessionLocal()
        try:
            email = db.query(EmailQueue).filter(EmailQueue.id == email_id).first()
            if not email:
                return False
            
            db.delete(email)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"删除邮件失败: {e}")
            return False
        finally:
            db.close()
    
    def clear_email_queue(self, status: str = None) -> bool:
        """清空邮件队列"""
        db = SessionLocal()
        try:
            query = db.query(EmailQueue)
            if status:
                query = query.filter(EmailQueue.status == status)
            
            deleted_count = query.delete()
            db.commit()
            logger.info(f"清空邮件队列成功，删除了 {deleted_count} 条记录")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"清空邮件队列失败: {e}")
            return False
        finally:
            db.close()

    def _start_health_check(self):
        """启动健康检查"""
        def health_check():
            if self._auto_restart and not self._stop_event.is_set():
                if not self.is_running or not self.processing_thread or not self.processing_thread.is_alive():
                    logger.warning("检测到邮件队列处理器异常，准备重启")
                    self._schedule_restart(5)
                else:
                    # 继续健康检查
                    self._restart_timer = threading.Timer(30, health_check)
                    self._restart_timer.start()
        
        # 启动第一次健康检查
        self._restart_timer = threading.Timer(30, health_check)
        self._restart_timer.start()
    
    def _schedule_restart(self, delay_seconds: int = 10):
        """安排重启"""
        if self._restart_timer:
            self._restart_timer.cancel()
        
        def restart():
            if self._auto_restart and not self._stop_event.is_set():
                logger.info("自动重启邮件队列处理器")
                self.is_running = False
                if self.processing_thread and self.processing_thread.is_alive():
                    self.processing_thread.join(timeout=5)
                self.start_processing()
        
        self._restart_timer = threading.Timer(delay_seconds, restart)
        self._restart_timer.start()
    
    def force_restart(self):
        """强制重启邮件队列处理器"""
        logger.info("强制重启邮件队列处理器")
        self.stop_processing()
        self._auto_restart = True
        self.start_processing()

# 全局邮件队列处理器实例
email_queue_processor = EmailQueueProcessor()

def get_email_queue_processor() -> EmailQueueProcessor:
    """获取邮件队列处理器实例"""
    return email_queue_processor
