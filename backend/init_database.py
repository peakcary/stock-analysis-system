#!/usr/bin/env python3
"""
数据库初始化脚本
Database Initialization Script
"""

import os
import sys
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量 - 统一使用MySQL
# 如果没有设置DATABASE_URL环境变量，则使用默认MySQL配置
if not os.environ.get("DATABASE_URL"):
    # 默认MySQL开发环境配置
    database_host = os.environ.get("DATABASE_HOST", "127.0.0.1")
    database_port = os.environ.get("DATABASE_PORT", "3306")
    database_user = os.environ.get("DATABASE_USER", "root")
    database_password = os.environ.get("DATABASE_PASSWORD", "dev_password")
    database_name = os.environ.get("DATABASE_NAME", "stock_analysis_dev")
    os.environ["DATABASE_URL"] = f"mysql+pymysql://{database_user}:{database_password}@{database_host}:{database_port}/{database_name}"

os.environ["ADMIN_SECRET_KEY"] = "admin-secret-key-here-please-change-in-production-32chars"

# 导入必需模块
from app.core.database import create_tables, Base, engine
from app.models import *  # 导入所有模型
from sqlalchemy import text

def init_database():
    """初始化数据库"""
    print("🚀 开始初始化数据库...")

    try:
        # 创建所有表
        print("📊 创建数据库表...")
        try:
            Base.metadata.create_all(bind=engine, checkfirst=True)
        except Exception as create_error:
            print(f"⚠️ 部分表创建遇到问题: {create_error}")
            print("📝 尝试继续创建用户表...")

            # 单独创建用户相关的表
            from app.models.user import User, UserQuery, Payment
            from app.models.admin_user import AdminUser
            from app.models.payment import PaymentOrder, PaymentPackage, PaymentNotification

            for model in [User, UserQuery, Payment, AdminUser, PaymentOrder, PaymentPackage, PaymentNotification]:
                try:
                    model.__table__.create(bind=engine, checkfirst=True)
                    print(f"✅ 创建表: {model.__tablename__}")
                except Exception as table_error:
                    print(f"⚠️ 表 {model.__tablename__} 创建失败或已存在: {table_error}")

        print("✅ 数据库表创建完成")

        # 创建默认管理员用户
        print("👤 创建默认用户...")
        from app.core.security import get_password_hash
        from sqlalchemy.orm import sessionmaker

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 检查是否已有用户
        from app.models.user import User
        from app.models.admin_user import AdminUser

        existing_user = db.query(User).filter(User.username == "admin").first()
        if not existing_user:
            # 创建客户端管理员用户
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=get_password_hash("admin")
            )
            db.add(admin_user)
            print("✅ 创建默认客户端用户: admin/admin")
        else:
            print("ℹ️ 默认客户端用户已存在")

        # 创建后台管理员用户
        existing_admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        if not existing_admin:
            admin_admin = AdminUser(
                username="admin",
                email="admin@admin.com",
                password_hash=get_password_hash("admin"),
                is_active=True,
                is_superuser=True
            )
            db.add(admin_admin)
            print("✅ 创建默认后台管理员用户: admin/admin")
        else:
            print("ℹ️ 默认后台管理员用户已存在")

        # 创建默认支付套餐
        from app.models.payment import PaymentPackage
        existing_packages = db.query(PaymentPackage).first()
        if not existing_packages:
            default_packages = [
                PaymentPackage(
                    package_type="basic",
                    name="基础套餐",
                    price=9.90,
                    queries_count=50,
                    validity_days=30,
                    membership_type="basic",
                    description="30天内可进行50次查询",
                    is_active=True,
                    sort_order=1
                ),
                PaymentPackage(
                    package_type="premium",
                    name="高级套餐",
                    price=29.90,
                    queries_count=200,
                    validity_days=30,
                    membership_type="premium",
                    description="30天内可进行200次查询",
                    is_active=True,
                    sort_order=2
                ),
                PaymentPackage(
                    package_type="pro",
                    name="专业套餐",
                    price=99.90,
                    queries_count=999,
                    validity_days=90,
                    membership_type="pro",
                    description="90天内可进行999次查询",
                    is_active=True,
                    sort_order=3
                ),
                PaymentPackage(
                    package_type="yearly",
                    name="年度套餐",
                    price=299.90,
                    queries_count=9999,
                    validity_days=365,
                    membership_type="pro",
                    description="365天内可进行9999次查询",
                    is_active=True,
                    sort_order=4
                )
            ]
            for package in default_packages:
                db.add(package)
            print("✅ 创建默认支付套餐")
        else:
            print("ℹ️ 默认支付套餐已存在")

        db.commit()
        db.close()

        print("\n🎉 数据库初始化完成！")
        print("📝 默认登录信息:")
        print("   用户名: admin")
        print("   密码: admin")
        print("💰 支付套餐已初始化")

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)