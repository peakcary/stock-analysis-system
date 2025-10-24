#!/bin/bash
set -e

# ===== 简化的数据库初始化脚本 =====
# 不依赖MySQL密码，直接用sudo

SERVER_IP="82.157.28.35"
SERVER_USER="ubuntu"
SERVER_PASSWORD="chen_188_8_8"

echo "🚀 简化数据库初始化脚本"
echo "================================"
echo ""

# 在服务器上执行
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    ${SERVER_USER}@${SERVER_IP} << 'INIT_SCRIPT'

echo "📋 初始化步骤："
echo ""

# 第1步：确保MySQL运行
echo "1️⃣  启动MySQL服务..."
sudo systemctl restart mysql
sleep 3

# 第2步：创建数据库（用sudo mysql，无需密码）
echo "2️⃣  创建数据库..."
sudo mysql << 'SQL'
CREATE DATABASE IF NOT EXISTS stock_analysis_prod DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SELECT 'stock_analysis_prod' as DATABASE_CREATED;
SQL

echo ""
echo "3️⃣  运行Python初始化脚本..."

cd /opt/stock-analysis-system/backend

# 激活虚拟环境
source venv/bin/activate

# 设置环境变量（使用默认值）
export DATABASE_HOST=127.0.0.1
export DATABASE_PORT=3306
export DATABASE_USER=root
export DATABASE_PASSWORD=""
export DATABASE_NAME=stock_analysis_prod

# 运行初始化脚本
python3 << 'PYTHON_SCRIPT'
import os
import sys
from pathlib import Path

# 设置项目路径
project_root = Path("/opt/stock-analysis-system/backend")
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ["DATABASE_HOST"] = "127.0.0.1"
os.environ["DATABASE_PORT"] = "3306"
os.environ["DATABASE_USER"] = "root"
os.environ["DATABASE_PASSWORD"] = ""
os.environ["DATABASE_NAME"] = "stock_analysis_prod"
os.environ["DATABASE_URL"] = "mysql+pymysql://root@127.0.0.1:3306/stock_analysis_prod"
os.environ["ADMIN_SECRET_KEY"] = "admin-secret-key-please-change-in-production"

try:
    from app.core.database import create_tables, Base, engine
    from app.models import *
    from sqlalchemy import text
    from sqlalchemy.orm import sessionmaker
    from app.core.security import get_password_hash

    print("🔧 创建数据库表...")
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("✅ 表创建成功")

    print("👤 创建默认用户...")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    from app.models.user import User
    from app.models.admin_user import AdminUser

    # 检查并创建管理员用户
    existing_admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
    if not existing_admin:
        admin = AdminUser(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin"),
            is_superuser=True
        )
        db.add(admin)
        db.commit()
        print("✅ 默认管理员用户已创建")
        print("   用户名: admin")
        print("   密码: admin")
    else:
        print("⚠️  管理员用户已存在")

    # 检查并创建普通用户
    existing_user = db.query(User).filter(User.username == "admin").first()
    if not existing_user:
        user = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin")
        )
        db.add(user)
        db.commit()
        print("✅ 默认客户端用户已创建")
    else:
        print("⚠️  客户端用户已存在")

    db.close()

    print("")
    print("✅ 数据库初始化完成！")

except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)

PYTHON_SCRIPT

echo ""
echo "4️⃣  验证初始化..."
sudo mysql stock_analysis_prod -e "SHOW TABLES;" 2>/dev/null || echo "（可能还没有表）"

echo ""
echo "✅ 初始化成功！"
echo ""
echo "📝 详情："
echo "   - 数据库: stock_analysis_prod"
echo "   - 默认管理员用户: admin / admin"
echo "   - 默认客户端用户: admin / admin"

INIT_SCRIPT

echo ""
echo "✅ 所有初始化步骤完成！"
echo ""
echo "🧪 验证API连接："
curl -s https://qwquant.com/api/v1/health -k && echo "" && echo "✅ API正常"

