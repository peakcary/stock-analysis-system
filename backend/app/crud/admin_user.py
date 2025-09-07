"""
管理员用户CRUD操作
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from passlib.context import CryptContext

from app.models.admin_user import AdminUser


class AdminUserCRUD:
    def __init__(self, db: Session):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_by_id(self, admin_id: int) -> Optional[AdminUser]:
        """根据ID获取管理员"""
        return self.db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    
    def get_by_username(self, username: str) -> Optional[AdminUser]:
        """根据用户名获取管理员"""
        return self.db.query(AdminUser).filter(AdminUser.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[AdminUser]:
        """根据邮箱获取管理员"""
        return self.db.query(AdminUser).filter(AdminUser.email == email).first()
    
    def create(self, username: str, email: str, password: str, 
               full_name: str = None, is_superuser: bool = False) -> AdminUser:
        """创建管理员用户"""
        password_hash = self.get_password_hash(password)
        admin_user = AdminUser(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_superuser=is_superuser
        )
        self.db.add(admin_user)
        self.db.commit()
        self.db.refresh(admin_user)
        return admin_user
    
    def authenticate(self, username: str, password: str) -> Optional[AdminUser]:
        """认证管理员用户"""
        admin_user = self.get_by_username(username)
        if not admin_user:
            return None
        if not self.verify_password(password, admin_user.password_hash):
            return None
        if not admin_user.is_active:
            return None
        
        # 更新最后登录时间
        admin_user.last_login = func.now()
        self.db.commit()
        return admin_user
    
    def update_last_login(self, admin_id: int) -> None:
        """更新最后登录时间"""
        admin_user = self.get_by_id(admin_id)
        if admin_user:
            admin_user.last_login = func.now()
            self.db.commit()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[AdminUser]:
        """获取所有管理员用户"""
        return self.db.query(AdminUser).offset(skip).limit(limit).all()
    
    def deactivate(self, admin_id: int) -> bool:
        """停用管理员用户"""
        admin_user = self.get_by_id(admin_id)
        if admin_user:
            admin_user.is_active = False
            self.db.commit()
            return True
        return False