from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.core.database import init_database
from app.models import (
    User, Subscription, Device, Order, Package, EmailQueue, 
    EmailTemplate, Notification, Node, PaymentTransaction, 
    PaymentConfig, PaymentCallback, SystemConfig, Announcement, 
    ThemeConfig, UserActivity, SubscriptionReset, LoginHistory
)

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
    """应用启动时初始化数据库"""
    try:
        init_database()
    except Exception as e:
        print(f"数据库初始化失败: {e}")

@app.get("/")
async def root():
    return {"message": "XBoard Modern API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
