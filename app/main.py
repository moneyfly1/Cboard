from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from .core.config import settings
from .api.api_v1.api import api_router
from .core.database import init_database
from .models import (
    User, Subscription, Device, Order, Package, EmailQueue, 
    EmailTemplate, Notification, Node, PaymentTransaction, 
    PaymentConfig, PaymentCallback, SystemConfig, Announcement, 
    ThemeConfig, UserActivity, SubscriptionReset, LoginHistory
)
from .services.email_queue_processor import get_email_queue_processor
from .tasks.notification_tasks import start_notification_scheduler, stop_notification_scheduler
# from .services.node_speed_monitor import get_node_speed_monitor  # 已删除

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="XBoard Modern - 现代化订阅管理系统",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库和启动邮件队列处理器"""
    try:
        init_database()
        print("数据库初始化成功")
        
        # 启动邮件队列处理器
        email_processor = get_email_queue_processor()
        email_processor.start_processing()
        print("邮件队列处理器已启动")
        
        # 启动通知调度器
        start_notification_scheduler()
        print("通知调度器已启动")
        
        # 启动节点测速监控 - 已删除
        # node_monitor = get_node_speed_monitor()
        # node_monitor.start()
        # print("节点测速监控已启动")
        
    except Exception as e:
        print(f"应用启动失败: {e}")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时停止邮件队列处理器"""
    try:
        email_processor = get_email_queue_processor()
        email_processor.stop_processing()
        print("邮件队列处理器已停止")
        
        # 停止通知调度器
        stop_notification_scheduler()
        print("通知调度器已停止")
        
        # 停止节点测速监控 - 已删除
        # node_monitor = get_node_speed_monitor()
        # node_monitor.stop()
        # print("节点测速监控已停止")
    except Exception as e:
        print(f"停止服务失败: {e}")

@app.get("/")
async def root():
    return {"message": "XBoard Modern API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 禁用自动重载，避免订阅更新时服务器重启
        log_level="info"
    ) 