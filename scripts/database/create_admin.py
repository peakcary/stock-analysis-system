#!/usr/bin/env python3
"""
创建管理员用户脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.crud.user import UserCRUD
from app.schemas.user import UserCreate
from app.models.user import MembershipType

def create_admin_user():
    """创建管理员用户"""
    db = next(get_db())
    user_crud = UserCRUD(db)
    
    # 检查是否已存在admin用户
    existing_admin = user_crud.get_user_by_username("admin")
    if existing_admin:
        print("❌ 管理员用户已存在!")
        print(f"   用户名: {existing_admin.username}")
        print(f"   邮箱: {existing_admin.email}")
        print(f"   创建时间: {existing_admin.created_at}")
        return
    
    # 创建管理员用户
    admin_data = UserCreate(
        username="admin",
        email="admin@stockanalysis.com",
        password="admin123"  # 建议在生产环境中使用更强的密码
    )
    
    try:
        admin_user = user_crud.create_user(admin_data)
        
        # 升级为高级会员
        user_crud.upgrade_membership(
            user_id=admin_user.id,
            membership_type=MembershipType.PREMIUM,
            queries_to_add=9999,  # 给管理员大量查询次数
            days_to_add=36500  # 100年有效期
        )
        
        print("✅ 管理员用户创建成功!")
        print(f"   用户名: {admin_user.username}")
        print(f"   邮箱: {admin_user.email}")
        print(f"   密码: admin123")
        print("   会员类型: PREMIUM")
        print("   ⚠️  请及时修改默认密码!")
        
    except ValueError as e:
        print(f"❌ 创建管理员失败: {e}")
    except Exception as e:
        print(f"❌ 创建管理员时发生错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 正在创建管理员用户...")
    create_admin_user()