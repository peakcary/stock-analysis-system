"""
创建管理员用户表的数据库迁移脚本
"""
from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
from app.models.admin_user import AdminUser
from app.crud.admin_user import AdminUserCRUD
from app.core.database import get_db

def create_admin_table():
    """创建管理员用户表"""
    try:
        # 创建数据库引擎
        engine = create_engine(settings.DATABASE_URL)
        
        # 创建所有表（包括AdminUser表）
        Base.metadata.create_all(bind=engine, tables=[AdminUser.__table__])
        
        print("✅ AdminUser表创建成功")
        return True
    except Exception as e:
        print(f"❌ 创建AdminUser表失败: {str(e)}")
        return False

def create_default_admin():
    """创建默认的超级管理员账号"""
    try:
        from sqlalchemy.orm import sessionmaker
        from app.core.config import settings
        
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        admin_crud = AdminUserCRUD(db)
        
        # 检查是否已存在admin用户
        existing_admin = admin_crud.get_by_username("admin")
        if existing_admin:
            print("⚠️  默认管理员账号已存在")
            return True
        
        # 创建默认管理员账号
        admin_user = admin_crud.create(
            username="admin",
            email="admin@example.com", 
            password="admin123",
            full_name="系统管理员",
            is_superuser=True
        )
        
        print(f"✅ 创建默认管理员账号成功:")
        print(f"   用户名: {admin_user.username}")
        print(f"   邮箱: {admin_user.email}")
        print(f"   密码: admin123")
        print(f"   超级用户: {admin_user.is_superuser}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 创建默认管理员账号失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始创建AdminUser表和默认管理员账号...")
    
    # 创建表
    if create_admin_table():
        # 创建默认管理员
        create_default_admin()
        print("\n🎉 管理员系统初始化完成!")
    else:
        print("\n❌ 管理员系统初始化失败!")