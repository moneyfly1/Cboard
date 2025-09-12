from typing import List, Union
from pydantic import AnyHttpUrl, validator, BaseSettings
import os
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "XBoard Modern"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # 数据库配置 - 支持多种数据库
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./xboard.db")
    
    # MySQL配置
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "xboard_user")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "xboard_password_2024")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "xboard_db")
    
    # PostgreSQL配置
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "xboard")
    
    # JWT配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_HOURS", "24")) * 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # 邮件配置
    SMTP_TLS: bool = os.getenv("SMTP_ENCRYPTION", "tls") in ["tls", "ssl"]
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.qq.com")
    SMTP_USER: str = os.getenv("SMTP_USERNAME", "your-email@qq.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "your-smtp-password")
    EMAILS_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "your-email@qq.com")
    EMAILS_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "XBoard Modern")
    
    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL: str = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
    
    # 支付宝配置
    ALIPAY_APP_ID: str = os.getenv("ALIPAY_APP_ID", "your-alipay-app-id")
    ALIPAY_PRIVATE_KEY: str = os.getenv("ALIPAY_PRIVATE_KEY", "your-private-key")
    ALIPAY_PUBLIC_KEY: str = os.getenv("ALIPAY_PUBLIC_KEY", "alipay-public-key")
    ALIPAY_NOTIFY_URL: str = os.getenv("ALIPAY_NOTIFY_URL", "https://yourdomain.com/api/v1/payment/alipay/notify")
    ALIPAY_RETURN_URL: str = os.getenv("ALIPAY_RETURN_URL", "https://yourdomain.com/api/v1/payment/alipay/return")
    
    # 文件上传配置
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    # 订阅配置
    SUBSCRIPTION_URL_PREFIX: str = os.getenv("SUBSCRIPTION_URL_PREFIX", "http://localhost:8000/sub")
    DEVICE_LIMIT_DEFAULT: int = int(os.getenv("DEVICE_LIMIT_DEFAULT", "3"))
    
    # 应用配置
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    BASE_URL: str = os.getenv("BASE_URL", "https://moneyfly.top")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# 确保上传目录存在
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(exist_ok=True) 