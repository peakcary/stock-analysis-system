"""
数据库迁移版本 XXX - [描述您的更改]

说明:
  - 版本号: XXX (三位数，如: 002, 003 等)
  - 描述: [简要说明此迁移做了什么]
  - 创建时间: [日期]
  - 升级: 执行 upgrade() 函数
  - 回滚: 执行 downgrade() 函数

例子：
  版本 002: 添加用户表中的 phone_number 字段
  版本 003: 创建支付订单表
  版本 004: 添加 admin_users 表的 last_login 字段

使用方式（通常由 db-migrate.sh 自动调用）:
  python3 migrations/XXX_description.py upgrade
  python3 migrations/XXX_description.py downgrade
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
    """
    try:
        print("🔧 升级数据库到版本 XXX...")

        # 方式 1: 如果只是添加新字段或表，可以用 SQLAlchemy
        # from app.core.database import engine
        # from app.models import *
        # Base.metadata.create_all(bind=engine, checkfirst=True)

        # 方式 2: 如果需要复杂的数据变换，使用原生 SQL
        from sqlalchemy import text
        from app.core.database import engine

        with engine.connect() as conn:
            # 示例：添加新字段
            # conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)"))

            # 示例：创建新表
            # conn.execute(text("""
            #     CREATE TABLE IF NOT EXISTS new_table (
            #         id INT PRIMARY KEY AUTO_INCREMENT,
            #         name VARCHAR(100) NOT NULL,
            #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            #     )
            # """))

            # 示例：迁移数据
            # conn.execute(text("UPDATE users SET status = 'active' WHERE status IS NULL"))

            conn.commit()

        print("   ✅ 升级完成")
        print("\n✅ 版本 XXX 升级完成！")
        return True

    except Exception as e:
        print(f"\n❌ 升级失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def downgrade():
    """
    回滚数据库从此版本
    """
    try:
        print("⚠️  警告：这将删除或修改数据！")
        response = input("确认回滚? (y/n): ")

        if response.lower() != 'y':
            print("已取消")
            return False

        print("🔄 回滚数据库从版本 XXX...")

        from sqlalchemy import text
        from app.core.database import engine

        with engine.connect() as conn:
            # 示例：删除新增的字段
            # conn.execute(text("ALTER TABLE users DROP COLUMN phone_number"))

            # 示例：删除创建的表
            # conn.execute(text("DROP TABLE IF EXISTS new_table"))

            # 示例：还原数据
            # conn.execute(text("UPDATE users SET status = 'inactive' WHERE status = 'active'"))

            conn.commit()

        print("   ✅ 回滚完成")
        print("\n✅ 版本 XXX 回滚完成！")
        return True

    except Exception as e:
        print(f"\n❌ 回滚失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方式:")
        print("  python3 XXX_description.py upgrade   # 升级到此版本")
        print("  python3 XXX_description.py downgrade # 回滚此版本")
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
