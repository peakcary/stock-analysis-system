"""
数据库迁移版本 001 - 初始化数据库结构

说明:
  - 版本号: 001
  - 描述: 初始化数据库，创建基础表结构
  - 创建时间: 2025-10-24
  - 升级: 执行 upgrade() 函数
  - 回滚: 执行 downgrade() 函数（危险！仅在紧急情况使用）

使用方式（通常由 db-migrate.sh 自动调用）:
  python3 migrations/001_initial_schema.py upgrade
  python3 migrations/001_initial_schema.py downgrade
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ["DATABASE_HOST"] = "127.0.0.1"
os.environ["DATABASE_PORT"] = "3306"
os.environ["DATABASE_USER"] = "root"
os.environ["DATABASE_PASSWORD"] = ""
os.environ["DATABASE_NAME"] = "stock_analysis_prod"


def upgrade():
    """
    升级数据库到此版本
    创建所有表结构
    """
    try:
        print("🔧 升级数据库到版本 001...")

        from app.core.database import create_tables, Base, engine
        from app.models import *

        # 创建所有表
        print("   - 创建数据库表...")
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("   ✅ 表创建成功")

        # 创建默认用户
        print("   - 创建默认用户...")
        from sqlalchemy.orm import sessionmaker
        from app.models.user import User
        from app.models.admin_user import AdminUser
        from app.core.security import get_password_hash

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 创建默认管理员用户
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
            print("   ✅ 默认管理员用户已创建")
        else:
            print("   ⚠️  管理员用户已存在，跳过创建")

        # 创建默认客户端用户
        existing_user = db.query(User).filter(User.username == "admin").first()
        if not existing_user:
            user = User(
                username="admin",
                email="admin@example.com",
                password_hash=get_password_hash("admin")
            )
            db.add(user)
            db.commit()
            print("   ✅ 默认客户端用户已创建")
        else:
            print("   ⚠️  客户端用户已存在，跳过创建")

        db.close()

        print("\n✅ 版本 001 升级完成！")
        return True

    except Exception as e:
        print(f"\n❌ 升级失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def downgrade():
    """
    回滚数据库从此版本
    删除所有表（危险！）
    """
    try:
        print("⚠️  警告：这将删除所有数据库表！")
        response = input("确认回滚? (y/n): ")

        if response.lower() != 'y':
            print("已取消")
            return False

        print("🔄 回滚数据库从版本 001...")

        from app.core.database import Base, engine
        from app.models import *

        print("   - 删除所有表...")
        Base.metadata.drop_all(bind=engine)
        print("   ✅ 所有表已删除")

        print("\n✅ 版本 001 回滚完成！")
        return True

    except Exception as e:
        print(f"\n❌ 回滚失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方式:")
        print("  python3 001_initial_schema.py upgrade   # 升级到此版本")
        print("  python3 001_initial_schema.py downgrade # 回滚此版本")
        sys.exit(1)

    action = sys.argv[1].lower()

    if action == "upgrade":
        success = upgrade()
        sys.exit(0 if success else 1)
    elif action == "downgrade":
        success = downgrade()
        sys.exit(0 if success else 1)
    else:
        print(f"❌ 不支持的操作: {action}")
        sys.exit(1)
