"""
管理员用户模型
用于管理端的用户认证和权限管理
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class AdminRole(enum.Enum):
    """管理员角色枚举"""
    SUPER_ADMIN = "super_admin"     # 超级管理员 - 所有权限
    ADMIN = "admin"                 # 普通管理员 - 基础管理权限
    CUSTOMER_SERVICE = "customer_service"  # 客服 - 只能查看用户信息
    DATA_ANALYST = "data_analyst"   # 数据分析师 - 数据相关权限


class AdminUser(Base):
    """管理员用户表 - 后台管理系统的管理员账户"""
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    full_name = Column(String(100), nullable=True, comment="姓名")
    # role = Column(Enum(AdminRole), default=AdminRole.ADMIN, nullable=True, comment="管理员角色")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<AdminUser(username='{self.username}', email='{self.email}')>"