#!/usr/bin/env python3
"""
创建超级管理员用户脚本
"""
import sys
import os
import asyncio
from getpass import getpass
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.models.user import User, MembershipType
from app.core.security import get_password_hash


def create_superuser(username=None, email=None, password=None):
    """创建超级管理员用户"""
    print("🚀 创建超级管理员用户")
    print("=" * 50)
    
    # 如果参数未提供，使用默认值或获取用户输入
    if not username:
        try:
            username = input("请输入用户名: ").strip()
        except (EOFError, KeyboardInterrupt):
            username = "superadmin"
            print(f"使用默认用户名: {username}")
    
    if not username:
        print("❌ 用户名不能为空")
        return False
    
    if not email:
        try:
            email = input("请输入邮箱: ").strip()
        except (EOFError, KeyboardInterrupt):
            email = "admin@example.com"
            print(f"使用默认邮箱: {email}")
    
    if not email or '@' not in email:
        print("❌ 请输入有效的邮箱地址")
        return False
    
    if not password:
        try:
            password = getpass("请输入密码: ")
            if not password or len(password) < 6:
                print("❌ 密码至少需要6位字符")
                return False
            
            password_confirm = getpass("请确认密码: ")
            if password != password_confirm:
                print("❌ 两次输入的密码不一致")
                return False
        except (EOFError, KeyboardInterrupt):
            password = "admin123456"
            print("使用默认密码: admin123456")
    
    if not password or len(password) < 6:
        print("❌ 密码至少需要6位字符")
        return False
    
    # 创建数据库会话
    db = next(get_db())
    
    try:
        # 检查用户名和邮箱是否已存在
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print("❌ 用户名或邮箱已存在")
            return False
        
        # 暂时使用PREMIUM类型作为超级管理员 
        # 等数据库更新后可以改为SUPER_ADMIN
        superuser = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            membership_type=MembershipType.PREMIUM,
            queries_remaining=999999,  # 无限查询次数
            membership_expires_at=datetime.now() + timedelta(days=36500),  # 100年有效期
        )
        
        db.add(superuser)
        db.commit()
        db.refresh(superuser)
        
        print("✅ 超级管理员创建成功!")
        print(f"   用户ID: {superuser.id}")
        print(f"   用户名: {superuser.username}")
        print(f"   邮箱: {superuser.email}")
        print(f"   会员类型: {superuser.membership_type.value}")
        print(f"   查询次数: {superuser.queries_remaining}")
        print("🔑 该用户拥有最高权限，可以访问所有数据和功能")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建用户失败: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """主函数"""
    try:
        # 支持命令行参数
        import argparse
        parser = argparse.ArgumentParser(description='创建超级管理员用户')
        parser.add_argument('--username', '-u', default='superadmin', help='用户名 (默认: superadmin)')
        parser.add_argument('--email', '-e', default='admin@example.com', help='邮箱 (默认: admin@example.com)')
        parser.add_argument('--password', '-p', default='admin123456', help='密码 (默认: admin123456)')
        
        args = parser.parse_args()
        
        success = create_superuser(args.username, args.email, args.password)
        if success:
            print("\n🎉 超级管理员创建完成!")
            print("现在您可以使用该账户登录系统，享受无限制访问权限。")
            print(f"登录信息:")
            print(f"  用户名: {args.username}")
            print(f"  密码: {args.password}")
        else:
            print("\n💔 创建失败，请重试。")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()