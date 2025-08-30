from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
import os
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "XBoard Modern"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./xboard.db"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "xboard"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 邮件配置
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_USER: str = "your-email@qq.com"
    SMTP_PASSWORD: str = "your-smtp-password"
    EMAILS_FROM_EMAIL: str = "your-email@qq.com"
    EMAILS_FROM_NAME: str = "XBoard Modern"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379"
    
    # 支付宝配置
    ALIPAY_APP_ID: str = "your-alipay-app-id"
    ALIPAY_PRIVATE_KEY: str = "your-private-key"
    ALIPAY_PUBLIC_KEY: str = "alipay-public-key"
    ALIPAY_NOTIFY_URL: str = "https://yourdomain.com/api/v1/payment/alipay/notify"
    ALIPAY_RETURN_URL: str = "https://yourdomain.com/api/v1/payment/alipay/return"
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 订阅配置
    SUBSCRIPTION_URL_PREFIX: str = "https://yourdomain.com/sub"
    DEVICE_LIMIT_DEFAULT: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# 确保上传目录存在
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(exist_ok=True) 