#!/usr/bin/env python3
"""
数据库初始化脚本 - 创建所有表
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import engine
from app.core.database import Base
# 导入所有模型，以便 Base.metadata 包含它们
from app.models import *
from app.models.admin_user import AdminUser
from app.models.payment import PaymentPackage

def init_db():
    """创建所有数据库表"""
    print("🔨 开始创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")

if __name__ == "__main__":
    init_db()
