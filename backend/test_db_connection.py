#!/usr/bin/env python3
"""
数据库连接测试脚本
Test Database Connection Script
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_database_connection():
    """测试数据库连接"""

    # 从环境变量读取数据库配置
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        # 手动构建连接字符串
        db_host = os.getenv("DATABASE_HOST", "127.0.0.1")
        db_port = os.getenv("DATABASE_PORT", "3306")
        db_user = os.getenv("DATABASE_USER", "root")
        db_password = os.getenv("DATABASE_PASSWORD", "")
        db_name = os.getenv("DATABASE_NAME", "stock_analysis_dev")

        database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    print("=" * 60)
    print("数据库连接测试 (Database Connection Test)")
    print("=" * 60)

    # 隐藏密码显示
    display_url = database_url.replace(os.getenv("DATABASE_PASSWORD", ""), "****")
    print(f"\n连接字符串 (Connection String):\n{display_url}\n")

    try:
        print("正在连接数据库... (Connecting to database...)")
        engine = create_engine(database_url, echo=False)

        # 测试连接
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            connection.commit()

        print("✅ 数据库连接成功! (Database connection successful!)")

        # 获取数据库信息
        with engine.connect() as connection:
            # 获取数据库版本
            version = connection.execute(text("SELECT VERSION()")).fetchone()
            print(f"\n📊 MySQL 版本 (Version): {version[0]}")

            # 获取数据库列表
            databases = connection.execute(text("SHOW DATABASES")).fetchall()
            print(f"\n📁 可用数据库 (Available Databases):")
            for db in databases:
                print(f"   - {db[0]}")

            # 获取当前数据库中的表
            db_name = os.getenv("DATABASE_NAME", "stock_analysis_dev")
            try:
                tables = connection.execute(text(f"SHOW TABLES FROM {db_name}")).fetchall()
                if tables:
                    print(f"\n📋 数据库 '{db_name}' 中的表 (Tables):")
                    for table in tables:
                        print(f"   - {table[0]}")
                else:
                    print(f"\n⚠️  数据库 '{db_name}' 中没有表 (No tables found)")
            except Exception as e:
                print(f"\n⚠️  无法列出表: {e}")

        return True

    except OperationalError as e:
        print(f"❌ 数据库连接失败! (Connection failed!)")
        print(f"\n错误详情 (Error Details):")
        print(f"{str(e)}\n")

        # 诊断信息
        print("🔍 诊断信息 (Diagnostic Information):")
        print(f"   - 主机 (Host): {os.getenv('DATABASE_HOST')}")
        print(f"   - 端口 (Port): {os.getenv('DATABASE_PORT')}")
        print(f"   - 用户 (User): {os.getenv('DATABASE_USER')}")
        print(f"   - 数据库 (Database): {os.getenv('DATABASE_NAME')}")
        print("\n常见问题:")
        print("   1. 检查网络连接是否正常")
        print("   2. 检查数据库主机地址是否正确")
        print("   3. 检查数据库端口是否正确")
        print("   4. 检查用户名和密码是否正确")
        print("   5. 检查数据库用户是否有访问权限")

        return False

    except Exception as e:
        print(f"❌ 发生错误 (Error): {str(e)}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
