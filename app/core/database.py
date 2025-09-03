from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings
import logging
import os

logger = logging.getLogger(__name__)

def get_database_url():
    """获取数据库连接URL"""
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    
    # 如果没有设置DATABASE_URL，则根据环境变量构建
    if os.getenv("USE_MYSQL", "false").lower() == "true":
        # MySQL连接
        return f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}?charset=utf8mb4"
    elif os.getenv("USE_POSTGRES", "false").lower() == "true":
        # PostgreSQL连接
        return f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:5432/{settings.POSTGRES_DB}"
    else:
        # 默认SQLite
        return "sqlite:///./xboard.db"

# 创建数据库引擎
database_url = get_database_url()
logger.info(f"使用数据库: {database_url}")

# 根据数据库类型设置不同的连接参数
if "sqlite" in database_url:
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )
elif "mysql" in database_url:
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.DEBUG
    )
elif "postgresql" in database_url:
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.DEBUG
    )
else:
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 依赖注入：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 测试数据库连接
def test_database_connection():
    """测试数据库连接"""
    try:
        with engine.connect() as connection:
            if "sqlite" in database_url:
                result = connection.execute(text("SELECT 1"))
            else:
                result = connection.execute(text("SELECT 1"))
            logger.info("数据库连接测试成功")
            return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False

# 初始化数据库
def init_database():
    """初始化数据库表"""
    try:
        # 导入所有模型以确保表被创建
        from app.models import (
            User, Subscription, Device, Order, Package, EmailQueue, 
            EmailTemplate, Notification, Node, PaymentTransaction, 
            PaymentConfig, PaymentCallback, SystemConfig, Announcement, 
            ThemeConfig, UserActivity, SubscriptionReset, LoginHistory
        )
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表初始化成功")
        
        # 验证关键表是否创建成功
        with engine.connect() as connection:
            if "sqlite" in database_url:
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            elif "mysql" in database_url:
                result = connection.execute(text("SHOW TABLES"))
            elif "postgresql" in database_url:
                result = connection.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
            else:
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            
            tables = [row[0] for row in result]
            logger.info(f"已创建的表: {tables}")
            
            # 检查关键表是否存在
            required_tables = [
                "users", "subscriptions", "devices", "orders", "packages",
                "user_activities", "subscription_resets", "login_history"
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                logger.warning(f"缺少的表: {missing_tables}")
            else:
                logger.info("所有必需的表都已创建")
            
        return True
    except Exception as e:
        logger.error(f"数据库表初始化失败: {e}")
        return False 