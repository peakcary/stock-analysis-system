"""
应用配置管理
Application Configuration Management
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基本配置
    APP_NAME: str = "股票概念分析系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 3007
    
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:Pp123456@127.0.0.1:3306/stock_analysis_dev"
    DATABASE_HOST: str = "127.0.0.1"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = "Pp123456"
    DATABASE_NAME: str = "stock_analysis_dev"
    
    # JWT 配置
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS 配置
    ALLOWED_ORIGINS: list = [
        "http://localhost:8005",
        "http://127.0.0.1:8005",
        "http://localhost:8006",
        "http://127.0.0.1:8006"
    ]
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "uploads"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # 微信支付配置
    WECHAT_APPID: str = ""  # 微信公众平台/开放平台 AppID
    WECHAT_MCH_ID: str = ""  # 微信商户号
    WECHAT_API_KEY: str = ""  # 微信支付API密钥
    WECHAT_CERT_PATH: str = ""  # 商户证书路径（可选，用于退款等操作）
    WECHAT_KEY_PATH: str = ""  # 商户私钥路径（可选）
    
    # 应用基础URL（用于支付回调）
    BASE_URL: str = "http://localhost:3007"
    
    # 支付配置
    PAYMENT_ORDER_TIMEOUT_HOURS: int = 2  # 支付订单超时时间（小时）
    PAYMENT_ENABLED: bool = True  # 是否启用支付功能
    PAYMENT_MOCK_MODE: bool = True  # 是否启用模拟支付（用于本地测试）
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局设置实例
settings = Settings()


# 数据库 URL 构建函数
def get_database_url() -> str:
    """构建数据库连接 URL"""
    return f"mysql+pymysql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"