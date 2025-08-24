"""
数据库连接和会话管理
Database Connection and Session Management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings, get_database_url

# 创建数据库引擎
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,  # 连接前检查
    pool_recycle=300,    # 连接回收时间（秒）
    echo=settings.DEBUG  # 在调试模式下打印SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用作 FastAPI 的依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """创建所有数据表"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """删除所有数据表"""
    Base.metadata.drop_all(bind=engine)