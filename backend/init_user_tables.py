#!/usr/bin/env python3
"""
初始化用户相关数据库表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.user import User, UserQuery, Payment

def init_user_tables():
    """初始化用户相关数据库表"""
    try:
        print("🔧 正在创建用户相关数据库表...")
        
        # 创建所有用户相关表
        User.__table__.create(engine, checkfirst=True)
        UserQuery.__table__.create(engine, checkfirst=True)
        Payment.__table__.create(engine, checkfirst=True)
        
        print("✅ 用户数据库表创建成功!")
        print("   - users (用户表)")
        print("   - user_queries (用户查询记录表)")
        print("   - payments (支付记录表)")
        
        # 显示表结构信息
        print("\n📋 用户表结构:")
        print("   - id: 主键ID")
        print("   - username: 用户名（唯一）")
        print("   - email: 邮箱（唯一）")
        print("   - password_hash: 密码哈希")
        print("   - membership_type: 会员类型 (free/pro/premium)")
        print("   - queries_remaining: 剩余查询次数")
        print("   - membership_expires_at: 会员到期时间")
        print("   - created_at: 创建时间")
        print("   - updated_at: 更新时间")
        
        print("\n🎯 下一步:")
        print("   运行 python create_admin.py 创建管理员账户")
        
    except Exception as e:
        print(f"❌ 创建数据库表时发生错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = init_user_tables()
    if success:
        print("\n🚀 用户系统初始化完成!")
    else:
        print("\n💥 用户系统初始化失败!")
        sys.exit(1)